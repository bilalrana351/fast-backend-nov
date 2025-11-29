import os
import sys
from groq import Groq
from pydantic import BaseModel, Field
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    print("❌ Error: GROQ_API_KEY not found.")
    print("Run: export GROQ_API_KEY='gsk_...'")
    sys.exit(1)

client = Groq(api_key=API_KEY)

# --- Simplified Pydantic Model ---

class SimpleInterviewBrief(BaseModel):
    """
    A simplified, structured representation of an interview brief.
    """
    company_background: str = Field(..., description="A brief background of the company, its mission, and recent activities.")
    technical_questions: list[str] = Field(..., description="A flat list of technical interview questions.")
    behavioral_questions: list[str] = Field(..., description="A flat list of behavioral interview questions.")


def structure_interview_brief(text_input: str) -> str:
    """
    Takes unstructured text and converts it into a simple, structured JSON object.
    """
    print("\n🤖 Converting unstructured brief into simplified structured JSON...")

    system_prompt = (
        "You are a data structuring expert. Your task is to receive an interview preparation brief "
        "and extract only three key pieces of information: the company's background, a list of technical questions, "
        "and a list of behavioral questions. Format this into a clean JSON object that conforms to the provided simple schema."
    )

    user_content = f"""
    Please extract the company background, technical questions, and behavioral questions from the following brief into a JSON object based on the `SimpleInterviewBrief` schema.

    --- UNSTRUCTURED BRIEF ---
    {text_input}
    --- END OF BRIEF ---
    """

    try:
        response = client.chat.completions.create(
            model="moonshotai/kimi-k2-instruct-0905",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "simple_interview_brief",
                    "description": "Structures the brief into a simple JSON with background, technical, and behavioral questions.",
                    "schema": SimpleInterviewBrief.model_json_schema()
                }
            },
            temperature=0.1,
        )

        structured_data = json.loads(response.choices[0].message.content)
        validated_brief = SimpleInterviewBrief.model_validate(structured_data)
        
        return json.dumps(validated_brief.model_dump(), indent=2)

    except Exception as e:
        return f'{{"error": "Failed to structure the brief.", "details": "{str(e)}"}}'

def main():
    # This is a placeholder for the output from groqtest.py
    sample_input_from_groqtest = """
    **CONFIDENTIAL INTERVIEW BRIEF: Google - Software Engineer**

    **Background:** Google is a multinational technology company that specializes in Internet-related services and products, which include online advertising technologies, a search engine, cloud computing, software, and hardware. It is considered one of the Big Five companies in the U.S. information technology industry, alongside Amazon, Apple, Meta, and Microsoft.

    **Assumption:** Google will heavily test for large-scale system design, data structures, and algorithms, with a focus on reliability and efficiency, given their infrastructure.

    **1. Technology Analysis: Python**
    *High-Value Topics:*
    - Concurrency (GIL, asyncio, threading vs. multiprocessing)
    - Metaclasses and Descriptors
    - Memory Management and Garbage Collection

    *Core Questions:*
    - Q: Explain the Global Interpreter Lock (GIL) and its implications for a multi-threaded web server.
      - Strategy Note: Tests fundamental understanding of Python's concurrency model and its real-world limitations.
    - Q: How does Python's garbage collection work?
      - Strategy Note: Assesses knowledge of memory management, crucial for performance in long-running services.

    *Advanced Questions:*
    - Q: Describe a use case for a metaclass in a real-world application.
      - Strategy Note: Probes deep, advanced language knowledge, often used in frameworks like Django or SQLAlchemy.

    *Practical Scenario Questions:*
    - Q: You have a service that needs to make 100 independent API calls. How would you implement this efficiently in Python?
      - Strategy Note: Practical application of concurrency concepts (asyncio/aiohttp is the ideal answer).

    **2. Behavioral Questions**
    - Q: Tell me about a time you had to deal with a major production outage. What was the root cause, and what did you learn?
      - Strategy Note: Maps to Google's value of 'Respect the user.' Shows ownership and learning from failure.
    - Q: Describe a complex project you worked on and how you handled disagreements with your teammates.
      - Strategy Note: Assesses collaboration and communication skills, vital for large, cross-functional teams at Google.

    **3. Suggested Reading**
    - https://engineering.google/blog/
    - "Designing Data-Intensive Applications" by Martin Kleppmann
    """

    print("--- Groq Output Structuring Service (Simple) ---")
    
    structured_json = structure_interview_brief(sample_input_from_groqtest)
    
    print("\n--- Structured JSON Output ---")
    print(structured_json)
    print("------------------------------")


if __name__ == "__main__":
    main()