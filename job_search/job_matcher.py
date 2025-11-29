"""
Job Matching and Compatibility Scoring Module
"""
import re
from typing import Dict, List, Any, Set
from collections import Counter


def extract_skills_from_job(job: Dict[str, Any]) -> Set[str]:
    """
    Extract skills and technologies from job description, title, and qualifications
    
    Args:
        job: Job object from SerpAPI response
        
    Returns:
        Set of extracted skills/technologies
    """
    skills = set()
    
    # Expanded tech skills list - includes more technologies
    tech_keywords = [
        # Programming languages
        'python', 'java', 'javascript', 'typescript', 'react', 'node.js', 'nodejs',
        'swift', 'objective-c', 'kotlin', 'golang', 'go', 'c#', 'php',
        'rust', 'ruby', 'perl', 'scala', 'r', 'matlab',
        # Cloud & Infrastructure
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ci/cd',
        'jenkins', 'ansible', 'puppet', 'chef', 'vagrant',
        # Databases
        'sql', 'mongodb', 'postgresql', 'mysql', 'redis', 'cassandra', 'dynamodb',
        'oracle', 'sqlite', 'elasticsearch',
        # APIs & Services
        'restful', 'api', 'graphql', 'microservices', 'soap', 'grpc',
        # ML/AI
        'machine learning', 'ml', 'ai', 'tensorflow', 'pytorch', 'keras',
        'deep learning', 'neural networks', 'nlp', 'computer vision',
        # Mobile & Web
        'ios', 'android', 'mobile', 'web', 'frontend', 'backend', 'full stack',
        'html', 'css', 'angular', 'vue', 'next.js', 'svelte',
        # Methodologies
        'agile', 'scrum', 'kanban', 'devops', 'git', 'github', 'gitlab',
        # IDEs & Tools
        'xcode', 'android studio', 'ide', 'visual studio', 'eclipse',
        # Operating Systems
        'linux', 'unix', 'windows', 'macos',
        # Data & Analytics
        'data engineering', 'etl', 'spark', 'hadoop', 'kafka',
        'snowflake', 'clickhouse', 'data pipeline', 'airflow',
        # Security & Networking
        'ssl', 'tls', 'openssl', 'cryptography', 'security',
        'network programming', 'networking', 'tcp/ip', 'http', 'https',
        # Frameworks
        'spring', 'django', 'flask', 'express', 'nestjs', 'fastapi',
        'laravel', 'rails', 'asp.net',
        # Servers & Web
        'nginx', 'apache', 'tomcat', 'iis',
    ]
    
    # Combine description, title, and qualifications
    text_content = ""
    
    # Add job title (important for skills like "C++ with SSL")
    if job.get("title"):
        text_content += job["title"].lower() + " "
    
    if job.get("description"):
        text_content += job["description"].lower() + " "
    
    if job.get("job_highlights"):
        for highlight in job["job_highlights"]:
            if highlight.get("title") == "Qualifications":
                for item in highlight.get("items", []):
                    text_content += item.lower() + " "
    
    # Special handling for C++ (regex issues with ++)
    text_lower = text_content.lower()
    if any(term in text_lower for term in ['c++', 'cpp', 'c plus plus', 'cplusplus']):
        skills.add('c++')
    
    # Extract other skills using keyword matching
    for keyword in tech_keywords:
        # Skip c++ since we handle it above
        if keyword == 'c++':
            continue
            
        # Use word boundaries for most keywords
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_content, re.IGNORECASE):
            skills.add(keyword.lower())
    
    return skills


def extract_experience_requirement(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract experience level requirements from job description
    
    Returns:
        Dict with min_years, max_years, level (junior/mid/senior)
    """
    text_content = ""
    if job.get("description"):
        text_content += job["description"] + " "
    
    if job.get("job_highlights"):
        for highlight in job["job_highlights"]:
            if highlight.get("title") == "Qualifications":
                for item in highlight.get("items", []):
                    text_content += item + " "
    
    # Patterns to match years of experience (improved patterns)
    years_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|professional|software|development|engineering)',
        r'(\d+)\s*-\s*(\d+)\s*years?\s*(?:of\s*)?(?:experience|professional|software|development|engineering)',
        r'(\d+)\s*to\s*(\d+)\s*years?\s*(?:of\s*)?(?:experience|professional|software|development|engineering)',
        r'(\d+)\+?\s*years?\s*(?:relevant|relative|software|development|engineering)\s*experience',
        r'(\d+)\s*-\s*(\d+)\+?\s*years?\s*(?:of\s*)?experience',
    ]
    
    min_years = None
    max_years = None
    
    for pattern in years_patterns:
        matches = re.finditer(pattern, text_content, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) == 1:
                years = int(match.group(1))
                if min_years is None or years < min_years:
                    min_years = years
                if max_years is None or years > max_years:
                    max_years = years
            elif len(match.groups()) == 2:
                min_val = int(match.group(1))
                max_val = int(match.group(2))
                if min_years is None or min_val < min_years:
                    min_years = min_val
                if max_years is None or max_val > max_years:
                    max_years = max_val
    
    # Determine level based on years
    level = "mid"
    if min_years:
        if min_years <= 2:
            level = "junior"
        elif min_years >= 8:
            level = "senior"
        elif min_years >= 5:
            level = "senior"
    
    # Also check for explicit level mentions
    text_lower = text_content.lower()
    if any(word in text_lower for word in ["junior", "entry", "associate", "intern"]):
        level = "junior"
    elif any(word in text_lower for word in ["senior", "staff", "principal", "lead"]):
        level = "senior"
    
    return {
        "min_years": min_years,
        "max_years": max_years,
        "level": level
    }


def calculate_compatibility_score(
    job: Dict[str, Any],
    user_skills: Set[str],
    user_experience_years: int,
    user_location: str = None
) -> Dict[str, Any]:
    """
    Calculate compatibility score between user profile and job
    
    Returns:
        Dict with score (0-100) and breakdown
    """
    job_skills = extract_skills_from_job(job)
    exp_req = extract_experience_requirement(job)
    
    # Skill match score (40%)
    if job_skills:
        matching_skills = user_skills.intersection(job_skills)
        skill_score = (len(matching_skills) / len(job_skills)) * 100
        skill_score = min(skill_score, 100)  # Cap at 100
    else:
        skill_score = 50  # Neutral if no skills extracted
        matching_skills = set()
    
    # Experience match score (25%)
    exp_score = 50  # Default neutral
    
    if exp_req["min_years"]:
        # Use years-based matching (preferred method)
        user_years = user_experience_years
        req_years = exp_req["min_years"]
        
        if user_years >= req_years:
            # User has more or equal experience
            if user_years <= req_years + 2:
                exp_score = 100  # Perfect match
            elif user_years <= req_years + 5:
                exp_score = 80  # Good match
            else:
                exp_score = 60  # Overqualified but still relevant
        else:
            # User has less experience
            diff = req_years - user_years
            if diff == 1:
                exp_score = 70  # Close
            elif diff == 2:
                exp_score = 50  # Moderate gap
            else:
                exp_score = 30  # Significant gap
    elif exp_req["level"]:
        # Fallback: Use level-based matching when years not available
        # Map user experience to level
        if user_experience_years <= 2:
            user_level = "junior"
        elif user_experience_years <= 4:
            user_level = "mid"
        elif user_experience_years <= 7:
            user_level = "senior"
        else:
            user_level = "senior"  # 8+ years is definitely senior
        
        job_level = exp_req["level"]
        
        # Match levels
        if user_level == job_level:
            exp_score = 100  # Perfect match
        elif job_level == "junior" and user_level in ["mid", "senior"]:
            exp_score = 85  # Overqualified but acceptable
        elif job_level == "mid" and user_level == "senior":
            exp_score = 80  # Overqualified
        elif job_level == "mid" and user_level == "junior":
            exp_score = 65  # Slightly underqualified but close
        elif job_level == "senior" and user_level == "junior":
            exp_score = 35  # Significantly underqualified
        elif job_level == "senior" and user_level == "mid":
            exp_score = 55  # Moderately underqualified
        else:
            exp_score = 50  # Neutral (shouldn't happen with current levels)
    
    # Location match score (10%)
    location_score = 50  # Default neutral
    if user_location and job.get("location"):
        job_loc = job["location"].lower()
        user_loc = user_location.lower()
        
        # Check for exact match or same city/state
        if user_loc in job_loc or job_loc in user_loc:
            location_score = 100
        elif any(city in job_loc for city in user_loc.split(",")):
            location_score = 70
        elif "remote" in job_loc or "remote" in job.get("description", "").lower():
            location_score = 100  # Remote matches any location
    
    # Education match (10%)
    education_score = 50  # Default neutral
    description = job.get("description", "").lower()
    if "bachelor" in description or "degree" in description:
        # Assume user has degree (can be enhanced with actual resume data)
        education_score = 100
    else:
        education_score = 100  # No degree requirement
    
    # Additional factors (15%) - salary, benefits, etc.
    additional_score = 50
    if job.get("detected_extensions", {}).get("salary"):
        additional_score += 10  # Has salary info
    if job.get("detected_extensions", {}).get("health_insurance"):
        additional_score += 5  # Has health insurance
    
    # Weighted total score
    total_score = (
        skill_score * 0.40 +
        exp_score * 0.25 +
        location_score * 0.10 +
        education_score * 0.10 +
        additional_score * 0.15
    )
    
    return {
        "total_score": round(total_score, 2),
        "breakdown": {
            "skill_match": round(skill_score, 2),
            "experience_match": round(exp_score, 2),
            "location_match": round(location_score, 2),
            "education_match": round(education_score, 2),
            "additional_factors": round(additional_score, 2)
        },
        "matching_skills": list(matching_skills),
        "missing_skills": list(job_skills - user_skills),
        "required_skills": list(job_skills),  # All skills extracted from job description
        "experience_requirement": exp_req
    }


def generate_match_explanation(
    job: Dict[str, Any],
    compatibility: Dict[str, Any]
) -> List[str]:
    """
    Generate human-readable explanation for why job matches user
    
    Returns:
        List of explanation strings
    """
    explanations = []
    
    score = compatibility["total_score"]
    breakdown = compatibility["breakdown"]
    
    # Overall match strength
    if score >= 80:
        explanations.append(f"Strong match ({score}% compatibility)")
    elif score >= 60:
        explanations.append(f"Good match ({score}% compatibility)")
    elif score >= 40:
        explanations.append(f"Moderate match ({score}% compatibility)")
    else:
        explanations.append(f"Weak match ({score}% compatibility)")
    
    # Skill match details
    matching_skills = compatibility["matching_skills"]
    missing_skills = compatibility["missing_skills"]
    required_skills = compatibility.get("required_skills", [])
    total_required = len(required_skills) if required_skills else (len(matching_skills) + len(missing_skills))
    
    if total_required > 0:
        skills_str = ", ".join(matching_skills[:5]) if matching_skills else "none"
        explanations.append(f"Skills match: You have {len(matching_skills)}/{total_required} required skills ({skills_str})")
    
    if missing_skills:
        missing_str = ", ".join(missing_skills[:3])  # Show top 3 missing
        explanations.append(f"Missing skills: {missing_str} (mentioned in job requirements)")
    
    # Experience match
    exp_req = compatibility["experience_requirement"]
    if exp_req["min_years"]:
        level_text = f" ({exp_req['level']} level)" if exp_req['level'] else ""
        explanations.append(f"Experience level: Job requires {exp_req['min_years']}+ years{level_text} - {breakdown['experience_match']}% match")
    elif exp_req["level"]:
        # Map user years to level for comparison
        user_years = compatibility.get("user_experience_years", 0)
        if user_years <= 2:
            user_level = "junior"
        elif user_years <= 4:
            user_level = "mid"
        else:
            user_level = "senior"
        explanations.append(f"Experience level: Job requires {exp_req['level']} level (you have {user_level} level based on {user_years} years) - {breakdown['experience_match']}% match")
    
    # Location
    if breakdown["location_match"] >= 70:
        explanations.append(f"Location: {job.get('location', 'N/A')} - Good match")
    
    return explanations


def match_jobs_to_user(
    jobs: List[Dict[str, Any]],
    user_skills: Set[str],
    user_experience_years: int,
    user_location: str = None
) -> List[Dict[str, Any]]:
    """
    Match and rank jobs based on user profile
    
    Args:
        jobs: List of job objects from SerpAPI
        user_skills: Set of user's skills
        user_experience_years: User's years of experience
        user_location: User's preferred location
        
    Returns:
        List of matched jobs with compatibility scores and explanations
    """
    matched_jobs = []
    
    for job in jobs:
        compatibility = calculate_compatibility_score(
            job, user_skills, user_experience_years, user_location
        )
        
        # Add user_experience_years to compatibility dict for explanation generation
        compatibility["user_experience_years"] = user_experience_years
        
        explanations = generate_match_explanation(job, compatibility)
        
        matched_job = {
            "job_id": job.get("job_id"),
            "title": job.get("title"),
            "company_name": job.get("company_name"),
            "location": job.get("location"),
            "source": job.get("via"),  # Source where job was found (Indeed, LinkedIn, etc.)
            "posted_at": job.get("detected_extensions", {}).get("posted_at"),
            "salary": job.get("detected_extensions", {}).get("salary"),
            "schedule_type": job.get("detected_extensions", {}).get("schedule_type"),
            "compatibility_score": compatibility["total_score"],
            "score_breakdown": compatibility["breakdown"],
            "match_explanations": explanations,
            "matching_skills": compatibility["matching_skills"],
            "missing_skills": compatibility["missing_skills"],
            "required_skills": compatibility.get("required_skills", []),  # All skills extracted from job description
            "experience_requirement": compatibility["experience_requirement"],
            "apply_link": job.get("apply_options", [{}])[0].get("link") if job.get("apply_options") else None,
            "description_preview": job.get("description", "")[:200] + "..." if job.get("description") else None
        }
        
        matched_jobs.append(matched_job)
    
    # Sort by compatibility score (highest first)
    matched_jobs.sort(key=lambda x: x["compatibility_score"], reverse=True)
    
    return matched_jobs

