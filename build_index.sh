#!/bin/bash
# build_index.sh
# Executes the index building and compression script.

# Arguments:
# $1: <CORPUS_DIR>
# $2: <VOCAB_PATH>
# $3: <INDEX_DIR> (for uncompressed index.json)
# $4: <COMPRESSED_DIR>

python3 build_index.py "$1" "$2" "$3" "$4"