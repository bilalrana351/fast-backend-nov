from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import services
from services.resume_processor import ResumeProcessor
from services.supabase_client import SupabaseService

app = FastAPI(
    title="Backend API",
    description="FastAPI backend for webdevhackathon",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize services
groq_api_key = os.getenv("GROQ_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not groq_api_key or not supabase_url or not supabase_key:
    raise ValueError("Missing required environment variables. Please check .env file.")

resume_processor = ResumeProcessor(groq_api_key)
supabase_service = SupabaseService(supabase_url, supabase_key)


# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


class MessageResponse(BaseModel):
    message: str


class ResumeAnalyzeRequest(BaseModel):
    resume_id: str
    file_url: str
    user_id: str


class ResumeAnalyzeResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ExperienceItem(BaseModel):
    company: str
    role: str
    duration: str
    description: str


class EducationItem(BaseModel):
    school: str
    degree: str
    field: str
    year: str


class ProjectItem(BaseModel):
    name: str
    technologies: str
    description: str


class ResumeDetailsResponse(BaseModel):
    id: str
    resume_id: str
    skills: List[str]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    parsed_at: str


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to the Backend API"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now()
    )


@app.get("/api/hello", response_model=MessageResponse)
async def hello():
    """Hello endpoint"""
    return MessageResponse(message="Hello from backend!")


@app.post("/api/resume/analyze", response_model=ResumeAnalyzeResponse)
async def analyze_resume(request: ResumeAnalyzeRequest):
    """
    Analyze a resume PDF and extract structured data
    
    Flow:
    1. Verify resume ownership
    2. Download PDF from Supabase Storage
    3. Extract text using pdfplumber
    4. Extract structured data using Groq LLM
    5. Store results in resume_details table
    """
    try:
        # Verify the resume belongs to the user
        is_owner = await supabase_service.verify_resume_ownership(
            request.resume_id, 
            request.user_id
        )
        
        if not is_owner:
            raise HTTPException(
                status_code=403, 
                detail="Unauthorized: You don't have permission to analyze this resume"
            )
        
        # Process the resume
        structured_data = await resume_processor.process_resume(request.file_url)
        
        # Store in database
        resume_details = await supabase_service.insert_resume_details(
            resume_id=request.resume_id,
            skills=structured_data.get("skills", []),
            experience=structured_data.get("experience", []),
            education=structured_data.get("education", []),
            projects=structured_data.get("projects", [])
        )
        
        return ResumeAnalyzeResponse(
            success=True,
            message="Resume analyzed successfully",
            data=resume_details
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze resume: {str(e)}"
        )


@app.get("/api/resume/{resume_id}/details")
async def get_resume_details(resume_id: str, user_id: str):
    """
    Get parsed resume details for a specific resume
    """
    try:
        # Verify ownership
        is_owner = await supabase_service.verify_resume_ownership(resume_id, user_id)
        
        if not is_owner:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: You don't have permission to view this resume"
            )
        
        # Get resume with details
        resume_data = await supabase_service.get_resume_with_details(resume_id)
        
        if not resume_data:
            raise HTTPException(
                status_code=404,
                detail="Resume not found"
            )
        
        return resume_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get resume details: {str(e)}"
        )


@app.get("/api/user/{user_id}/resumes")
async def get_user_resumes(user_id: str):
    """
    Get all resumes for a specific user
    """
    try:
        resumes = await supabase_service.get_user_resumes(user_id)
        return {"resumes": resumes}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user resumes: {str(e)}"
        )


@app.delete("/api/resume/{resume_id}")
async def delete_resume(resume_id: str, user_id: str):
    """
    Delete a resume and its associated details
    """
    try:
        success = await supabase_service.delete_resume(resume_id, user_id)
        
        if success:
            return {"success": True, "message": "Resume deleted successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete resume"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete resume: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
