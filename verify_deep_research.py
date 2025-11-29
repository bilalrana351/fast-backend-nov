import requests
import json
import sys

def test_deep_research():
    url = "http://localhost:8001/api/deep-research"
    
    payload = {
        "company_name": "Anthropic",
        "role": "Senior Backend Engineer",
        "technologies": "Python, Rust, AWS, Kubernetes"
    }
    
    print(f"Testing Deep Research Endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Success!")
            print(f"Message: {data.get('message')}")
            print("\n--- Result Data Preview (Structured) ---")
            result_data = data.get('data', {})
            print(json.dumps(result_data, indent=2))
            print("----------------------------------------")
        else:
            print(f"\n❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    test_deep_research()
