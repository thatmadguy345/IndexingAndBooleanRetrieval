import sys
import os
import json
import re
import time

def tokenize(text: str, stopwords: set) -> list:
    """Applies the tokenization process to a string."""
    # 1. Preprocessing: Lowercase, Remove digits
    text = text.lower()
    text = re.sub(r'\d', '', text)
    
    # 2. Split on whitespace
    raw_tokens = text.split()
    
    # 3. Remove stopwords
    return [token for token in raw_tokens if token not in stopwords]

def build_vocab(corpus_dir: str, stopwords_file: str, vocab_dir: str) -> None:
    """
    Builds a vocabulary from the corpus documents.
    """
    # Load stopwords
    try:
        with open(stopwords_file, 'r', encoding='utf-8') as f:
            stopwords = set(line.strip() for line in f)
    except FileNotFoundError:
        print(f"Error: Stopwords file not found at {stopwords_file}")
        return

    vocabulary = set()
    
    # Process each document in the corpus directory
    for filename in os.listdir(corpus_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(corpus_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip(): # Ensure the line is not empty
                        doc = json.loads(line) # Use json.loads() for strings
                        doc_content = []
                        # Concatenate all fields except 'doc_id'
                        for key, value in doc.items():
                            if key != 'doc_id':
                                doc_content.append(str(value))
                        
                        full_text = ' '.join(doc_content)
                        tokens = tokenize(full_text, stopwords)
                        vocabulary.update(tokens)

    # Sort the vocabulary lexicographically
    sorted_vocab = sorted(list(vocabulary))
    
    # Save the vocabulary to vocab.txt
    if not os.path.exists(vocab_dir):
        os.makedirs(vocab_dir)
    
    vocab_path = os.path.join(vocab_dir, 'vocab.txt')
    with open(vocab_path, 'w', encoding='utf-8') as f:
        for token in sorted_vocab:
            f.write(token + '\n')
            
    print(f"Vocabulary created with {len(sorted_vocab)} unique tokens.")
    print(f"Saved to {vocab_path}")


if __name__ == '__main__':

    start_time = time.monotonic()

    if len(sys.argv) != 4:
        print("Usage: python tokenize_corpus.py <CORPUS_DIR> <STOPWORDS_FILE> <VOCAB_DIR>")
    else:
        corpus_dir = sys.argv[1]
        stopwords_file = sys.argv[2]
        vocab_dir = sys.argv[3]
        build_vocab(corpus_dir, stopwords_file, vocab_dir)

    end_time = time.monotonic()
    elapsed_time = end_time - start_time
    print(f"\nTokenization process took: {elapsed_time:.2f} seconds.")