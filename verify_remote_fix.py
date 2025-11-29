import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.job_service import JobService

async def verify_fix():
    print("Verifying JobService logic for 'Remote' location...")
    
    service = JobService("fake_key", "fake_key")
    
    # Mock requests.get to capture params
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"jobs_results": []}
        mock_get.return_value = mock_response
        
        # Test with "Remote"
        await service.search_jobs("Python", "Remote")
        
        # Check arguments passed to requests.get
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        
        print(f"Params for 'Remote': {params}")
        
        if "location" in params:
            print("❌ FAIL: 'location' param is still present!")
        else:
            print("✅ PASS: 'location' param was removed.")
            
        if "Remote" in params["q"]:
            print("✅ PASS: 'Remote' added to query.")
        else:
            print("❌ FAIL: 'Remote' NOT added to query.")

if __name__ == "__main__":
    asyncio.run(verify_fix())
