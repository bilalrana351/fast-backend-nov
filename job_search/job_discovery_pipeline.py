"""
Main Job Discovery Pipeline
Combines SerpAPI scraping with job matching
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Set
from dotenv import load_dotenv
import requests

from job_matcher import match_jobs_to_user, extract_skills_from_job

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def fetch_jobs_from_serpapi(
    job_title: str,
    location: str,
    num_results: int = 10,
    api_key: str = None
) -> List[Dict[str, Any]]:
    """
    Fetch jobs from SerpAPI
    
    Returns:
        List of job objects
    """
    if not api_key:
        api_key = os.getenv("SERP_API_KEY")
        if not api_key:
            raise ValueError("SERP_API_KEY not found in .env file")
    
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_jobs",
        "q": job_title,
        "location": location,
        "api_key": api_key,
        "num": num_results
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    return data.get("jobs_results", [])


def generate_search_queries(user_skills: Set[str], job_title: str) -> List[str]:
    """
    Generate multiple search queries based on user skills
    
    Returns:
        List of search query strings
    """
    queries = []
    
    # Primary query with job title
    queries.append(job_title)
    
    # Add queries with top skills
    top_skills = list(user_skills)[:3]  # Top 3 skills
    for skill in top_skills:
        queries.append(f"{job_title} {skill}")
    
    return queries


def discover_and_match_jobs(
    user_profile: Dict[str, Any],
    use_api: bool = False
) -> Dict[str, Any]:
    """
    Main pipeline: Discover jobs and match them to user profile
    
    Args:
        user_profile: Dict with skills, experience_years, location, job_title
        use_api: If True, fetch from API. If False, use cached data
        
    Returns:
        Dict with matched jobs and metadata
    """
    user_skills = set(user_profile.get("skills", []))
    user_experience_years = user_profile.get("experience_years", 0)
    user_location = user_profile.get("location", "San Francisco, CA")
    job_title = user_profile.get("job_title", "Software Engineer")
    
    jobs = []
    
    if use_api:
        # Fetch from API
        queries = generate_search_queries(user_skills, job_title)
        seen_job_ids = set()
        
        for query in queries[:2]:  # Limit to 2 queries to avoid rate limits
            try:
                fetched_jobs = fetch_jobs_from_serpapi(
                    job_title=query,
                    location=user_location,
                    num_results=10
                )
                
                for job in fetched_jobs:
                    job_id = job.get("job_id")
                    if job_id and job_id not in seen_job_ids:
                        jobs.append(job)
                        seen_job_ids.add(job_id)
            except Exception as e:
                print(f"Error fetching jobs for query '{query}': {e}")
                continue
    else:
        # Use cached data from raw_response.json
        try:
            raw_response_path = Path(__file__).parent / "raw_response.json"
            # Try multiple encodings (file appears to be UTF-16)
            content = None
            for encoding in ['utf-16', 'utf-16-le', 'utf-16-be', 'utf-8', 'utf-8-sig', 'latin-1']:
                try:
                    with open(raw_response_path, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                        # Check if we got valid content (not just null bytes)
                        if content and len(content.strip()) > 100:
                            break
                except:
                    continue
            
            if content:
                # Find JSON start - look for "search_metadata" or opening brace
                json_start = content.find('"search_metadata"')
                if json_start == -1:
                    json_start = content.find('{')
                
                if json_start != -1:
                    # Go back to find the opening brace
                    brace_pos = content.rfind('{', 0, json_start + 1)
                    if brace_pos == -1:
                        brace_pos = json_start - 10 if json_start > 10 else 0
                    
                    json_content = content[brace_pos:].strip()
                    data = json.loads(json_content)
                    jobs = data.get("jobs_results", [])
                else:
                    # Try loading entire file as JSON
                    data = json.loads(content)
                    jobs = data.get("jobs_results", [])
            else:
                jobs = []
        except Exception as e:
            print(f"Error loading cached data: {e}")
            jobs = []
    
    # Limit to first N jobs for testing
    jobs = jobs[:4]  # Get first 4 jobs
    
    # Match jobs to user profile
    matched_jobs = match_jobs_to_user(
        jobs=jobs,
        user_skills=user_skills,
        user_experience_years=user_experience_years,
        user_location=user_location
    )
    
    return {
        "user_profile": {
            "skills": list(user_skills),
            "experience_years": user_experience_years,
            "location": user_location,
            "job_title": job_title
        },
        "total_jobs_found": len(jobs),
        "matched_jobs": matched_jobs,
        "summary": {
            "average_score": round(sum(j["compatibility_score"] for j in matched_jobs) / len(matched_jobs), 2) if matched_jobs else 0,
            "high_match_count": len([j for j in matched_jobs if j["compatibility_score"] >= 70]),
            "medium_match_count": len([j for j in matched_jobs if 40 <= j["compatibility_score"] < 70]),
            "low_match_count": len([j for j in matched_jobs if j["compatibility_score"] < 40])
        }
    }


if __name__ == "__main__":
    # Test with sample user profile
    test_user_profile = {
        "skills": [
            "python", "javascript", "react", "node.js", "aws", "docker",
            "sql", "restful", "api", "git", "agile", "typescript"
        ],
        "experience_years": 4,
        "location": "San Francisco, CA",
        "job_title": "Software Engineer"
    }
    
    result = discover_and_match_jobs(test_user_profile, use_api=False)
    
    # Output as JSON
    print(json.dumps(result, indent=2))

