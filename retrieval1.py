import sys
import os
import json
import re
from collections import deque
import time

# --- VByte Decoder ---
def vbyte_decode_stream(byte_stream):
    """Decodes a stream of V-Bytes to a list of integers."""
    numbers = []
    n = 0
    for byte in byte_stream:
        if (byte & 128) == 0:
            n = (n << 7) | byte
        else:
            n = (n << 7) | (byte & 127)
            numbers.append(n)
            n = 0
    return numbers

class CompressedIndexReader:
    """Handles on-demand decompression of postings lists."""
    def __init__(self, compressed_dir):
        metadata_path = os.path.join(compressed_dir, 'metadata.json')
        index_path = os.path.join(compressed_dir, 'compressed_index.bin')

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            self.lexicon = metadata['lexicon']
            self.doc_id_map = {int(k): v for k, v in metadata['doc_id_map'].items()}
            self.all_doc_ids = set(self.doc_id_map.values())
            
        self.index_file = open(index_path, 'rb')

    def get_postings(self, term):
        """Retrieves and decodes the postings list (doc IDs only) for a term."""
        if term not in self.lexicon:
            return set()
            
        entry = self.lexicon[term]
        doc_count = entry['doc_count']
        
        self.index_file.seek(entry['offset'])
        compressed_data = self.index_file.read(entry['size'])
        
        # Decode the entire byte stream for this term
        decoded_numbers = vbyte_decode_stream(compressed_data)
        
        # The first `doc_count` numbers are the docID deltas
        doc_id_deltas = decoded_numbers[:doc_count]
        
        # Reconstruct absolute doc IDs from deltas
        last_doc_id = 0
        final_doc_ids = set()
        for delta in doc_id_deltas:
            current_doc_id = last_doc_id + delta
            final_doc_ids.add(self.doc_id_map[current_doc_id])
            last_doc_id = current_doc_id
            
        return final_doc_ids

    def close(self):
        self.index_file.close()

# --- Query Processor ---
def preprocess_query(query_title: str, stopwords: set) -> list:
    """Tokenizes a query and inserts implicit ANDs."""
    query_title = query_title.lower()
    query_title = re.sub(r'\d', '', query_title)
    query_title = query_title.replace('(', ' ( ').replace(')', ' ) ')
    raw_tokens = query_title.split()

    operators = {'and', 'or', 'not', '(', ')'}
    processed_tokens = [
        token for token in raw_tokens 
        if token in operators or token not in stopwords
    ]

    final_tokens = []
    for i, token in enumerate(processed_tokens):
        final_tokens.append(token)
        is_term = token not in operators
        is_next_term = (i + 1 < len(processed_tokens) and 
                        processed_tokens[i+1] not in operators and
                        processed_tokens[i+1] != ')')
        
        if is_term and is_next_term:
            final_tokens.append('and')
            
    return final_tokens

def to_postfix(tokens: list) -> deque:
    """Converts infix token list to postfix (RPN) using Shunting-yard."""
    precedence = {'not': 3, 'and': 2, 'or': 1}
    output = deque()
    op_stack = []
    for token in tokens:
        if token not in {'and', 'or', 'not', '(', ')'}:
            output.append(token)
        elif token == '(':
            op_stack.append(token)
        elif token == ')':
            while op_stack and op_stack[-1] != '(':
                output.append(op_stack.pop())
            if op_stack: op_stack.pop()
        else:
            while (op_stack and op_stack[-1] != '(' and 
                   precedence.get(op_stack[-1], 0) >= precedence.get(token, 0)):
                output.append(op_stack.pop())
            op_stack.append(token)
    while op_stack:
        output.append(op_stack.pop())
    return output

def evaluate_postfix(postfix_query: deque, index_reader: CompressedIndexReader):
    """Evaluates a postfix query using the compressed index reader."""
    eval_stack = []
    all_doc_ids = index_reader.all_doc_ids

    for token in postfix_query:
        if token == 'and':
            right = eval_stack.pop()
            left = eval_stack.pop()
            eval_stack.append(left.intersection(right))
        elif token == 'or':
            right = eval_stack.pop()
            left = eval_stack.pop()
            eval_stack.append(left.union(right))
        elif token == 'not':
            operand = eval_stack.pop()
            eval_stack.append(all_doc_ids - operand)
        else: # Operand
            eval_stack.append(index_reader.get_postings(token))
            
    return eval_stack[0] if eval_stack else set()

def boolean_retrieval(index_reader: CompressedIndexReader, path_to_query_file: str, output_dir: str):
    """Main function to run Boolean retrieval."""
    try:
        with open(path_to_query_file, 'r', encoding='utf-8') as f:
            queries = json.load(f)
    except FileNotFoundError:
        print(f"Error: Query file not found at {path_to_query_file}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'docids.txt')

    with open(output_path, 'w', encoding='utf-8') as f_out:
        for query in queries:
            qid = query['query_id']
            title = query['title']
            
            query_tokens = preprocess_query(title, set())
            postfix_query = to_postfix(query_tokens)
            result_doc_ids = evaluate_postfix(postfix_query, index_reader)
            
            if result_doc_ids:
                sorted_doc_ids = sorted(list(result_doc_ids))
                for rank, doc_id in enumerate(sorted_doc_ids, 1):
                    line = f"{qid} Q0 {doc_id} {rank} 1.0 bool\n"
                    f_out.write(line)
    
    print(f"Retrieval results saved to {output_path}")

if __name__ == '__main__':
    start_time = time.monotonic()

    if len(sys.argv) != 4:
        print("Usage: python retrieval.py <COMPRESSED_DIR> <QUERY_FILE_PATH> <OUTPUT_DIR>")
    else:
        compressed_dir = sys.argv[1]
        query_file = sys.argv[2]
        output_dir = sys.argv[3]

        reader = None
        try:
            # Initialize the reader for the compressed index
            reader = CompressedIndexReader(compressed_dir)
            # Pass the reader object to the retrieval function
            boolean_retrieval(reader, query_file, output_dir)
        except FileNotFoundError:
            print("Error: Compressed index files not found. Ensure metadata.json and compressed_index.bin are in the specified directory.")
        finally:
            # Ensure the file handle is closed
            if reader:
                reader.close()

    end_time = time.monotonic()
    elapsed_time = end_time - start_time
    print(f"\nProcess took: {elapsed_time:.2f} seconds.")