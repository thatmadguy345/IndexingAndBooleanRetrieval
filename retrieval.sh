#!/bin/bash
# retrieval.sh
# Executes the boolean retrieval script.

# Arguments:
# $1: <COMPRESSED_DIR>
# $2: <QUERY_FILE_PATH>
# $3: <OUTPUT_DIR>

python3 retrieval.py "$1" "$2" "$3"