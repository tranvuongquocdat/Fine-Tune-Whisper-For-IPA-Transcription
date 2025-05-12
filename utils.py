import os
import google.generativeai as genai
from dotenv import load_dotenv
import random
import time

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_text_with_gemini(topic, difficulty, max_words=15):
    """
    Generate text using Gemini API based on topic and difficulty
    
    Args:
        topic (str): Topic of the sentence (e.g., education, travel)
        difficulty (str): Difficulty level (e.g., easy, medium, hard)
        max_words (int): Maximum number of words in the generated text
    
    Returns:
        str: Generated text
    """
    start_time = time.time()
    
    prompt = f"""
    Generate a natural English sentence about {topic} that is {difficulty} level for pronunciation practice.
    The sentence should be natural, common in daily conversation, and not exceed {max_words} words.
    Only provide the sentence itself without any introduction or explanation.
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    sentence = response.text.strip()
    # Make sure the sentence is not too long
    words = sentence.split()
    if len(words) > max_words:
        sentence = ' '.join(words[:max_words])
    
    elapsed_time = time.time() - start_time
    return sentence, elapsed_time

def evaluate_pronunciation(reference_ipa, user_ipa):
    """
    Evaluate pronunciation by comparing reference and user IPA transcriptions using Gemini
    
    Args:
        reference_ipa (str): Reference IPA transcription
        user_ipa (str): User's IPA transcription
    
    Returns:
        str: Evaluation results with score and feedback in plain text
        float: Time taken for evaluation
    """
    start_time = time.time()
    
    prompt = f"""
    I have two IPA (International Phonetic Alphabet) transcriptions:
    
    Reference (Correct): {reference_ipa}
    User's Pronunciation: {user_ipa}
    
    As a pronunciation expert, please analyze these transcriptions and provide:
    1. A score from 60-100 reflecting the pronunciation accuracy
    2. Specific feedback on the pronunciation errors and what to improve
    
    Format your response as plain text with:
    Score: (number between 0-100)
    Feedback: (your detailed feedback, no more than 20 words)
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    elapsed_time = time.time() - start_time
    
    try:
        # Return the plain text response
        result = response.text.strip()
        return result, elapsed_time
    except Exception as e:
        return f"Error evaluating pronunciation: {str(e)}", elapsed_time

# Sample topics and difficulty levels for the UI
def get_sample_topics():
    return [
        "education", "travel", "food", "technology", "sports", 
        "health", "environment", "business", "entertainment", "science"
    ]

def get_difficulty_levels():
    return ["beginner", "intermediate", "advanced"] 