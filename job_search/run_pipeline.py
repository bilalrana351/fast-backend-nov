"""
Run the job discovery pipeline and output JSON results
"""
import json
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from job_discovery_pipeline import discover_and_match_jobs


def main():
    # Test user profile - simulating resume parser output
    test_user_profile = {
        "skills": [
            "python", "javascript", "react", "node.js", "aws", "docker",
            "sql", "restful", "api", "git", "agile", "typescript", "java",
            "microservices", "kubernetes", "ci/cd"
        ],
        "experience_years": 4,
        "location": "Pakistan",
        "job_title": "Software Engineer"
    }
    
    # Run pipeline (use_api=True to fetch real jobs for Pakistan)
    result = discover_and_match_jobs(test_user_profile, use_api=True)
    
    # Output JSON
    output = json.dumps(result, indent=2)
    print(output)
    
    # Also save to file
    output_path = Path(__file__).parent / "matched_jobs_output.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()

