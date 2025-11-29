import os
import sys
from groq import Groq
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not API_KEY:
    print("❌ Error: GROQ_API_KEY not found.")
    print("Run: export GROQ_API_KEY='gsk_...'")
    sys.exit(1)

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Supabase credentials not found.")
    sys.exit(1)

client = Groq(api_key=API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Use Groq's Agentic Model which has built-in web search tools

MODEL_ID = "compound-beta" 

def deep_research_interview(company, role, tech_stack):
    print(f"\n⚡ Generating Confidential Interview Brief for {company}...")
    print("   (Agent is analyzing recent roles, culture, recent outages, and team culture...)\n")

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
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            # This triggers the agentic behavior in Compound models
            # We do NOT restrict domains here to allow full deep research (Github, Blogs, etc)
            temperature=0.7,
            max_completion_tokens=8192 
        )

        return response.choices[0].message.content, response.choices[0].message.tool_calls

    except Exception as e:
        return f"Error: {str(e)}", None

# ---------------------------------------------------------
# CLI INTERFACE
# ---------------------------------------------------------
def main():
    print("--- ⚡ Groq 'Compound' Deep Research Agent (Realtime Search) ---")
    
    try:
        # Fetch available resumes
        resumes_response = supabase.table("resume_details").select("resume_id").execute()
        if resumes_response.data:
            print("\nAvailable resumes to test:")
            for resume in resumes_response.data:
                print(f"- {resume['resume_id']}")
        else:
            print("\nNo resumes found to test.")
            return

        resume_id_to_test = input("\nEnter the resume_id you want to use for the test: ").strip()

        # Fetch the selected resume details
        resume_details_response = supabase.table("resume_details").select("*").eq("resume_id", resume_id_to_test).execute()
        
        if not resume_details_response.data:
            print(f"\n❌ Error: Resume with id '{resume_id_to_test}' not found.")
            return

        resume_data = resume_details_response.data[0]

        # Format the resume data into a string
        resume_string = f"Resume ID: {resume_data.get('resume_id')}\n"
        
        skills = resume_data.get('skills')
        if skills:
            resume_string += f"Skills: {', '.join(skills)}\n"
            
        experience = resume_data.get('experience')
        if experience:
            resume_string += "Experience:\n"
            for exp in experience:
                resume_string += f"  - Company: {exp.get('company')}, Role: {exp.get('role')}, Years: {exp.get('years')}\n"

        education = resume_data.get('education')
        if education:
            resume_string += "Education:\n"
            for edu in education:
                resume_string += f"  - School: {edu.get('school')}, Degree: {edu.get('degree')}, Year: {edu.get('year')}\n"
        
        projects = resume_data.get('projects')
        if projects:
            resume_string += "Projects:\n"
            for proj in projects:
                resume_string += f"  - Name: {proj.get('name')}, Tech: {proj.get('tech')}, Description: {proj.get('desc')}\n"

        print("\n--- Extracted Resume Details ---")
        print(resume_string)
        print("---------------------------------")


        c_name = input("1. Target Company Name: ").strip()
        c_role = input("2. Role Applying For:   ").strip()
        
        # For tech stack, we can now use the skills from the resume
        c_tech = ", ".join(resume_data.get('skills', []))
        print(f"3. Tech Stack / Skills (from resume): {c_tech}")


        if not all([c_name, c_role, c_tech]):
            print("\n❌ Error: All fields are required.")
            return

        result, tool_calls = deep_research_interview(c_name, c_role, c_tech)
        
        print("\n" + "="*60)
        print(result)
        print("="*60)
        
        # Optional: Debug info to show judges you actually used tools
        if tool_calls:
            print(f"\n🔧 [Debug] Tools Used: {len(tool_calls)} external search calls made.")

    except KeyboardInterrupt:
        print("\n\nExiting...")

if __name__ == "__main__":
    main()