from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def build_pdf(summaries):
    """Build a PDF report from email summaries."""
    filename = f"email_digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles only if they don't exist
    if 'CustomHeading1' not in styles:
        styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        ))
    
    if 'CustomNormal' not in styles:
        styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12
        ))
    
    # Build the document
    story = []
    
    # Add title
    title = Paragraph(
        f"Email Digest Report - {datetime.now().strftime('%Y-%m-%d')}",
        styles['CustomHeading1']
    )
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Add each summary
    for summary in summaries:
        p = Paragraph(summary.replace('\n', '<br/>'), styles['CustomNormal'])
        story.append(p)
        story.append(Spacer(1, 12))
    
    # Generate PDF
    doc.build(story)
    return filename
