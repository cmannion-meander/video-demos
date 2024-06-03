import openai
import os
import requests
import pickle
import string
import time
from jobtracker.models import Company, Job, Role, Location
from bs4 import BeautifulSoup
from fuzzywuzzy import process
import spacy

# Load SpaCy model for natural language processing
nlp = spacy.load("en_core_web_sm")

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to check if a URL is active
def is_url_active(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Function to clean text by removing punctuation and converting to lowercase
def clean_text(text):
    return ''.join([char for char in text if char not in string.punctuation]).lower()

# Load the model and vectorizer
with open('finalized_model.pkl', 'rb') as model_file:
    loaded_model = pickle.load(model_file)

with open('finalized_vectorizer.pkl', 'rb') as vectorizer_file:
    loaded_vectorizer = pickle.load(vectorizer_file)

# Function to find the best matching role for a given job title
def find_best_matching_role(job_title, roles):
    roles_dict = {role.title: role.id for role in roles}
    clean_job_title = clean_text(job_title)
    vectorized_title = loaded_vectorizer.transform([clean_job_title])
    predicted_role_title = loaded_model.predict(vectorized_title)[0]
    return roles_dict.get(predicted_role_title)

# Function to fetch the content of a job page
def fetch_job_page(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except requests.RequestException:
        return None

# Function to extract text from HTML content
def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    texts = soup.stripped_strings
    combined_text = " ".join(texts)[:1000]
    return combined_text

# Function to match location data with a list of cities
def match_location(location_data, cities_list, location_qs):
    if location_data.lower() == "remote":
        location, created = Location.objects.get_or_create(
            city="Remote", defaults={'state': "", 'country': ""}
        )
        return location
    
    best_match, match_score = process.extractOne(location_data, cities_list)
    MATCH_THRESHOLD = 80
    
    if match_score >= MATCH_THRESHOLD:
        location = location_qs.get(city=best_match)
    else:
        location, created = Location.objects.get_or_create(
            city="Other", defaults={'state': "", 'country': ""}
        )

    return location

# Function to extract location using GPT-3
def extract_location_with_gpt(text, cities_list):
    prompt = f"""
    Identify the closest city references in the text provided. If the location is listed as remote, return "remote". If the location is on the following list, or close to one of those cities, return that city. All other values should return "Other". Return only the city name.

    List of cities:
    {', '.join(cities_list)}

    Text to analyze:
    "{text}"
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an AI specializing in geolocation."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    location_str = response.choices[0].message['content'].strip()
    return location_str

# Function to process each job for location extraction
def process_job_for_location(job):
    html_content = fetch_job_page(job.external_posting_url)
    if html_content:
        text = extract_text_from_html(html_content)
        location_qs = Location.objects.all()
        cities_list = location_qs.values_list('city', flat=True)
        location_str = extract_location_with_gpt(text, cities_list)
        job_location = match_location(location_str, cities_list, location_qs)
        
        try:
            job.job_location = job_location
            job.save()
        except:
            pass

# Initialize counters
inactive_count = 0
misclassified_count = 0

# Function to process each job for inactivity and role misclassification
def process_job(job, roles):
    global inactive_count
    global misclassified_count

    if job.external_posting_url and not is_url_active(job.external_posting_url):
        job.is_active = False
        job.save()
        inactive_count += 1
        print(f'Found {inactive_count} inactive jobs so far.')
        return

    if job.role and job.role.title == "Other":
        job.is_active = False
        job.save()

# Get all roles and companies
roles = Role.objects.all()
companies = Company.objects.all()

# Process each company and their active jobs
for company in companies:
    jobs = Job.objects.filter(company=company, is_active=True)
    for job in jobs:
        process_job_for_location(job)
    print(f'Completed QA for {company.name}.')
    time.sleep(5)

print(f'Total Jobs Removed: {inactive_count}')
print(f'Total Jobs Reclassified: {misclassified_count}')