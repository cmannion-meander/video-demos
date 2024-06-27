import fitz  # Import PyMuPDF
import json
import logging
from openai import OpenAI
import os
import re
from helpers import parse_resume, match_keywords, filter_candidates
from flask import Flask, request, render_template
import serpapi

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Initialize the OpenAI client with the API key from environment variable
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Initialize SERP API client with the API key from environment variable
SERP_API_KEY = os.environ.get("SERP_API_KEY")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def form():
    return render_template('form.html')

## Resume parsing functionality
@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume_file' not in request.files:
        return "No file part", 400
    file = request.files['resume_file']
    if file.filename == '':
        return "No selected file", 400
    
    # Assuming the file is a PDF
    if file and allowed_file(file.filename):
        text = extract_text_from_pdf(file)
        parsed_resume_json_string = parse_resume_with_gpt(text)
        parsed_resume = json.loads(parsed_resume_json_string)
        formatted_resume_text = f"Name: {parsed_resume['name']}\nContact: {parsed_resume['contact']}\nOrganizations: {', '.join(parsed_resume['organizations'])}"
        print(parsed_resume)
        # Perform search using the parsed name and other identifying features
        search_results = search_candidate(parsed_resume['name'], parsed_resume['organizations'])
    return render_template('form_resume.html', resume_text=formatted_resume_text, parsed_resume=json.dumps(parsed_resume), search_results=search_results)


@app.route('/create_profile', methods=['POST'])
def create_profile():
    try:
        parsed_resume = request.form['parsed_resume']
        parsed_resume = json.loads(parsed_resume)
        name = parsed_resume['name']
        logging.debug(f"Parsed Resume: {parsed_resume}")
        
        # Perform search using the parsed name and other identifying features
        search_results = search_candidate(parsed_resume['name'], parsed_resume['organizations'])
        logging.debug(f"Search Results: {search_results}")
        
        # Use the snippets from the search results
        snippets = [result['snippet'] for result in search_results]
        logging.debug(f"Snippets: {snippets}")
        
        # Analyze the text using the DISC / OCEAN framework
        analysis = analyze_text(snippets)
        logging.debug(f"Analysis: {analysis}")
        
        # Generate a narrative
        narrative = generate_narrative(analysis)
        logging.debug(f"Narrative: {narrative}")
        
        # Create a final profile based on the narrative
        final_profile = create_final_profile(narrative, name)
        logging.debug(f"Final Profile: {final_profile}")
        
        return render_template('profile.html', analysis=analysis, narrative=narrative, final_profile=final_profile, name=name)
    except Exception as e:
        logging.error(f"Error in create_profile function: {e}")
        return f"An error occurred: {e}"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx'}

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_resume_with_gpt(resume_text):
    # Construct the prompt with the provided resume text
    prompt = f'''
        Act as an advanced AI capable of parsing resume texts to extract key information including name, skills, and experience. Your task is to analyze the given resume text, identify the name, skills, and experience mentioned, and then output this information in a structured JSON format. You will only output the JSON data.

        Given the resume text, output the extracted name, skills, and experience in JSON format like this:
        {{
        "name": "Candidate Name",
        "contact": "The email address would normally go here, but return omitted for privacy reasons.",
        "organizations": ["List", "Of", "Current", "Prior", "Organizations", "Here"],
        }}

        Parse the following resume text into the required JSON format:
        {resume_text}
        '''
    
    # Make the API call
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a highly intelligent AI skilled in parsing and structuring resume information."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    try:
        # Assuming the output is JSON formatted as expected, directly return the result
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return {}

def search_candidate(name, organizations):
    social_media_sites = ["LinkedIn", "Twitter", "Facebook"]
    search_results = []

    for organization in organizations[:3]:
        for site in social_media_sites:
            search_query = f"{name} {organization} site:{site.lower()}.com"
            params = {
                "q": search_query,
                "api_key": SERP_API_KEY
            }
            search = serpapi.search(params)
            try:
                results = search["organic_results"]
                search_results.extend(results)
            except:
                print(search)

    return search_results

def analyze_text(snippets):
    combined_text = " ".join(snippets)
    prompt = f'''
        Act as an AI skilled in psychological analysis. Analyze the following text using the DISC and OCEAN personality frameworks and provide a structured analysis.

        Text:
        {combined_text}
        '''
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a highly intelligent AI skilled in psychological analysis."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    
    try:
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error analyzing text: {e}")
        return {}

def generate_narrative(analysis):
    prompt = f'''
        Based on the following DISC and OCEAN personality analysis, create a narrative that summarizes the candidate's personality and professional behavior.

        Analysis:
        {analysis}
        '''
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a highly intelligent AI skilled in creating narratives."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    
    try:
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating narrative: {e}")
        return {}

def create_final_profile(narrative, name):
    prompt = f'''
        Create a final candidate profile for this candidate named {name} to be presented to a hiring manager who is focused on cultural fit based on the following narrative:

        Narrative:
        {narrative}
        '''
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a highly intelligent AI skilled in creating candidate profiles."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    
    try:
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error creating final profile: {e}")
        return {}

if __name__ == '__main__':
    app.run(debug=True)