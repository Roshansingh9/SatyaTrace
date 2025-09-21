import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

def detect_language(text: str) -> str:
    """Detect the language of the input text using Gemini."""
    try:
        prompt = f"""
Detect the language of this text and return ONLY the language code (2-letter ISO code like 'en', 'hi', 'es', etc.):

Text: "{text}"

Language code:
"""
        
        response = model.generate_content(prompt)
        language_code = response.text.strip().lower()
        
        # Validate and clean the response
        if len(language_code) == 2 and language_code.isalpha():
            logger.info(f"Detected language: {language_code}")
            return language_code
        else:
            logger.warning(f"Invalid language code detected: {language_code}, defaulting to 'en'")
            return 'en'
            
    except Exception as e:
        logger.error(f"Error detecting language: {str(e)}")
        return 'en'  # Default to English

def translate_to_english(text: str, source_lang: str) -> str:
    """Translate text from source language to English using Gemini."""
    try:
        prompt = f"""
Translate this text from {source_lang} to English. Return ONLY the translated text, no explanations:

Text: "{text}"

English translation:
"""
        
        response = model.generate_content(prompt)
        translated_text = response.text.strip()
        
        logger.info(f"Translated to English: {translated_text}")
        return translated_text
        
    except Exception as e:
        logger.error(f"Error translating to English: {str(e)}")
        return text  # Return original text if translation fails

def translate_from_english(text: str, target_lang: str) -> str:
    """Translate text from English to target language using Gemini."""
    try:
        # Language name mapping for better translation
        lang_names = {
            'hi': 'Hindi',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'bn': 'Bengali',
            'te': 'Telugu',
            'ta': 'Tamil',
            'mr': 'Marathi',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'pa': 'Punjabi',
            'ur': 'Urdu'
        }
        
        target_language = lang_names.get(target_lang, target_lang)
        
        prompt = f"""
Translate this English text to {target_language}. Return ONLY the translated text, no explanations:

Text: "{text}"

{target_language} translation:
"""
        
        response = model.generate_content(prompt)
        translated_text = response.text.strip()
        
        logger.info(f"Translated to {target_language}: {translated_text}")
        return translated_text
        
    except Exception as e:
        logger.error(f"Error translating from English: {str(e)}")
        return text  # Return original text if translation fails