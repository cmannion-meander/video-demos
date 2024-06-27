### Parameters:
threshold_score = 5

### Sample resume_text:
"""
Name: John Doe
Skills: Python, Machine Learning, Data Analysis, SQL
Experience: 5 years
"""

def parse_resume(resume_text):
    """
    Parses the resume text and extracts name, skills, and experience.
    """
    lines = resume_text.strip().split('\n')
    resume_data = {}
    for line in lines:
        key, value = line.split(': ')
        resume_data[key.lower()] = value.strip()
    return resume_data

def match_keywords(parsed_resume, required_skills):
    """
    Searches the candidate's skills list for the required skills, handling spaces after commas.
    
    Parameters:
    - parsed_resume: A dictionary containing at least the "skills" key with a string value.
    - required_skills: A list of strings representing the required skills.
    
    Returns:
    - The number of matched skills and a list of those skills.
    """
    # Split the skills string by comma and strip whitespace from each skill
    candidate_skills = [skill.strip().lower() for skill in parsed_resume["skills"].split(',')]
    
    # Ensure required_skills are also stripped of whitespace for consistent matching
    required_skills_stripped = [skill.strip().lower() for skill in required_skills]
    
    # Find which required skills are present in the candidate's skills list
    matched_skills = [skill for skill in candidate_skills if skill in required_skills_stripped]
    
    return len(matched_skills), matched_skills


def calculate_score(matched_skill_count, parsed_resume):
    """
    Calculates a score for the candidate based on the number of matched skills and years of experience.
    Each matched skill adds 1 point, and each year of experience adds 0.5 points.
    """
    # Extract years of experience and convert to an integer
    experience_years = int(parsed_resume["experience"].split(' ')[0])
    
    # Calculate the score
    score = matched_skill_count + (experience_years * 0.5)
    return score

def filter_candidates(candidate_score, threshold=5):
    """
    Determines if the candidate's score meets or exceeds the threshold.
    
    Parameters:
    - candidate_score: The score calculated for the candidate.
    - threshold: The minimum score required to pass the filtering step.
    
    Returns:
    - A boolean indicating whether the candidate passes the filtering step.
    """
    return candidate_score >= threshold
