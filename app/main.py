from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json, os
from .gmail_service import gmail_build, send_email_summary
from .ranker import summarize
import traceback

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailResponse(BaseModel):
    subject: str
    from_: str
    summary: str
    error: Optional[str] = None

@app.get("/")
async def root():
    return {"status": "Email Analysis Service is running"}

@app.post("/run")
async def run_analysis():
    try:
        # Get Gmail service
        service = gmail_build()
        if not service:
            raise HTTPException(status_code=500, detail="Failed to initialize Gmail service")

        # Get messages
        results = service.users().messages().list(userId='me', maxResults=10).execute()
        messages = results.get('messages', [])

        if not messages:
            return {"message": "No emails found", "summaries": []}

        summaries = []
        user_email = None  # Store user's email

        for msg in messages:
            try:
                # Get full message details
                full_msg = service.users().messages().get(userId='me', id=msg['id']).execute()
                
                # Get headers
                headers = full_msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                from_ = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
                
                # Get the user's email from the 'to' field of any message
                if not user_email:
                    user_email = next((h['value'] for h in headers if h['name'].lower() == 'to'), None)
                    if user_email and '<' in user_email:
                        user_email = user_email[user_email.find('<')+1:user_email.find('>')]
                
                # Get summary
                summary = summarize(full_msg)
                
                summary_obj = EmailResponse(
                    subject=subject,
                    from_=from_,
                    summary=summary
                )
                summaries.append(summary_obj)
                
            except Exception as e:
                # Log the error but continue processing other emails
                summaries.append(EmailResponse(
                    subject="Error Processing Email",
                    from_="System",
                    summary="Failed to process this email",
                    error=str(e)
                ))

        # Convert summaries to dict for email sending
        summary_dicts = [s.dict() for s in summaries]
        
        # If we don't have user_email from messages, try to get it from environment
        if not user_email:
            user_email = os.getenv('USER_EMAIL')  # Make sure to set this in your .env file
        
        # Send email summary if we have the user's email
        if user_email:
            send_success = send_email_summary(service, user_email, summary_dicts)
            return {
                "message": f"Analysis complete and summary sent to {user_email}" if send_success else "Analysis complete but failed to send email",
                "summaries": summary_dicts,
                "email_sent": send_success,
                "sent_to": user_email
            }
        else:
            return {
                "message": "Analysis complete but couldn't determine email address to send to",
                "summaries": summary_dicts,
                "email_sent": False
            }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
