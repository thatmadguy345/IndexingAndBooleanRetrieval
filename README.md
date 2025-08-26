# Boolean Retrieval System Assignment

## Description
This project is a complete implementation of a Boolean retrieval system as per the assignment specifications. It includes components for tokenization, inverted index creation, index compression, and query processing.

## Requirements
- Python 3.x
- No external libraries are needed beyond the Python Standard Library.

## How to Run
The project is divided into three main stages, each executed by a shell script.

### 1. Set Permissions
First, make all the shell scripts executable:
chmod +x build.sh tokenize_corpus.sh build_index.sh retrieval.sh

### 2. Build (Optional for Python)
The build.sh script is included for compliance but is not necessary for this Python implementation.
./build.sh

### 3. Generate Vocabulary (Task 1)
This script processes the document corpus to create a sorted vocabulary file.
./tokenize_corpus.sh <CORPUS_DIR> <STOPWORDS_FILE> <VOCAB_DIR>

Example:
./tokenize_corpus.sh ./corpus ./stopwords.txt ./output

This will create `output/vocab.txt`.

### 4. Build and Compress Index (Task 2 & 3)
This script builds the inverted index from the corpus and vocabulary, saves it as `index.json`, and also creates a compressed version.
./build_index.sh <CORPUS_DIR> <VOCAB_PATH> <INDEX_DIR> <COMPRESSED_DIR>

Example:
./build_index.sh ./corpus ./output/vocab.txt ./output ./output

This will create `output/index.json` and compressed files inside the `./output` directory.

### 5. Perform Boolean Retrieval (Task 4)
This script uses the compressed index to run Boolean queries and generate a results file in TREC format.
./retrieval.sh <COMPRESSED_DIR> <QUERY_FILE_PATH> <OUTPUT_DIR>

Example:
./retrieval.sh ./output ./test_queries.json ./output

This will create `output/docids.txt`.