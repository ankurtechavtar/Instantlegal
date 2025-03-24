import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
import time

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default-secret-key")

# Configure CORS
CORS(app)

# Configure OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    app.logger.warning("OpenAI API key not set. Document generation will not work.")

# Initialize OpenAI client with no proxy configuration
client = OpenAI(api_key=OPENAI_API_KEY)

# Ensure the uploads directory exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "documents")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure the downloads directory exists
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "static", "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Document types and their descriptions
DOCUMENT_TYPES = {
    "nda": "Non-Disclosure Agreement (NDA)",
    "terms": "Website Terms of Service",
    "privacy": "Privacy Policy",
    "contract": "Freelance Contract",
    "employee": "Employment Agreement",
    "partnership": "Partnership Agreement"
}

@app.route('/')
def index():
    return render_template('index.html', document_types=DOCUMENT_TYPES)


# @app.route('/generate-document', methods=['POST'])
# def handle_document_generation():
#     try:
#         return generate_document(request.form)
#     except Exception as e:
#         app.logger.error(f"Error generating document: {str(e)}")
#         return jsonify({'error': f'Failed to generate document: {str(e)}'}), 500

from flask import redirect, url_for

@app.route('/generate-document', methods=['POST'])
def handle_document_generation():
    try:
        # Generate the document and get the download URL
        result = generate_document(request.form)

        # Redirect to the success page with a success message and download link
        return redirect(url_for('download_success', filename=result['download_url'][9:], message="Your document has been generated successfully!"))
    except Exception as e:
        app.logger.error(f"Error generating document: {str(e)}")
        return jsonify({'error': f'Failed to generate document: {str(e)}'}), 500

@app.route('/download-success/<filename>/<message>')
def download_success(filename, message):
    return render_template('download_success.html', filename=filename, message=message)

def generate_document(form_data):
    try:
        # Extract form data
        document_type = form_data.get('document_type')
        business_name = form_data.get('business_name')
        business_type = form_data.get('business_type')
        state = form_data.get('state')
        industry = form_data.get('industry')
        protection_level = form_data.get('protection_level', '2')
        
        # Special clauses
        clauses = []
        if form_data.get('clause_confidentiality'):
            clauses.append("Enhanced Confidentiality")
        if form_data.get('clause_arbitration'):
            clauses.append("Arbitration Provision")
        if form_data.get('clause_termination'):
            clauses.append("Advanced Termination Options")
        if form_data.get('clause_ip'):
            clauses.append("Intellectual Property Protection")
        
        additional_instructions = form_data.get('additional_instructions', '')
        
        # Create prompt for OpenAI
        prompt = f"""Generate a professional {DOCUMENT_TYPES.get(document_type, 'legal document')} for {business_name}, a {business_type} in the {industry} industry, operating in {state}.

Protection Level: {protection_level} out of 3

Special Clauses to Include: {', '.join(clauses) if clauses else 'None'}

Additional Instructions: {additional_instructions}

**Formatting Guidelines:**
- Use clear section headings in bold and all caps (e.g., **TERMS AND CONDITIONS**).
- Use proper indentation and line spacing for readability.
- Ensure signature fields are properly spaced and formatted as follows:

  **Signature:** ______________________  **Date:** _______________

- Use bullet points for lists where appropriate.
- Avoid overly dense paragraphs; break them up into short, digestible sections.
- Use legal language but ensure clarity for business professionals.

Format the document professionally with appropriate sections, headings, and legal language. Include all necessary legal provisions for this type of document in {state}.
"""

        # Call OpenAI API with retry logic
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use a more reliable model
                    messages=[
                        {"role": "system", "content": "You are a legal document generator that creates professional, legally-sound documents tailored to specific business needs and jurisdictions."},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=30,  # Shorter timeout to avoid worker timeouts
                    max_tokens=4000  # Limit token count to speed up generation
                )
                
                # Extract generated text
                document_text = response.choices[0].message.content
                break  # Success, exit the retry loop
                
            except Exception as e:
                app.logger.error(f"OpenAI API error (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    # Not the last attempt, wait and retry
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Last attempt failed, raise the exception
                    app.logger.error(f"All {max_retries} attempts to call OpenAI API failed")
                    raise Exception(f"Failed to generate document after {max_retries} attempts: {str(e)}")
        
        # Generate a unique filename
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{document_type}_{unique_id}.pdf"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create PDF
        create_pdf(document_text, filepath, business_name, DOCUMENT_TYPES.get(document_type, "Legal Document"))
        
        # Return success response
        return {
            'success': True,
            'download_url': f'/download/{filename}'
        }
    
    except Exception as e:
        app.logger.error(f"OpenAI API error: {str(e)}")
        raise Exception(f"Failed to generate document: {str(e)}")

def create_pdf(text, filepath, business_name, document_type):
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.navy,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        firstLineIndent=20,
        leading=14,
        spaceBefore=6,
        spaceAfter=6
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=13,
        spaceAfter=10,
        spaceBefore=15,
        textColor=colors.navy,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.lightgrey,
        borderPadding=5,
        borderRadius=2
    )
    
    # Build document content
    content = []
    
    # Add title
    content.append(Paragraph(f"{document_type.upper()}", title_style))
    content.append(Paragraph(f"For: {business_name}", title_style))
    content.append(Spacer(1, 20))
    
    # Add date with better formatting
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_RIGHT,
        textColor=colors.darkgrey
    )
    content.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", date_style))
    content.append(Spacer(1, 20))
    
    # Process the text into paragraphs
    paragraphs = text.split('\n')
    for para in paragraphs:
        if para.strip():
            # Handle markdown-style headers (# Header)
            if para.strip().startswith('#'):
                header_text = para.replace('#', '').strip()
                content.append(Paragraph(header_text, header_style))
            # Handle all-caps headers (HEADER)
            elif para.strip().isupper() and len(para.strip()) > 3:
                content.append(Paragraph(para.strip(), header_style))
            # Handle bullet points
            elif para.strip().startswith('•') or para.strip().startswith('-') or para.strip().startswith('*'):
                bullet_style = ParagraphStyle(
                    'Bullet',
                    parent=normal_style,
                    leftIndent=30,
                    firstLineIndent=0,
                    spaceBefore=3,
                    spaceAfter=3
                )
                content.append(Paragraph(para.strip(), bullet_style))
            # Handle signature lines
            elif "signature" in para.lower() or "sign" in para.lower() or "date:" in para.lower():
                sig_style = ParagraphStyle(
                    'Signature',
                    parent=normal_style,
                    spaceBefore=15,
                    spaceAfter=15
                )
                content.append(Paragraph(para, sig_style))
            # Regular paragraph
            else:
                content.append(Paragraph(para, normal_style))
            
            # Add appropriate spacing
            if para.strip().startswith('#') or para.strip().isupper():
                content.append(Spacer(1, 10))
            else:
                content.append(Spacer(1, 6))
    
    # Build the PDF
    doc.build(content)

# @app.route('/download/<filename>')
# def download_file(filename):
#     return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

from flask import Response

@app.route('/download/<filename>')
def download_file(filename):
    try:
        # Create the file path
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # Send the file with a Content-Disposition header to trigger the download
        return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True, download_name=filename)
    except Exception as e:
        app.logger.error(f"Error sending file: {str(e)}")
        return jsonify({'error': 'Failed to download file.'}), 500

# Route to serve favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
