import google.generativeai as genai
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

def calculate_profile_score(profile_content: str, job_description: str, profile_data: Dict[str, Any]) -> tuple[int, str, str, str]:
    """Calculate profile score and analysis sections."""
    prompt = f"""
    As an expert recruiter, analyze this candidate's profile against the job requirements.
    Format your ENTIRE response using Markdown syntax.
    
    Job Requirements:
    {job_description}

    Complete Profile Content:
    {profile_content}

    Additional Info:
    - Name: {profile_data.get('intro', {}).get('name', 'N/A')}
    - Headline: {profile_data.get('intro', {}).get('headline', 'N/A')}

    Respond in exactly this format with Markdown:
    
    ### Match Score
    **Score:** [number between 0-100]
    
    ### Match Analysis
    [Detailed explanation of the match percentage]
    
    ### Qualifications Analysis
    
    #### Key Qualifications
    - [Bullet points of matching qualifications]
    
    #### Areas of Excellence
    - [Bullet points of strengths]
    
    #### Development Areas
    - [Bullet points of gaps]
    
    ### Personalized Message
    [Write outreach message]
    """
    
    response = model.generate_content(prompt)
    if not response or not response.text:
        raise Exception("Empty response from Gemini")
        
    text = response.text
    score = max(0, min(100, extract_score(text)))
    
    reasoning_section = text[text.find('### Match Analysis'):text.find('### Qualifications Analysis')]
    analysis_section = text[text.find('### Qualifications Analysis'):text.find('### Personalized Message')]
    message_section = text[text.find('### Personalized Message'):].replace('### Personalized Message', '').strip()
    
    return score, reasoning_section.strip(), analysis_section.strip(), message_section

def extract_score(text: str) -> int:
    """Helper function to extract score from text."""
    try:
        lines = text.split('\n')
        score_line = next((line for line in lines if '**Score:**' in line), '')
        digits = ''.join(filter(str.isdigit, score_line))
        return int(digits) if digits else 0
    except Exception:
        return 0

def generate_outreach_message(name: str, score: int, message_section: str) -> str:
    """Generate personalized outreach message."""
    return f"""
    Hi {name},
    
    Great news! Based on our analysis, your profile is an excellent match ({score}%) for the position.
    
    {message_section}
    
    Best regards,
    Recruitment Team
    """

def send_notifications(profile_data: Dict[str, Any], score: int, message_section: str) -> None:
    """Send email and SMS notifications for high-scoring candidates."""
    email = profile_data.get('email')
    phone = profile_data.get('phone')
    name = profile_data.get('name', 'Candidate')
    
    if score >= 90:
        notification_message = generate_outreach_message(name, score, message_section)
        
        # Log notification attempts
        print(f"Sending notifications for {name} (Score: {score})")
        
        if email:
            print(f"Would send email to: {email}")
            # Email sending functionality would be implemented here
            
        if phone:
            print(f"Would send SMS to: {phone}")
            # SMS sending functionality would be implemented here
