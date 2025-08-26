import sys
import os

def load_qrels(qrels_path):
    """
    Loads the qrels file into a dictionary.
    Assumes TREC format: qid 0 docid relevance
    We only consider documents with relevance > 0.
    """
    qrels = {}
    try:
        with open(qrels_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 4:
                    qid, _, docid, relevance = parts
                    if int(relevance) > 0:
                        if qid not in qrels:
                            qrels[qid] = set()
                        qrels[qid].add(docid)
    except FileNotFoundError:
        print(f"Error: Qrels file not found at {qrels_path}")
        sys.exit(1)
    return qrels

def load_results(results_path):
    """
    Loads the system's results file (docids.txt) into a dictionary.
    Assumes TREC format: qid Q0 docid rank score tag
    """
    results = {}
    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 6:
                    qid, _, docid, _, _, _ = parts
                    if qid not in results:
                        results[qid] = []
                    results[qid].append(docid)
    except FileNotFoundError:
        print(f"Error: Results file not found at {results_path}")
        sys.exit(1)
    return results

def calculate_average_precision(retrieved_docs, relevant_docs):
    """Calculates the Average Precision (AP) for a single query."""
    if not retrieved_docs or not relevant_docs:
        return 0.0

    precision_scores = []
    num_retrieved_relevant = 0
    for i, doc_id in enumerate(retrieved_docs):
        if doc_id in relevant_docs:
            num_retrieved_relevant += 1
            precision_at_k = num_retrieved_relevant / (i + 1)
            precision_scores.append(precision_at_k)

    if not precision_scores:
        return 0.0

    return sum(precision_scores) / len(relevant_docs)

def main():
    """Main function to run the evaluation."""
    output_dir = 'output'
    qrels_file = 'qrels-rnd1.txt' # Assuming this is in your main directory
    results_file = os.path.join(output_dir, 'docids.txt')

    print("--- Loading Evaluation Files ---")
    relevant_docs_map = load_qrels(qrels_file)
    retrieved_docs_map = load_results(results_file)
    print(f"Loaded {len(relevant_docs_map)} queries from Qrels file.")
    print(f"Loaded results for {len(retrieved_docs_map)} queries from your system.")
    
    total_precision = 0
    total_recall = 0
    total_average_precision = 0
    num_queries = len(relevant_docs_map)

    print("\n--- Evaluating Queries ---")
    for qid, relevant_docs in relevant_docs_map.items():
        retrieved_docs = retrieved_docs_map.get(qid, [])
        
        # Find the set of documents that are both retrieved and relevant
        retrieved_relevant_set = set(retrieved_docs) & relevant_docs
        
        num_retrieved = len(retrieved_docs)
        num_relevant = len(relevant_docs)
        num_retrieved_relevant = len(retrieved_relevant_set)

        # Calculate Precision and Recall for this query
        precision = num_retrieved_relevant / num_retrieved if num_retrieved > 0 else 0
        recall = num_retrieved_relevant / num_relevant if num_relevant > 0 else 0
        
        total_precision += precision
        total_recall += recall
        
        # Calculate Average Precision for this query
        ap = calculate_average_precision(retrieved_docs, relevant_docs)
        total_average_precision += ap

    # Calculate the mean scores across all queries
    mean_precision = total_precision / num_queries
    mean_recall = total_recall / num_queries
    mean_average_precision = total_average_precision / num_queries

    print("\n--- Overall Performance Metrics ---")
    print(f"Number of queries evaluated: {num_queries}")
    print(f"Mean Precision:            {mean_precision:.4f}")
    print(f"Mean Recall:               {mean_recall:.4f}")
    print(f"Mean Average Precision (MAP): {mean_average_precision:.4f}")

if __name__ == '__main__':
    main()