#!/bin/bash
# tokenize_corpus.sh
# Executes the vocabulary building script.

# Arguments:
# $1: <CORPUS_DIR>
# $2: <PATH_OF_STOPWORDS_FILE>
# $3: <VOCAB_DIR>

python3 tokenize_corpus.py "$1" "$2" "$3"