import os
import json
import argparse
from datetime import datetime
from typing import List, Dict

try:
    from sentence_transformers import SentenceTransformer, util
    HAS_MINILM = True
except ImportError:
    HAS_MINILM = False

def compute_minilm_sts(pairs: List[tuple]) -> List[float]:
    """Compute STS for a list of (text1, text2) pairs using all-MiniLM-L6-v2."""
    if not HAS_MINILM:
        print("Error: sentence-transformers not installed. Run with 'uv run --with sentence-transformers'")
        return [0.0] * len(pairs)
    
    print(f"Loading all-MiniLM-L6-v2 and processing {len(pairs)} pairs...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    scores = []
    # Batch processing is more efficient
    texts1 = [p[0] for p in pairs]
    texts2 = [p[1] for p in pairs]
    
    # Check for empty strings to avoid errors
    for i in range(len(texts1)):
        if not texts1[i]: texts1[i] = " "
        if not texts2[i]: texts2[i] = " "
        
    embeddings1 = model.encode(texts1, convert_to_tensor=True)
    embeddings2 = model.encode(texts2, convert_to_tensor=True)
    
    cosine_scores = util.cos_sim(embeddings1, embeddings2)
    
    # Extract diagonal elements for paired similarity
    for i in range(len(pairs)):
        scores.append(float(cosine_scores[i][i].item()))
        
    return scores

def process_file(file_path: str):
    """Load detailed JSON, update STS scores, and save back."""
    print(f"\nProcessing {file_path}...")
    with open(file_path, "r") as f:
        data = json.load(f)
    
    if isinstance(data, dict) and "per_model" in data:
        # EXP03 structure
        for model_tag, model_data in data["per_model"].items():
            process_results_list(model_data["per_query"], f"Model {model_tag}")
            # Update average
            if model_data["per_query"]:
                model_data["avg_utility_sts"] = sum(r["utility_sts"] for r in model_data["per_query"]) / len(model_data["per_query"])
                if "full_redaction_utility_sts" in model_data["per_query"][0]:
                    model_data["avg_full_redaction_sts"] = sum(r.get("full_redaction_utility_sts", 0) for r in model_data["per_query"]) / len(model_data["per_query"])
    elif isinstance(data, list):
        # EXP01 structure
        process_results_list(data, "All queries")
    
    # Save with a suffix or overwrite? User said "run and then draft", so overwrite is probably fine if we have backup
    # For safety, let's create a new file
    output_path = file_path.replace(".json", "_minilm.json")
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved updated results to: {output_path}")

def process_results_list(results: List[Dict], label: str):
    """Helper to process a list of result dictionaries."""
    print(f"  {label}: extracting pairs...")
    
    # Pairs for Sovereign Learner: (no_protection_response, recontextualized_response)
    sl_pairs = []
    # Pairs for Redaction: (no_protection_response, redaction_response)
    redact_pairs = []
    
    indices_with_refs = []
    
    for i, r in enumerate(results):
        ref = r.get("no_protection_response")
        target = r.get("recontextualized_response") or r.get("cloud_response")
        redact = r.get("redaction_response")
        
        if ref:
            sl_pairs.append((ref, target))
            if redact:
                redact_pairs.append((ref, redact))
            indices_with_refs.append(i)
        else:
            # Fallback if no_protection_response is missing: use original_query as reference
            # Note: This is less accurate than EXP01's output-vs-output method
            sl_pairs.append((r["original_query"], target))
            if redact:
                redact_pairs.append((r["original_query"], redact))
            indices_with_refs.append(i)

    if not sl_pairs:
        print(f"    No processable pairs found for {label}")
        return

    sl_scores = compute_minilm_sts(sl_pairs)
    redact_scores = compute_minilm_sts(redact_pairs) if redact_pairs else []
    
    for i, idx in enumerate(indices_with_refs):
        results[idx]["utility_sts"] = sl_scores[i]
        results[idx]["sts_metric"] = "all-MiniLM-L6-v2"
        if redact_scores:
            results[idx]["full_redaction_utility_sts"] = redact_scores[i]

def main():
    parser = argparse.ArgumentParser(description="Post-process experiment results with MiniLM STS.")
    parser.add_argument("files", nargs="+", help="JSON result files to process")
    args = parser.parse_args()
    
    if not HAS_MINILM:
        print("\n" + "!"*60)
        print("WARNING: sentence-transformers not found in current environment.")
        print("Please run this script using:")
        print("uv run --with sentence-transformers python experiments/shared_utils/sts_post_processor.py <files>")
        print("!"*60 + "\n")
        return

    for f in args.files:
        if os.path.exists(f):
            process_file(f)
        else:
            print(f"File not found: {f}")

if __name__ == "__main__":
    main()
