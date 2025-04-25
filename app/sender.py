import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from datetime import datetime
from jinja2 import Template
from dotenv import load_dotenv

load_dotenv()

def format_summaries(summaries):
    """Format summaries into urgent and important categories"""
    urgent = []
    important = []
    
    for summary in summaries:
        lines = summary.split('\n')
        importance = next((line for line in lines if '⭐ Importance:' in line), '')
        
        # Extract importance level
        importance_level = int(importance.split(':')[1].strip()[0])
        
        # Format the summary with metadata and styling
        formatted_summary = f"""
        <div class='metadata'>
            <span class='importance-{importance_level}'>
                {lines[0]}  <!-- Importance -->
            </span>
        </div>
        <div class='content'>
            {lines[1]}  <!-- Summary -->
        </div>
        <div class='details'>
            {lines[2] if len(lines) > 2 else ''}  <!-- Action Items -->
            {lines[3] if len(lines) > 3 else ''}  <!-- Deadlines -->
            {lines[4] if len(lines) > 4 else ''}  <!-- Response -->
        </div>
        """
        
        if importance_level == 1:
            urgent.append(formatted_summary)
        elif importance_level == 2:
            important.append(formatted_summary)
    
    return urgent, important

def send_digest(summaries, recipient_email=None):
    """Send the digest email with HTML formatting"""
    if recipient_email is None:
        recipient_email = os.getenv("EMAIL_USER")
    
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Daily Email Digest - {datetime.now().strftime("%Y-%m-%d")}'
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    # Read HTML template
    with open('app/templates/email_template.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())
    
    # Format summaries
    urgent_summaries, important_summaries = format_summaries(summaries)
    
    # Render HTML
    html = template.render(
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        emails_processed=len(summaries),
        important_emails=len(urgent_summaries) + len(important_summaries),
        urgent_summaries=urgent_summaries,
        important_summaries=important_summaries
    )
    
    # Attach HTML content
    msg.attach(MIMEText(html, 'html'))
    
    # Send email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
