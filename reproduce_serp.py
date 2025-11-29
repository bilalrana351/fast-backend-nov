import requests
import os

# Using the key from the error log
API_KEY = "111d68344dd8487f0704dec468c8c010d62e1fd39ab659cc2e92ab7a8f7c18b6"

def test_serp():
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_jobs",
        "q": "Full Stack Engineer",
        "location": "Remote",
        "api_key": API_KEY,
        "num": 10
    }
    
    print(f"Testing URL: {url}")
    print(f"Params: {params}")
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

if __name__ == "__main__":
    test_serp()
