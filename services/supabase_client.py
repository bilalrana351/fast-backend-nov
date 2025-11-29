from supabase import create_client, Client
from typing import Dict, Any, Optional, List
from datetime import datetime


class SupabaseService:
    """Service for interacting with Supabase database"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)
    
    async def insert_resume_details(
        self, 
        resume_id: str, 
        skills: List[str],
        experience: List[Dict[str, Any]],
        education: List[Dict[str, Any]],
        projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Insert parsed resume details into the resume_details table
        
        Args:
            resume_id: UUID of the resume record
            skills: List of skill strings
            experience: List of experience dictionaries
            education: List of education dictionaries
            projects: List of project dictionaries
        
        Returns:
            Dictionary with the inserted record
        """
        try:
            data = {
                "resume_id": resume_id,
                "skills": skills,
                "experience": experience,
                "education": education,
                "projects": projects,
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            # Check if record already exists
            existing = self.client.table("resume_details").select("*").eq("resume_id", resume_id).execute()
            
            if existing.data and len(existing.data) > 0:
                # Update existing record
                result = self.client.table("resume_details").update(data).eq("resume_id", resume_id).execute()
            else:
                # Insert new record
                result = self.client.table("resume_details").insert(data).execute()
            
            return result.data[0] if result.data else {}
            
        except Exception as e:
            raise Exception(f"Failed to insert resume details: {str(e)}")
    
    async def get_resume_details(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve parsed resume details by resume_id
        
        Args:
            resume_id: UUID of the resume record
        
        Returns:
            Dictionary with resume details or None if not found
        """
        try:
            result = self.client.table("resume_details").select("*").eq("resume_id", resume_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Failed to get resume details: {str(e)}")
    
    async def get_user_resumes(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all resumes for a specific user
        
        Args:
            user_id: UUID of the user
        
        Returns:
            List of resume records
        """
        try:
            result = self.client.table("resumes").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            raise Exception(f"Failed to get user resumes: {str(e)}")
    
    async def get_resume_with_details(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """
        Get resume record along with its parsed details
        
        Args:
            resume_id: UUID of the resume record
        
        Returns:
            Dictionary with resume and its details combined
        """
        try:
            # Get resume record
            resume_result = self.client.table("resumes").select("*").eq("id", resume_id).execute()
            if not resume_result.data:
                return None
            
            resume = resume_result.data[0]
            
            # Get resume details
            details_result = self.client.table("resume_details").select("*").eq("resume_id", resume_id).execute()
            
            if details_result.data:
                resume["details"] = details_result.data[0]
            else:
                resume["details"] = None
            
            return resume
            
        except Exception as e:
            raise Exception(f"Failed to get resume with details: {str(e)}")
    
    async def delete_resume(self, resume_id: str, user_id: str) -> bool:
        """
        Delete a resume and its associated details
        
        Args:
            resume_id: UUID of the resume record
            user_id: UUID of the user (for authorization check)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # First verify the resume belongs to the user
            resume = self.client.table("resumes").select("user_id").eq("id", resume_id).execute()
            
            if not resume.data or resume.data[0]["user_id"] != user_id:
                raise Exception("Unauthorized: Resume does not belong to user")
            
            # Delete resume details (will cascade due to foreign key)
            self.client.table("resume_details").delete().eq("resume_id", resume_id).execute()
            
            # Delete resume record
            self.client.table("resumes").delete().eq("id", resume_id).execute()
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to delete resume: {str(e)}")
    
    async def verify_resume_ownership(self, resume_id: str, user_id: str) -> bool:
        """
        Verify that a resume belongs to a specific user
        
        Args:
            resume_id: UUID of the resume record
            user_id: UUID of the user
        
        Returns:
            True if the resume belongs to the user, False otherwise
        """
        try:
            result = self.client.table("resumes").select("user_id").eq("id", resume_id).execute()
            
            if not result.data:
                return False
            
            return result.data[0]["user_id"] == user_id
            
        except Exception as e:
            return False

