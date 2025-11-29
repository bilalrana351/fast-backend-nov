from typing import Literal
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import json
import logging
import os
from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import Request
from supabase import create_client, Client

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class CallReport(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    passed: bool
    call_type: Literal["technical", "behavioural"]

@router.post("/api/end-of-call-report")
async def get_transcript(request: Request):
    body = await request.json()

    # Extract call_id
    call_id = body.get("message", {}).get("call", {}).get("id")
    if call_id:
        try:
            existing = supabase.table("call_reports").select("id").eq("id", call_id).execute()
            if existing.data:
                print(f"Call report already exists for ID: {call_id}")
                return {"status": "exists", "message": "Report already exists", "call_id": call_id}
        except Exception as e:
            print(f"Error checking for existing call report: {e}")

    transcript = body.get("message", {}).get("artifact", {}).get("transcript", "")
    

    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are an expert interviewer. Analyze the following interview transcript and provide a structured report containing the candidate's strengths, weaknesses, whether they passed, "
                    f'and the call_type of interview ("technical" or "behavioural"). The "call_type" field must be exactly one of: "technical", "behavioural". Infer this from the call transcript. Have about 5 strengths and about 5 weaknesses.'
                )
            },
            {
                "role": "user",
                "content": transcript,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "call_report",
                "schema": CallReport.model_json_schema()
            }
        }
    )
    
    analysis = json.loads(response.choices[0].message.content)
    
    # Extract variables safely
    message = body.get("message", {})
    call = message.get("call", {})
    assistant = message.get("assistant", {})
    
    call_overrides = call.get("assistantOverrides") or {}
    call_vars = call_overrides.get("variableValues") or {}
    assistant_vars = assistant.get("variableValues") or {}
    
    # Get user_id with fallback
    user_id = call_vars.get("user_id") or assistant_vars.get("user_id")
    
    # Get call_type with fallback
    call_type_override = call_vars.get("call_type") or assistant_vars.get("call_type")
        
    if call_type_override:
        print(f"Overriding call_type with: {call_type_override}")
        analysis["call_type"] = call_type_override
        
    print("Analysis:", analysis)
    print(f"Extracted user_id: {user_id}")

    if user_id:
        try:
            data = {
                "id": call_id,
                "user_id": user_id,
                "strengths": analysis.get("strengths", []),
                "weaknesses": analysis.get("weaknesses", []),
                "passed": analysis.get("passed", False),
                "call_type": analysis.get("call_type", "technical")
            }
            supabase.table("call_reports").insert(data).execute()
            print("Stored call report in Supabase")
        except Exception as e:
            print(f"Error storing call report: {e}")
    else:
        print("No user_id found, skipping Supabase storage")

    return {"received_body": body, "transcript": transcript, "analysis": analysis}

@router.get("/api/call-report/{call_id}")
async def get_call_report(call_id: str):
    try:
        result = supabase.table("call_reports").select("*").eq("id", call_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Call report not found")
        return result.data[0]
    except Exception as e:
        print(f"Error fetching call report: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching call report: {str(e)}")
