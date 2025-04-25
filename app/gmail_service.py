from __future__ import print_function
import base64, os, datetime as dt
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import html
load_dotenv()

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def gmail_build():
    """Build Gmail API service with proper authentication."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def create_html_summary(summaries):
    """Create a beautiful HTML email with all summaries"""
    html_content = """
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                line-height: 1.6; 
                color: #2c3e50; 
                background-color: #f5f6fa;
                margin: 0;
                padding: 0;
            }
            .email-container { 
                max-width: 800px; 
                margin: 20px auto; 
                padding: 20px;
                background: white;
                box-shadow: 0 2px 15px rgba(0,0,0,0.1);
                border-radius: 12px;
            }
            .summary-box { 
                border: 1px solid #e1e8ed; 
                border-radius: 12px; 
                padding: 20px; 
                margin-bottom: 25px;
                background: white;
                transition: all 0.3s ease;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                position: relative;
                overflow: hidden;
            }
            .summary-box:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .header { 
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                color: white; 
                padding: 25px;
                border-radius: 12px;
                margin-bottom: 30px;
                text-align: center;
            }
            .header h2 {
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }
            .header p {
                margin: 10px 0 0 0;
                opacity: 0.9;
            }
            .section { 
                margin: 15px 0;
                line-height: 1.8;
            }
            .importance { 
                font-size: 1.2em; 
                color: #e67e22;
                font-weight: 600;
            }
            .divider { 
                border-top: 1px solid #edf2f7;
                margin: 15px 0;
            }
            .priority-badge {
                display: inline-block;
                padding: 5px 12px;
                border-radius: 15px;
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 10px;
            }
            .priority-1 { background: #ff4757; color: white; }
            .priority-2 { background: #ffa502; color: white; }
            .priority-3 { background: #2ed573; color: white; }
            .priority-4 { background: #747d8c; color: white; }
            .priority-5 { background: #a4b0be; color: white; }
            .category-tag {
                display: inline-block;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 12px;
                background: #f1f2f6;
                color: #2f3542;
                margin-right: 5px;
                margin-top: 5px;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #edf2f7;
                color: #a4b0be;
                font-size: 14px;
            }
            .email-link {
                color: #2c3e50;
                text-decoration: none;
                transition: color 0.2s ease;
                display: block;
            }
            .email-link:hover {
                color: #3498db;
            }
            .view-original {
                position: absolute;
                top: 20px;
                right: 20px;
                background: #f8f9fa;
                padding: 8px 15px;
                border-radius: 20px;
                color: #2c3e50;
                text-decoration: none;
                font-size: 13px;
                transition: all 0.2s ease;
                border: 1px solid #e1e8ed;
            }
            .view-original:hover {
                background: #3498db;
                color: white;
                border-color: #3498db;
            }
            .view-original i {
                margin-left: 5px;
            }
            .metadata {
                color: #7f8c8d;
                font-size: 14px;
                margin: 10px 0;
            }
            .action-required {
                background: #fff3cd;
                border-left: 4px solid #ffa502;
                padding: 10px 15px;
                margin: 10px 0;
                border-radius: 4px;
            }
            .deadline {
                background: #f8d7da;
                border-left: 4px solid #ff4757;
                padding: 10px 15px;
                margin: 10px 0;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h2>📧 Günlük E-posta Özetiniz</h2>
                <p>""" + dt.datetime.now().strftime("%d.%m.%Y %H:%M") + """ tarihinde oluşturuldu</p>
            </div>
    """
    
    priority_names = {
        "1": "Acil",
        "2": "Yüksek Öncelik",
        "3": "Normal",
        "4": "Düşük Öncelik",
        "5": "Bilgi"
    }
    
    for summary in summaries:
        # Convert the summary text to HTML-safe format and preserve line breaks
        formatted_summary = html.escape(summary['summary']).replace('\n', '<br>')
        
        # Extract priority number from the summary
        priority = "3"  # default priority
        if "Priority:" in formatted_summary:
            priority = formatted_summary.split("Priority:")[1].strip()[0]
        
        # Extract category if available
        category = "Genel"
        if "Category:" in formatted_summary:
            category = formatted_summary.split("Category:")[1].split("<br>")[0].strip()
            
        # Extract action and deadline
        action = None
        if "Action Required:" in formatted_summary:
            action = formatted_summary.split("Action Required:")[1].split("<br>")[0].strip()
            
        deadline = None
        if "Deadline:" in formatted_summary:
            deadline = formatted_summary.split("Deadline:")[1].split("<br>")[0].strip()
        
        # Create Gmail link
        gmail_link = f"https://mail.google.com/mail/u/0/#search/{html.escape(summary['subject'].replace(' ', '%20'))}"
        
        html_content += f"""
            <div class="summary-box">
                <div class="priority-badge priority-{priority}">
                    ⭐ {priority_names[priority]}
                </div>
                <a href="{gmail_link}" target="_blank" class="email-link">
                    <h3 style="margin: 10px 0;">📌 {html.escape(summary['subject'])}</h3>
                </a>
                <a href="{gmail_link}" target="_blank" class="view-original">
                    Orijinal E-postayı Aç ↗
                </a>
                <div class="metadata">
                    <strong>Gönderen:</strong> {html.escape(summary['from_'])}
                </div>
                <div class="divider"></div>
                <div class="section">
                    {formatted_summary}
                </div>
                {f'<div class="action-required">✅ Yapılması Gereken: {action}</div>' if action and action.lower() != "no action needed" else ''}
                {f'<div class="deadline">⏰ Son Tarih: {deadline}</div>' if deadline and deadline.lower() != "no deadline" else ''}
                <div style="margin-top: 15px;">
                    <span class="category-tag">📑 {category}</span>
                </div>
            </div>
        """
    
    html_content += """
            <div class="footer">
                <p>Bu özet e-postası otomatik olarak oluşturulmuştur.</p>
                <p>© 2025 Email Özet Sistemi</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def send_email_summary(service, to_email, summaries):
    """Send email summary with beautiful formatting"""
    message = MIMEMultipart('alternative')
    message['to'] = to_email
    message['subject'] = f"📋 Günlük E-posta Özetiniz - {dt.datetime.now().strftime('%d.%m.%Y')}"
    
    # Create HTML content
    html_content = create_html_summary(summaries)
    
    # Attach HTML part
    html_part = MIMEText(html_content, 'html', 'utf-8')
    message.attach(html_part)
    
    # Encode the message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    try:
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def fetch_today_threads(max_results=100):
    service = gmail_build()
    today = dt.datetime.utcnow().strftime("%Y/%m/%d")
    query = f"after:{today}"
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    msgs = results.get("messages", [])
    full_msgs = []
    for m in msgs:
        data = (
            service.users()
            .messages()
            .get(userId="me", id=m["id"], format="full")
            .execute()
        )
        full_msgs.append(data)
    return full_msgs

def get_header(headers, name):
    """Get a specific header value from email headers."""
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ''
