import pdfplumber
import httpx
import json
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
from groq import AsyncGroq


class ResumeProcessor:
    """Service for processing resume PDFs and extracting structured data using Groq LLM"""
    
    def __init__(self, groq_api_key: str):
        self.client = AsyncGroq(api_key=groq_api_key)
        self.model = "llama-3.3-70b-versatile"
    
    async def download_pdf(self, file_url: str) -> bytes:
        """Download PDF from URL and return bytes"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(file_url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            raise Exception(f"Failed to download PDF: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes using pdfplumber"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_file_path = tmp_file.name
            
            text_content = []
            with pdfplumber.open(tmp_file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            
            # Clean up temp file
            Path(tmp_file_path).unlink(missing_ok=True)
            
            if not text_content:
                raise Exception("No text could be extracted from PDF")
            
            return "\n\n".join(text_content)
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    async def extract_structured_data_with_groq(self, resume_text: str) -> Dict[str, Any]:
        """Use Groq LLM to extract structured data from resume text"""
        
        prompt = f"""Extract the following information from this resume text and return ONLY valid JSON with no additional text or explanation.

The JSON should have this exact structure:
{{
  "skills": ["skill1", "skill2", ...],
  "experience": [
    {{"company": "Company Name", "role": "Job Title", "duration": "Start Date - End Date", "description": "Brief description of responsibilities"}}
  ],
  "education": [
    {{"school": "School Name", "degree": "Degree Type", "field": "Field of Study", "year": "Graduation Year"}}
  ],
  "projects": [
    {{"name": "Project Name", "technologies": "Technologies used", "description": "Project description"}}
  ]
}}

Rules:
- Extract ALL skills mentioned (technical skills, tools, frameworks, languages, etc.)
- For experience, include all job positions with company, role, duration, and key responsibilities
- For education, include all degrees, certifications, and relevant coursework
- For projects, include personal projects, academic projects, or notable work
- If a section has no information, return an empty array
- Return ONLY the JSON object, no markdown formatting, no explanations

Resume text:
{resume_text}"""

        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a resume parsing assistant. Extract structured information from resumes and return only valid JSON with no additional formatting or text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=2000,
            )
            
            groq_response = chat_completion.choices[0].message.content
            
            # Remove markdown code blocks if present
            groq_response = groq_response.strip()
            if groq_response.startswith("```json"):
                groq_response = groq_response[7:]
            if groq_response.startswith("```"):
                groq_response = groq_response[3:]
            if groq_response.endswith("```"):
                groq_response = groq_response[:-3]
            groq_response = groq_response.strip()
            
            # Parse JSON response
            structured_data = json.loads(groq_response)
            
            # Validate structure
            required_keys = ["skills", "experience", "education", "projects"]
            for key in required_keys:
                if key not in structured_data:
                    structured_data[key] = []
            
            return structured_data
                
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Groq response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to extract structured data: {str(e)}")
    
    async def process_resume(self, file_url: str) -> Dict[str, Any]:
        """
        Main method to process a resume:
        1. Download PDF from URL
        2. Extract text using pdfplumber
        3. Extract structured data using Groq LLM
        
        Returns: Dictionary with skills, experience, education, projects
        """
        try:
            # Step 1: Download PDF
            pdf_bytes = await self.download_pdf(file_url)
            
            # Step 2: Extract text
            resume_text = self.extract_text_from_pdf(pdf_bytes)
            
            # Step 3: Extract structured data with Groq
            structured_data = await self.extract_structured_data_with_groq(resume_text)
            
            return structured_data
            
        except Exception as e:
            raise Exception(f"Resume processing failed: {str(e)}")

