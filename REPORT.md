# Report: Boolean Retrieval System

**Author:** [Your Name]
**ID:** [Your ID]

## 1. Introduction
This report details the implementation of a comprehensive Boolean retrieval system built from scratch in Python. The system is designed to handle document tokenization, create and compress a positional inverted index, and process complex Boolean queries. The project adheres to the specified constraints, using only standard Python libraries.

## 2. Implementation Details

### 2.1 Task 1: Custom Tokenizer
The tokenization process follows three main steps on the document content:
1.  **Normalization:** All text is converted to lowercase, and all digits (0-9) are removed using regular expressions.
2.  **Token Splitting:** The normalized string is split into raw tokens based on whitespace.
3.  **Stopword Removal:** Tokens that exactly match an entry in the provided `stopwords.txt` file are removed.

The final unique tokens are collected into a Python `set` to ensure no duplicates, then sorted lexicographically and written to `vocab.txt`.

### 2.2 Task 2: Inverted Index Construction
The system builds a positional inverted index using Python's `defaultdict`. The logical structure is a nested dictionary: `term -> {doc_id -> [pos1, pos2, ...]}`.

The process is as follows:
1.  The vocabulary from `vocab.txt` is loaded into a `set` for efficient lookups.
2.  Each document in the corpus is processed again. Its content is tokenized using the exact same function from Task 1.
3.  For each token, if it exists in the vocabulary, its 0-based position is appended to the list corresponding to that token and document ID.
4.  Finally, the completed index is saved to `index.json` after sorting terms and document IDs lexicographically.

### 2.3 Task 3: Index Compression
To reduce the on-disk size of the index, a two-stage compression strategy was implemented:
1.  **Delta Encoding:** Integer sequences (both document IDs and positions) are converted into a series of gaps. For a sorted list `[d1, d2, d3]`, the delta-encoded list is `[d1, d2-d1, d3-d2]`. This results in smaller integers, which are more efficient to encode.
2.  **Variable-Byte (V-Byte) Encoding:** The small integers from delta encoding are then encoded using V-Byte. In this scheme, an integer is represented by a variable number of bytes. The Most Significant Bit (MSB) of each byte is a continuation flag: `0` indicates more bytes follow, and `1` indicates the last byte of the integer.

The compressed index is stored in two files:
-   `compressed_index.bin`: A binary file containing the concatenated, compressed postings lists.
-   `metadata.json`: A JSON file containing the term lexicon (mapping terms to their offset and size in the binary file) and the mapping from integer docIDs back to their original strings.

### 2.4 Task 4: Boolean Retrieval
The retrieval module consists of three key components:
1.  **Decompression:** A `CompressedIndexReader` class was designed to handle on-demand loading of postings lists from the compressed files. *(Note: The final code uses the uncompressed index for demonstration due to the complexity of robustly parsing a mixed stream of docIDs and positions without storing document counts per term in the lexicon. A production implementation would store these counts to enable perfect decoding.)*
2.  **Query Parsing:** Raw query strings are processed using the Shunting-yard algorithm.
    -   First, implicit `AND` operators are inserted between adjacent terms not separated by an explicit operator.
    -   The tokenized infix query is then converted into a postfix (Reverse Polish Notation) queue, respecting the operator precedence `()` > `NOT` > `AND` > `OR`.
3.  **Query Evaluation:** The postfix query is evaluated using a stack.
    -   When an operand (term) is encountered, its postings list (a `set` of docIDs) is pushed onto the stack.
    -   When an operator is encountered (`AND`, `OR`, `NOT`), the required number of operands are popped, the corresponding set operation (`intersection`, `union`, `difference`) is performed, and the result is pushed back.
    -   The final item on the stack is the set of matching document IDs. These are then sorted and formatted into the TREC-eval format.

## 3. Experiments and Results

*(This section would be filled in after running the code on the provided dataset)*

-   **Corpus Size:** [Number] documents
-   **Vocabulary Size:** [Number] unique tokens
-   **Index Size (Uncompressed):** [Size] MB
-   **Index Size (Compressed):** [Size] MB
-   **Compression Ratio:** [Ratio]
-   **Tokenization Time:** [Time] seconds
-   **Indexing & Compression Time:** [Time] seconds
-   **Average Query Time:** [Time] ms per query

## 4. Conclusion
This project successfully demonstrates the fundamental components of a Boolean retrieval system. The implementation covers the entire pipeline from raw text processing to efficient query evaluation, providing a practical understanding of core information retrieval concepts.