import requests
import json
import asyncio
from typing import List, Dict, Any, Optional
from groq import AsyncGroq

class JobService:
    """Service for searching and scoring jobs"""
    
    def __init__(self, groq_api_key: str, serp_api_key: str):
        self.groq_client = AsyncGroq(api_key=groq_api_key)
        self.serp_api_key = serp_api_key
        self.model = "llama-3.3-70b-versatile"
        
    async def search_jobs(self, query: str, location: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs using SerpAPI (Google Jobs engine)
        """
        if not self.serp_api_key:
            raise ValueError("SERP_API_KEY is not set")
            
        url = "https://serpapi.com/search"
        # Handle "Remote" location which SerpAPI doesn't support as a location parameter
        print(f"DEBUG: search_jobs called with query='{query}', location='{location}'")
        
        if location and "remote" in location.lower():
            print("DEBUG: Detected Remote location, modifying params...")
            query += " Remote"
            location = None
            
        print(f"DEBUG: Final location='{location}'")
            
        params = {
            "engine": "google_jobs",
            "q": query,
            "api_key": self.serp_api_key,
            "num": num_results
        }
        
        if location:
            params["location"] = location
        
        # Run synchronous request in a thread pool to avoid blocking async loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.get(url, params=params))
        response.raise_for_status()
        
        data = response.json()
        return data.get("jobs_results", [])

    async def score_jobs_with_groq(self, resume_data: Dict[str, Any], jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score jobs based on resume compatibility using Groq
        """
        # Prepare a simplified list of jobs for the LLM to reduce token usage
        jobs_for_prompt = []
        for job in jobs:
            jobs_for_prompt.append({
                "job_id": job.get("job_id"),
                "title": job.get("title"),
                "company": job.get("company_name"),
                "description": job.get("description", "")[:500]  # Truncate description
            })
            
        # Prepare resume summary
        resume_summary = {
            "skills": resume_data.get("skills", []),
            "experience": [
                f"{exp.get('role')} at {exp.get('company')}" 
                for exp in resume_data.get("experience", [])
            ],
            "education": [
                f"{edu.get('degree')} in {edu.get('field')}" 
                for edu in resume_data.get("education", [])
            ]
        }
        
        prompt = f"""
        You are a career coach. Evaluate the compatibility between a candidate and a list of jobs.
        
        Candidate Profile:
        {json.dumps(resume_summary, indent=2)}
        
        Jobs:
        {json.dumps(jobs_for_prompt, indent=2)}
        
        For each job, provide:
        1. A compatibility score (0-100).
        2. A brief explanation (1-2 sentences) of why it's a match or not.
        3. Key requirements from the job description (list of 3-5 short items).
        4. Alignment analysis: Pros (matching skills/experience) and Cons (missing skills/gaps).
        
        Return ONLY a valid JSON object in this format:
        {{
            "scores": [
                {{
                    "job_id": "id from input",
                    "score": 85,
                    "explanation": "Good match because...",
                    "key_requirements": ["Python", "FastAPI", "AWS"],
                    "alignment": {{
                        "pros": ["Strong Python experience", "Cloud knowledge"],
                        "cons": ["No React experience"]
                    }}
                }}
            ]
        }}
        """
        
        try:
            chat_completion = await self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that evaluates job compatibility. Return only JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = chat_completion.choices[0].message.content
            result = json.loads(content)
            scores_map = {item["job_id"]: item for item in result.get("scores", [])}
            
            # Merge scores back into original job objects
            scored_jobs = []
            for job in jobs:
                job_id = job.get("job_id")
                score_info = scores_map.get(job_id, {
                    "score": 0, 
                    "explanation": "Not evaluated",
                    "key_requirements": [],
                    "alignment": {"pros": [], "cons": []}
                })
                
                # Create a clean job object for the frontend
                scored_job = {
                    "job_id": job_id,
                    "title": job.get("title"),
                    "company_name": job.get("company_name"),
                    "location": job.get("location"),
                    "via": job.get("via"),
                    "description": job.get("description"),
                    "thumbnail": job.get("thumbnail"),
                    "extensions": job.get("detected_extensions", {}),
                    "apply_link": job.get("apply_options", [{}])[0].get("link") if job.get("apply_options") else None,
                    "compatibility_score": score_info.get("score", 0),
                    "match_explanation": score_info.get("explanation", "No explanation available"),
                    "key_requirements": score_info.get("key_requirements", []),
                    "alignment": score_info.get("alignment", {"pros": [], "cons": []})
                }
                scored_jobs.append(scored_job)
                
            # Sort by score descending
            scored_jobs.sort(key=lambda x: x["compatibility_score"], reverse=True)
            return scored_jobs
            
        except Exception as e:
            print(f"Error scoring jobs with Groq: {e}")
            # Fallback: return jobs without scores if LLM fails
            return [
                {
                    "job_id": job.get("job_id"),
                    "title": job.get("title"),
                    "company_name": job.get("company_name"),
                    "location": job.get("location"),
                    "via": job.get("via"),
                    "description": job.get("description"),
                    "apply_link": job.get("apply_options", [{}])[0].get("link") if job.get("apply_options") else None,
                    "compatibility_score": 0,
                    "match_explanation": "Scoring unavailable"
                }
                for job in jobs
            ]
