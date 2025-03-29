# Make sure to install dependencies first:
# pip install -r ../requirements.txt

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError("Please install google-generativeai: pip install google-generativeai")

from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, Any
import json
import os
import traceback
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from recruitment_utils import (
    calculate_profile_score,
    generate_outreach_message,
    send_notifications,
    model
)
from recruitment_agent import run_recruitment_agent

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def extract_score_from_text(text: str) -> tuple[int, str]:
    """Extract score and reasoning from Gemini output."""
    try:
        # Look specifically for the score line after Match Score header
        lines = text.split('\n')
        score_line = next((line for line in lines if '**Score:**' in line), '')
        if not score_line:
            print("Score line not found, using default")
            return 0, "Score not found in response"
            
        # Extract digits more carefully
        digits = ''.join(filter(str.isdigit, score_line))
        if not digits:
            print("No digits found in score line")
            return 0, "Invalid score format"
            
        score = int(digits)
        print(f"Extracted score: {score}")
        
        # Find reasoning section
        reasoning_start = text.find('### Match Analysis')
        reasoning_end = text.find('### Qualifications Analysis')
        if reasoning_start != -1 and reasoning_end != -1:
            reasoning = text[reasoning_start:reasoning_end].replace('### Match Analysis', '').strip()
        else:
            reasoning = "Reasoning section not found"
            
        return score, reasoning

    except Exception as e:
        print(f"Error in score extraction: {e}")
        return 0, f"Error extracting score: {str(e)}"

def extract_from_raw_html(html: str) -> Dict[str, str]:
    """Extract profile data from raw HTML if structured extraction fails."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        name_element = soup.select_one('h1')
        headline_element = soup.select_one('div.text-body-medium')
        summary_element = soup.select_one('#about ~ div .pv-shared-text-with-see-more')
        
        return {
            'name': name_element.text.strip() if name_element else '',
            'headline': headline_element.text.strip() if headline_element else '',
            'summary': summary_element.text.strip() if summary_element else '',
            'experience': '\n'.join([e.text.strip() for e in soup.select('#experience ~ div .pvs-entity') or []]),
            'education': '\n'.join([e.text.strip() for e in soup.select('#education ~ div .pvs-entity') or []]),
            'skills': ', '.join([s.text.strip() for s in soup.select('#skills ~ div .pvs-entity .t-bold span') or []])
        }
    except Exception as e:
        print(f"Error parsing raw HTML: {e}")
        return {}

def analyze_profile(profile_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """Analyze profile data against job description using agent."""
    try:
        print("Received profile data:", json.dumps(profile_data, indent=2))
        
        # Use the recruitment agent to analyze the profile
        result = run_recruitment_agent(profile_data, job_description)
        
        return result

    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'matchScore': 0,
            'scoreReasoning': "Analysis failed",
            'analysis': "",
            'message': ""
        }

def extract_skills(text: str) -> list[str]:
    """Extract skills from text."""
    # Implement skill extraction logic
    return []

def extract_years_required(text: str) -> int:
    """Extract required years of experience."""
    # Implement years extraction logic
    return 0

def extract_years_from_experience(text: str) -> int:
    """Extract years from experience text."""
    # Implement experience years extraction logic
    return 0

@app.route('/analyze', methods=['POST'])
def analyze_profile_endpoint():
    try:
        data = request.json
        if not data or 'profile' not in data or 'jobDescription' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        analysis_result = analyze_profile(data['profile'], data['jobDescription'])
        
        return jsonify(analysis_result)
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Analysis failed',
            'details': str(e)
        }), 500

def update_sheet(profile, analysis, message):
    # Google Sheets integration code
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID')
    
    creds = Credentials.from_authorized_user_file('credentials.json', SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    
    values = [[profile, analysis, message]]
    body = {'values': values}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT', 5000)))
