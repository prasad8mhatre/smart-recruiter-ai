import google.generativeai as genai
from typing import Dict, Any
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import pdb

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

def process_profile_data(profile_data: Any) -> Dict[str, Any]:
    """Convert profile data to proper format."""
    if isinstance(profile_data, str):
        return {
            'content': profile_data,
            'intro': {
                'name': 'Candidate',
                'headline': ''
            }
        }
    return profile_data

def calculate_profile_score(profile_content: str, job_description: str) -> tuple[int, str, str, str]:
    """Calculate profile score and analysis sections."""
    #pdb.set_trace()  # Debug: Score calculation start
    
    # Convert profile_data to proper format
    #formatted_profile = process_profile_data(profile_data)
    
    # Clean and truncate profile content
    if isinstance(profile_content, str):
        profile_content = BeautifulSoup(profile_content, 'html.parser').get_text()
        # Limit content length and clean up whitespace
        profile_content = ' '.join(profile_content.split())[:2000]
    
    prompt = f"""
    As an expert recruiter, analyze this candidate's profile against the job requirements.
    Format your ENTIRE response using Markdown syntax with EXACTLY these sections:
    
    Job Requirements:
    {job_description}

    Complete Profile Content:
    {profile_content}

    Respond with:
    
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
    #pdb.set_trace()  # Debug: After AI response
    
    if not response or not response.text:
        raise Exception("Empty response from Gemini")
        
    text = response.text
    score = max(0, min(100, extract_score(text)))
    
    # Extract sections more carefully
    sections = {
        'analysis': text[text.find('### Match Analysis'):text.find('### Qualifications Analysis')],
        'qualifications': text[text.find('### Qualifications Analysis'):text.find('### Personalized Message')],
        'message': text[text.find('### Personalized Message'):]
    }
    
    # Clean up section headers and whitespace
    cleaned_sections = {
        key: section.replace(f'### {key.title()}', '').strip()
        for key, section in sections.items()
    }
    
    return (
        score,
        cleaned_sections['analysis'],
        cleaned_sections['qualifications'],
        cleaned_sections['message'].replace('### Personalized Message', '').strip()
    )

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
    #pdb.set_trace()  # Debug: Message generation
    
    print(f"generated outreach message: {name}")
    return f"""
    Hi {name},
    
    Great news! Based on our analysis, your profile is an excellent match ({score}%) for the position.
    
    {message_section}
    
    Best regards,
    Recruitment Team
    """

def send_notifications(profile_data: str, score: int, message_section: str) -> bool:
    """Send email and SMS notifications for high-scoring candidates."""
    #pdb.set_trace()  # Debug: Notification sending
    
    print(f"Sent notifications for profile: {profile_data}")
    return True
