from groq import AsyncGroq
from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel, Field
import json

class SimpleInterviewBrief(BaseModel):
    """
    A simplified, structured representation of an interview brief.
    """
    company_background: str = Field(..., description="A brief background of the company, its mission, and recent activities.")
    technical_questions: List[str] = Field(..., description="A flat list of technical interview questions.")
    behavioral_questions: List[str] = Field(..., description="A flat list of behavioral interview questions.")
    urls: List[str] = Field(..., description="A list of urls that we used to fetch the content. Give around 10-15 at max")

class DeepResearchService:
    """Service for performing deep research using Groq LLM"""
    
    def __init__(self, groq_api_key: str):
        self.client = AsyncGroq(api_key=groq_api_key)
        self.model_id = "compound-beta"
        self.structuring_model_id = "moonshotai/kimi-k2-instruct-0905"
    
    async def structure_interview_brief(self, text_input: str) -> Dict[str, Any]:
        """
        Takes unstructured text and converts it into a simple, structured JSON object.
        """
        system_prompt = (
            "You are a data structuring expert. Your task is to receive an interview preparation brief "
            "and extract four key pieces of information: the company's background, a list of technical questions, "
            "a list of behavioral questions, and a list of sources/URLs. Format this into a clean JSON object that conforms to the provided simple schema."
        )

        user_content = f"""
        Please extract the company background, technical questions, behavioral questions, and sources (URLs) from the following brief into a JSON object based on the `SimpleInterviewBrief` schema.

        --- UNSTRUCTURED BRIEF ---
        {text_input}
        --- END OF BRIEF ---
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.structuring_model_id,
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
            # Validate with Pydantic
            validated_brief = SimpleInterviewBrief.model_validate(structured_data)
            return validated_brief.model_dump()

        except Exception as e:
            # Fallback to returning error in structure if parsing fails
            return {
                "company_background": "Error parsing background.",
                "technical_questions": ["Error parsing technical questions."],
                "behavioral_questions": ["Error parsing behavioral questions."],
                "urls": [],
                "error": str(e)
            }

    async def perform_deep_research(self, company: str, role: str, tech_stack: str) -> Tuple[Dict[str, Any], Optional[list]]:
        """
        Perform deep research on a company and role.
        Returns a tuple of (structured_data, tool_calls).
        """
        
        # --- THE REFINED "HEADHUNTER" PROMPT ---
        system_prompt = (
            "You are a Senior Technical Recruiter & Career Strategist for top-tier tech firms. "
            "Your goal is to prepare a candidate for a specific, high-stakes technical loop. "
            "You have access to live web search. USE IT to find recent engineering challenges, outages, or product launches. "
            
            "**CRITICAL INSTRUCTIONS:**"
            "1. **Contextualize Everything:** Do not ask generic questions. Connect every technical question to a specific tool or problem the company actually has."
            "2. **The 'Why':** For every question you generate, add a 'Strategy Note' explaining WHY this question is highly probable for this specific team."
            "3. **Culture Decoder:** Map behavioral questions explicitly to the company's public Core Values (e.g., 'Amazon Leadership Principles')."
            "4. **No Fluff:** Be concise, direct, and high-signal. Write like a dossier."
            
        )

        user_query = f"""
        TARGET:
        - Company: {company}
        - Role: {role}
        - Candidate Tech Stack: {tech_stack}

        MISSION:
        *** High-level objective:

        Using the inputs, perform a focused, defensible, multi-step internet research process and deliver a compact, 
        actionable interview prep pack containing role/company context, prioritized topics, deep technical questions, 
        role-specific behavioral questions, study timelines, and quick debugging/pitfall notes.

        1. Validate & normalize inputs

        Normalize technology names (e.g., nodejs → Node.js, py3 → Python 3.x) and record normalization table in the output.
        If company_name appears to match multiple entities (e.g., common name), choose the most likely by relevance and mention which entity you researched.

        2.Scoping & hypothesis
        Infer hiring priorities from company domain, size, and known tech stack (e.g., fintech → reliability and security; early-stage startup → full-stack breadth).
        Produce a 1-2 line hypothesis about what the company will test for this role (label clearly as “Assumption”).

        3. Live internet research
        Use live browsing tools to find current, relevant information about the company, the role, and the technologies. Prioritize: official company careers/engineering blog, GitHub org, tech blog posts, recent conference talks, major package release notes, Stack Overflow trends, Glassdoor/interview reports, and reputable tech news sites.
        Always check recency (prefer sources from the last 24 months; flag anything older).

        4. Filter & sanitize
        Remove deprecated APIs, outdated versions, or irrelevant historical practices.
        Note any critical breaking changes or version-specific behaviors that are likely to affect interview questions (e.g., Node 18 vs Node 20 differences, Python 2 vs 3).

        5. Analysis per technology
        For each key_technology, produce:
        3-6 High-value topics interviewers ask about (ranked).
        4 Core questions (fundamentals) + 3 Advanced questions + 2 Practical/Production scenario questions + 1 Trick/edge-case question.

        Short answer or bullet hints for each question (2-4 bullets, not full essays). Keep it concise.

        6. Behavioral & role-specific questions
        Generate 8-12 behavioral questions tailored to the role, company size, and inferred engineering culture. Include one behavioral question specifically intended to reveal system design tradeoff thinking or security mindset if applicable.

        Provide a concise annotated reading list (3-7 links) and hands-on tasks (2-3 exercises) mapped to the highest-priority topics.
        """

        try:
            # Step 1: Get Deep Research Content
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query},
                ],
                temperature=0.7,
                max_completion_tokens=8192 
            )
            
            raw_content = response.choices[0].message.content
            tool_calls = response.choices[0].message.tool_calls

            # Step 2: Structure the Output
            structured_data = await self.structure_interview_brief(raw_content)

            return structured_data, tool_calls

        except Exception as e:
            raise Exception(f"Deep research failed: {str(e)}")
