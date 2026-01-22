
import json
import os

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../../data/synthetic/synthetic_queries_1k.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../../data/synthetic/synthetic_queries_lowercase_1k.json")

def create_lowercase_dataset():
    """Transforms queries and sensitive entities to lowercase."""
    
    print(f"Reading from {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
            
        lower_data = []
        for item in data:
            # Lowercase query
            lower_query = item["query"].lower()
            
            # Lowercase sensitive entities
            lower_sensitive = [s.lower() for s in item["sensitive"]]
            
            lower_item = {
                "id": item["id"],
                "query": lower_query,
                "sensitive": lower_sensitive,
                "domain": item["domain"]
            }
            lower_data.append(lower_item)
            
        print(f"Processed {len(lower_data)} queries.")
        
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(lower_data, f, indent=2)
            
        print(f"Saved lowercase dataset to {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_lowercase_dataset()
