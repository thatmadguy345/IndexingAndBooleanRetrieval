#!/bin/bash

# Master build script to run the entire pipeline from tokenization to retrieval.
# NOTE: This is for convenience. The assignment requires the individual scripts
# (tokenize_corpus.sh, build_index.sh, retrieval.sh) to be runnable on their own.

echo "--- Starting Full Pipeline ---"

# --- Configuration ---
# Set the paths to your data and output directories here.
CORPUS_DIR="corpus"
STOPWORDS_FILE="stopwords.txt"
QUERIES_FILE="queries.json"
OUTPUT_DIR="output"

# --- Step 1: Create Output Directory ---
echo "[STEP 1/4] Creating output directory..."
mkdir -p "$OUTPUT_DIR"
echo "Done."

# --- Step 2: Tokenization ---
echo "[STEP 2/4] Running Tokenization..."
./tokenize_corpus.sh "$CORPUS_DIR" "$STOPWORDS_FILE" "$OUTPUT_DIR"
if [ $? -ne 0 ]; then
    echo "Tokenization failed. Aborting."
    exit 1
fi
echo "Tokenization complete."

# --- Step 3: Indexing ---
# The vocabulary path is derived from the output directory.
VOCAB_PATH="$OUTPUT_DIR/vocab.txt"
echo "[STEP 3/4] Running Indexing and Compression..."
./build_index.sh "$CORPUS_DIR" "$VOCAB_PATH" "$OUTPUT_DIR" "$OUTPUT_DIR"
if [ $? -ne 0 ]; then
    echo "Indexing failed. Aborting."
    exit 1
fi
echo "Indexing complete."

# --- Step 4: Retrieval ---
echo "[STEP 4/4] Running Retrieval..."
./retrieval.sh "$OUTPUT_DIR" "$QUERIES_FILE" "$OUTPUT_DIR"
if [ $? -ne 0 ]; then
    echo "Retrieval failed. Aborting."
    exit 1
fi
echo "Retrieval complete."

echo "--- Full Pipeline Finished Successfully ---"