
import json
import os

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../../data/synthetic/synthetic_queries_lowercase_1k.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../../data/synthetic/synthetic_queries_lowercase_blind_1k.json")

def create_lowercase_blind_dataset():
    """Removes sensitive labels from lowercase dataset."""
    
    print(f"Reading from {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
            
        blind_data = []
        for item in data:
            blind_item = {
                "id": item["id"],
                "query": item["query"],
                "domain": item["domain"]
                # Sensitive removed
            }
            blind_data.append(blind_item)
            
        print(f"Processed {len(blind_data)} queries.")
        
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(blind_data, f, indent=2)
            
        print(f"Saved lowercase blind dataset to {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_lowercase_blind_dataset()
