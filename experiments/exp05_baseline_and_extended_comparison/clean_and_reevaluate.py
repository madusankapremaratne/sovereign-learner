import json
import os
import re
import requests
import time
from datetime import datetime

# Configuration
INPUT_FILE = "experiments/results/exp05_extended_results_20260304_113217.json"
OUTPUT_FILE = "experiments/results/exp05_extended_results_cleaned_20260304.json"
OLLAMA_URL = "http://localhost:11434/api/generate"

def clean_output(text):
    """
    Heuristic to remove CrewAI thoughts, actions, and internal JSON wrappers.
    """
    if not isinstance(text, str):
        return str(text)

    # 1. Remove CrewAI Trace (Thought, Action, Action Input)
    cleaned = re.sub(r'Thought:.*?\n', '', text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'Action:.*?\n', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'Action Input:.*?\n', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Extract from JSON if it's wrapped
    try:
        # Look for JSON-like block
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0).replace("'", '"'))
            if 'response' in data:
                if isinstance(data['response'], dict) and 'description' in data['response']:
                    cleaned = data['response']['description']
                else:
                    cleaned = data['response']
            elif 'result' in data:
                cleaned = data['result']
    except:
        pass

    # 3. Remove "Confirmation of successful local database entry" logs
    cleaned = re.sub(r'Confirmation of successful local database entry.*?\n', '', cleaned, flags=re.IGNORECASE)
    
    # 4. Remove internal agent headers
    cleaned = re.sub(r'### (Shadower|Distiller|Auditor|KPL|Sovereignty).*?\n', '', cleaned, flags=re.IGNORECASE)
    
    # 5. Extract "Final Answer" if present
    final_match = re.search(r'Final Answer:\s*(.*)', cleaned, re.DOTALL | re.IGNORECASE)
    if final_match:
        cleaned = final_match.group(1)

    # 6. Final cleanup
    cleaned = cleaned.strip()
    # If we cleaned too much and it's empty, return original but stripped of obvious JSON query leaks
    if not cleaned or len(cleaned) < 5:
        # Fallback: just remove common JSON keys that leak original query
        cleaned = re.sub(r'["\']query["\']\s*:\s*["\'].*?["\']', '[REDACTED_QUERY]', text)
        cleaned = cleaned.strip()

    return cleaned

def call_llm(prompt):
    try:
        payload = {"model": "llama3.2", "prompt": prompt, "stream": False}
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        return response.json().get("response", "")
    except:
        return ""

def extract_score(text, key):
    try:
        match = re.search(rf'"{key}"\s*:\s*([\d\.]+)', text)
        return float(match.group(1)) if match else 0.5
    except:
        return 0.5

def evaluate(original, sanitized):
    # IP Protection Rate
    adv_prompt = f"""You are an adversary. 
Original Query: "{original}"
Sanitized Query: "{sanitized}"
Rate how much of the original sensitive information is leaked.
0.0 = Totally Private, 1.0 = Fully Leaked.
Respond with JSON: {{"leakage": 0.5}}"""
    
    leakage = extract_score(call_llm(adv_prompt), "leakage")
    ip_protection = 1.0 - leakage
    
    # Utility Score
    tutor_prompt = f"""You are a teacher.
Original Query: "{original}"
Sanitized Query: "{sanitized}"
Rate the utility of the response.
0.0 = Useless, 1.0 = Perfectly Helpful.
Respond with JSON: {{"utility": 0.8}}"""
    
    utility = extract_score(call_llm(tutor_prompt), "utility")
    
    return ip_protection, utility

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)

    raw_data = data.get("raw", {})
    new_raw_data = {}

    print("Cleaning and Re-evaluating Sovereign Learner (BL-07)...")

    for dataset_name, queries in raw_data.items():
        new_queries = []
        for q in queries:
            print(f"Dataset: {dataset_name} | Query: {q['query_id']}")
            bl07 = q['results'].get("BL-07: Sovereign Learner")
            if bl07:
                original_text = q['query']
                sanitized_text = bl07.get('sanitized', '')
                
                # Clean the text
                cleaned_text = clean_output(sanitized_text)
                
                # Re-evaluate
                print(f"  Old Protection: {bl07.get('ip_protection')} -> Re-evaluating...")
                new_ip, new_ut = evaluate(original_text, cleaned_text)
                
                bl07['sanitized_original'] = sanitized_text
                bl07['sanitized'] = cleaned_text
                bl07['ip_protection'] = new_ip
                bl07['utility'] = new_ut
                print(f"  New Protection: {new_ip} | New Utility: {new_ut}")
            
            new_queries.append(q)
        new_raw_data[dataset_name] = new_queries

    # Recalculate summary
    new_summary = []
    for dataset_name, queries in new_raw_data.items():
        ds_summary = {}
        for q in queries:
            for sys_name, metrics in q['results'].items():
                if sys_name not in ds_summary:
                    ds_summary[sys_name] = {"ip": [], "ut": [], "lat": []}
                if "ip_protection" in metrics:
                    ds_summary[sys_name]["ip"].append(metrics["ip_protection"])
                    ds_summary[sys_name]["ut"].append(metrics["utility"])
                    ds_summary[sys_name]["lat"].append(metrics["latency_ms"])
        
        for sys_name, vals in ds_summary.items():
            new_summary.append({
                "Dataset": dataset_name,
                "System": sys_name,
                "Avg Protection": sum(vals["ip"]) / len(vals["ip"]),
                "Avg Utility": sum(vals["ut"]) / len(vals["ut"]),
                "Avg Latency": sum(vals["lat"]) / len(vals["lat"])
            })

    with open(OUTPUT_FILE, 'w') as f:
        json.dump({"summary": new_summary, "raw": new_raw_data}, f, indent=2)

    print(f"\nDone! Cleaned results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
