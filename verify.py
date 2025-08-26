import json
import os

# Important: This script needs the CompressedIndexReader and vbyte_decode_stream
# functions. You can either copy them into this file or import them.

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

def verify():
    """
    Verifies that the decompressed index is identical to the original
    uncompressed index.
    """
    output_dir = 'output'
    uncompressed_path = os.path.join(output_dir, 'index.json')

    print("--- Starting Verification ---")

    # 1. Load the original uncompressed index
    try:
        with open(uncompressed_path, 'r', encoding='utf-8') as f:
            print("Loading uncompressed index.json...")
            uncompressed_index = json.load(f)
        print("Uncompressed index loaded successfully.")
    except FileNotFoundError:
        print(f"Error: {uncompressed_path} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode {uncompressed_path}.")
        return

    # 2. Initialize the reader for the compressed index
    try:
        print("Initializing compressed index reader...")
        reader = CompressedIndexReader(output_dir)
        print("Compressed index reader initialized.")
    except FileNotFoundError:
        print("Error: Compressed index files (metadata.json, etc.) not found.")
        return

    # 3. Compare the set of all terms
    print("\nComparing term sets...")
    uncompressed_terms = set(uncompressed_index.keys())
    compressed_terms = set(reader.lexicon.keys())

    if uncompressed_terms != compressed_terms:
        print("Verification FAILED: The set of terms is different.")
        print(f"Missing terms: {uncompressed_terms - compressed_terms}")
        print(f"Extra terms: {compressed_terms - uncompressed_terms}")
        return
    print("Term sets are identical.")

    # 4. Compare postings lists for each term
    print(f"\nComparing postings for all {len(uncompressed_terms)} terms...")
    for i, term in enumerate(uncompressed_terms):
        if (i + 1) % 10000 == 0:
            print(f"  ... verified {i + 1} terms ...")

        # Get postings from both versions
        original_postings = uncompressed_index[term]
        decompressed_doc_ids = reader.get_postings(term) # This needs to be modified if you want to check positions

        # Compare doc ID sets
        if set(original_postings.keys()) != decompressed_doc_ids:
            print(f"\nVerification FAILED for term '{term}': Doc ID sets do not match.")
            print(f"  Original: {set(original_postings.keys())}")
            print(f"  Decompressed: {decompressed_doc_ids}")
            return
            
        # NOTE: Your current `get_postings` only returns docIDs.
        # To verify positions, you would need to modify `get_postings` to return
        # the full dictionary: {doc_id: [positions]} and then compare them.

    print(f"Completed verification for all {len(uncompressed_terms)} terms.")
    print("\n✅ Verification successful! Your compression is lossless for document IDs.")
    
    # Clean up
    reader.close()


if __name__ == '__main__':
    verify()