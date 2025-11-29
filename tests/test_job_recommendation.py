import asyncio
import os
import sys
import json
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.job_service import JobService

async def test_job_service():
    print("Testing JobService...")
    
    # Setup mocks
    groq_key = "test_groq"
    serp_key = "test_serp"
    
    service = JobService(groq_key, serp_key)
    
    # 1. Test Search Jobs (Mocking requests.get)
    print("\n1. Testing search_jobs...")
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jobs_results": [
                {"title": "Python Dev", "company_name": "Tech Co", "location": "Remote", "job_id": "1"},
                {"title": "React Dev", "company_name": "Web Corp", "location": "Remote", "job_id": "2"}
            ]
        }
        mock_get.return_value = mock_response
        
        jobs = await service.search_jobs("Python", "Remote")
        
        assert len(jobs) == 2
        assert jobs[0]["title"] == "Python Dev"
        print("✅ search_jobs successful")
        
    # 2. Test Score Jobs (Mocking AsyncGroq)
    print("\n2. Testing score_jobs_with_groq...")
    
    # Mock resume data
    resume_data = {
        "skills": ["Python", "Django"],
        "experience": [{"role": "Backend Dev", "company": "Old Corp"}]
    }
    
    # Mock jobs
    jobs_to_score = [
        {"title": "Python Dev", "company_name": "Tech Co", "job_id": "1", "description": "Need Python"},
        {"title": "Java Dev", "company_name": "Legacy Co", "job_id": "2", "description": "Need Java"}
    ]
    
    # Mock Groq response
    mock_llm_response = {
        "scores": [
            {"job_id": "1", "score": 90, "explanation": "Great match"},
            {"job_id": "2", "score": 20, "explanation": "Bad match"}
        ]
    }
    
    with patch.object(service.groq_client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = json.dumps(mock_llm_response)
        mock_create.return_value = mock_completion
        
        scored_jobs = await service.score_jobs_with_groq(resume_data, jobs_to_score)
        
        assert len(scored_jobs) == 2
        # Check sorting (highest score first)
        assert scored_jobs[0]["job_id"] == "1"
        assert scored_jobs[0]["compatibility_score"] == 90
        assert scored_jobs[1]["job_id"] == "2"
        assert scored_jobs[1]["compatibility_score"] == 20
        print("✅ score_jobs_with_groq successful")

if __name__ == "__main__":
    asyncio.run(test_job_service())
