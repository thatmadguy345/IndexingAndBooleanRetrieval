import sys
import os
import json
import re
from collections import defaultdict
import time

# --- Tokenizer (reused from Task 1) ---
def tokenize(text: str, stopwords: set) -> list:
    text = text.lower()
    text = re.sub(r'\d', '', text)
    raw_tokens = text.split()
    return [token for token in raw_tokens if token not in stopwords]

# --- VByte Encoder/Decoder ---
def vbyte_encode(n: int) -> bytearray:
    """Encodes an integer into a V-Byte byte array."""
    if n < 0:
        raise ValueError(f"Cannot encode negative number: {n}")
    if n == 0:
        return bytearray([128])
    
    bytes_list = []
    while n > 0:
        byte = n % 128
        n //= 128
        bytes_list.append(byte) # Append is much faster
    
    bytes_list.reverse() # Reverse the list once at the end
    
    bytes_list[-1] |= 0x80 # Set MSB of last byte to 1
    return bytearray(bytes_list)

# --- Inverted Index Logic ---
def build_index(corpus_dir: str, vocab_path: str):
    """Builds a positional inverted index."""
    try:
        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab = set(line.strip() for line in f)
    except FileNotFoundError:
        print(f"Error: Vocabulary file not found at {vocab_path}")
        return None, None

    # This is a bit inefficient for very large corpora but simple.
    stopwords = set() # Assume vocab is already stop-filtered

    inverted_index = defaultdict(lambda: defaultdict(list))
    all_doc_ids = set()

    for filename in sorted(os.listdir(corpus_dir)):
        if filename.endswith(".json"):
            filepath = os.path.join(corpus_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip(): # Ensure the line is not empty
                        # Use json.loads(line) to parse the string from the current line
                        doc = json.loads(line) 
                        
                        doc_id = doc.get('doc_id')
                        if not doc_id: continue
                        all_doc_ids.add(doc_id)
                        
                        doc_content = []
                        for key, value in doc.items():
                            if key != 'doc_id':
                                doc_content.append(str(value))
                        
                        full_text = ' '.join(doc_content)
                        tokens = tokenize(full_text, stopwords)
                        
                        for pos, token in enumerate(tokens):
                            if token in vocab:
                                inverted_index[token][doc_id].append(pos)
    
    return inverted_index, sorted(list(all_doc_ids))

def save_index(inverted_index, index_dir: str) -> None:
    """Saves the uncompressed index to a JSON file."""
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)
        
    # Sort terms and doc_ids lexicographically
    sorted_index = {}
    for term in sorted(inverted_index.keys()):
        sorted_postings = {}
        for doc_id in sorted(inverted_index[term].keys()):
            positions = inverted_index[term][doc_id]
            positions.sort()
            sorted_postings[doc_id] = positions
        sorted_index[term] = sorted_postings
        
        
    index_path = os.path.join(index_dir, 'index.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_index, f, indent=4)
    print(f"Uncompressed index saved to {index_path}")

# --- Index Compression Logic ---
def compress_index(inverted_index, all_doc_ids, compressed_dir: str) -> None:
    """Compresses the index using Delta and V-Byte encoding."""
    if not os.path.exists(compressed_dir):
        os.makedirs(compressed_dir)

    # 1. DocID mapping
    doc_id_map = {doc_id: i for i, doc_id in enumerate(all_doc_ids)}
    int_to_doc_id_map = {i: doc_id for doc_id, i in doc_id_map.items()}

    lexicon = {}
    compressed_index_path = os.path.join(compressed_dir, 'compressed_index.bin')

    with open(compressed_index_path, 'wb') as f:
        current_offset = 0
        for term in sorted(inverted_index.keys()):
            postings = inverted_index[term]
            
            int_doc_ids = sorted([doc_id_map[doc_id] for doc_id in postings.keys()])

            # Delta encode doc IDs
            last_doc_id = 0
            encoded_postings = bytearray()
            for doc_id in int_doc_ids:
                delta = doc_id - last_doc_id
                encoded_postings.extend(vbyte_encode(delta))
                last_doc_id = doc_id

            # Also encode positions for each doc
            for int_doc_id in int_doc_ids:
                string_doc_id = int_to_doc_id_map[int_doc_id]
                positions = postings[string_doc_id]
                
                # --- ADD THIS LINE TO FIX THE BUG ---
                positions.sort() # Ensure the positions list is always sorted
                # ------------------------------------
                
                # Delta encode positions
                last_pos = 0
                for pos in positions:
                    delta = pos - last_pos
                    encoded_postings.extend(vbyte_encode(delta))
                    last_pos = pos

            f.write(encoded_postings)
            
            term_length = len(encoded_postings)
            position_counts = [len(postings[int_to_doc_id_map[doc_id]]) for doc_id in int_doc_ids]
            lexicon[term] = {
                'offset': current_offset, 
                'size': term_length,
                'doc_count': len(postings),
                'pos_counts': position_counts # Add the list of position counts
            }
            current_offset += term_length
            
    # Save metadata
    metadata = {
        'lexicon': lexicon,
        'doc_id_map': int_to_doc_id_map,
        'total_docs': len(all_doc_ids)
    }
    metadata_path = os.path.join(compressed_dir, 'metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f)
        
    print(f"Compressed index and metadata saved in {compressed_dir}")


if __name__ == '__main__':

    start_time = time.monotonic()

    if len(sys.argv) != 5:
        print("Usage: python build_index.py <CORPUS_DIR> <VOCAB_PATH> <INDEX_DIR> <COMPRESSED_DIR>")
    else:
        corpus_dir = sys.argv[1]
        vocab_path = sys.argv[2]
        index_dir = sys.argv[3]
        compressed_dir = sys.argv[4]
        
        print("Building index...")
        index, all_docs = build_index(corpus_dir, vocab_path)
        if index and all_docs:
            print("Saving uncompressed index...")
            save_index(index, index_dir)
            print("Compressing index...")
            compress_index(index, all_docs, compressed_dir)
            print("Done.")

    end_time = time.monotonic()
    elapsed_time = end_time - start_time
    print(f"\nProcess took: {elapsed_time:.2f} seconds.")