import json
import os

# --- VByte Decoder (no changes here) ---
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
        
        self.index_file = open(index_path, 'rb')

    def get_full_postings(self, term):
        """Retrieves and decodes the full postings list (doc IDs and positions)."""
        if term not in self.lexicon:
            return {}
            
        entry = self.lexicon[term]
        doc_count = entry['doc_count']
        pos_counts = entry['pos_counts']
        
        self.index_file.seek(entry['offset'])
        compressed_data = self.index_file.read(entry['size'])
        
        decoded_numbers = vbyte_decode_stream(compressed_data)
        
        # Reconstruct doc IDs
        doc_id_deltas = decoded_numbers[:doc_count]
        last_doc_id = 0
        int_doc_ids = []
        for delta in doc_id_deltas:
            current_doc_id = last_doc_id + delta
            int_doc_ids.append(current_doc_id)
            last_doc_id = current_doc_id
            
        # Reconstruct positions for each doc
        full_postings = {}
        position_deltas = decoded_numbers[doc_count:]
        pos_stream = iter(position_deltas)
        
        for i, int_doc_id in enumerate(int_doc_ids):
            string_doc_id = self.doc_id_map[int_doc_id]
            num_positions = pos_counts[i]
            
            last_pos = 0
            positions = []
            for _ in range(num_positions):
                delta = next(pos_stream)
                current_pos = last_pos + delta
                positions.append(current_pos)
                last_pos = current_pos
            
            full_postings[string_doc_id] = positions
            
        return full_postings

    def close(self):
        self.index_file.close()

def verify():
    """Verifies the entire decompressed index against the original."""
    output_dir = 'output'
    uncompressed_path = os.path.join(output_dir, 'index.json')

    print("--- Starting Full Verification (including positions) ---")

    try:
        with open(uncompressed_path, 'r', encoding='utf-8') as f:
            print("Loading uncompressed index.json...")
            uncompressed_index = json.load(f)
        print("Uncompressed index loaded successfully.")
    except Exception as e:
        print(f"Error loading uncompressed index: {e}")
        return

    reader = None
    try:
        print("Initializing compressed index reader...")
        reader = CompressedIndexReader(output_dir)
        print("Compressed index reader initialized.")
    except Exception as e:
        print(f"Error initializing reader: {e}")
        return

    print("\nComparing term sets...")
    if set(uncompressed_index.keys()) != set(reader.lexicon.keys()):
        print("Verification FAILED: The set of terms is different.")
        return
    print("Term sets are identical.")

    print(f"\nComparing full postings for all {len(uncompressed_index)} terms...")
    for i, term in enumerate(uncompressed_index.keys()):
        if (i + 1) % 10000 == 0:
            print(f"  ... verified {i + 1} terms ...")

        original_postings = uncompressed_index[term]
        decompressed_postings = reader.get_full_postings(term)

        if original_postings != decompressed_postings:
            print(f"\nVerification FAILED for term '{term}': Postings do not match.")
            print(f"  Original: {original_postings}")
            print(f"  Decompressed: {decompressed_postings}")
            return

    print(f"Completed verification for all {len(uncompressed_index)} terms.")
    print("\n✅ Verification successful! Your compression is perfectly lossless.")
    
    if reader:
        reader.close()


if __name__ == '__main__':
    verify()