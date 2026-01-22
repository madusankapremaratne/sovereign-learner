
import json
import os

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../../data/synthetic/synthetic_queries_1k.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../../data/synthetic/synthetic_queries_blind_1k.json")

def create_blind_dataset():
    """Removes the 'sensitive' field from all queries to simulate real-world conditions."""
    
    print(f"Reading from {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
            
        blind_data = []
        for item in data:
            # Create a copy without the sensitive field
            blind_item = {
                "id": item["id"],
                "query": item["query"],
                "domain": item["domain"]
                # 'sensitive' field is INTENTIONALLY OMITTED
            }
            blind_data.append(blind_item)
            
        print(f"Processed {len(blind_data)} queries.")
        
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(blind_data, f, indent=2)
            
        print(f"Saved blind dataset to {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_blind_dataset()
