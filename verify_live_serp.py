import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.job_service import JobService

# Key from user logs
API_KEY = "111d68344dd8487f0704dec468c8c010d62e1fd39ab659cc2e92ab7a8f7c18b6"

async def test_live():
    print("Testing JobService with LIVE SerpAPI key...")
    
    # Initialize service
    service = JobService("fake_groq", API_KEY)
    
    try:
        # Test with "Remote"
        print("Calling search_jobs('Full Stack Engineer', 'Remote')...")
        jobs = await service.search_jobs("Full Stack Engineer", "Remote")
        
        print(f"✅ Success! Found {len(jobs)} jobs.")
        if len(jobs) > 0:
            print(f"Sample job: {jobs[0].get('title')} at {jobs[0].get('company_name')}")
            
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_live())
