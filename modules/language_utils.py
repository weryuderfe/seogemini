from typing import Optional

try:
    from langdetect import detect
    from langcodes import Language
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

def detect_language(subject: str) -> str:
    """
    Detect language from text using langdetect if available
    
    Args:
        subject: The text to detect language from
        
    Returns:
        The detected language name (defaults to "English" if detection fails)
    """
    if not LANGDETECT_AVAILABLE:
        # If langdetect is not available, return English as default
        return "English"
    
    try:
        lang_code = detect(subject)
        language = Language.make(language=lang_code).display_name()
        return language
    except Exception as e:
        # On any error, default to English
        print(f"Language detection error: {str(e)}. Defaulting to English.")
        return "English"

def is_english(text: str) -> bool:
    """
    Check if text is in English
    
    Args:
        text: The text to check
        
    Returns:
        True if English is detected, False otherwise
    """
    if not LANGDETECT_AVAILABLE:
        # If langdetect is not available, assume English
        return True
    
    try:
        lang_code = detect(text)
        return lang_code.lower() == 'en'
    except:
        # On any error, assume English
        return True

def get_language_code(language_name: str) -> str:
    """
    Get ISO language code from language name
    
    Args:
        language_name: The language name (e.g., "English", "Spanish")
        
    Returns:
        ISO language code (e.g., "en", "es")
    """
    common_languages = {
        "english": "en",
        "spanish": "es",
        "french": "fr",
        "german": "de",
        "italian": "it",
        "portuguese": "pt",
        "russian": "ru",
        "chinese": "zh",
        "japanese": "ja",
        "korean": "ko",
        "arabic": "ar",
        "hindi": "hi",
        "indonesian": "id"
    }
    
    # Normalize input
    normalized = language_name.lower().strip()
    
    # Return code from common languages dict if available
    if normalized in common_languages:
        return common_languages[normalized]
    
    # Try with langcodes if available
    if LANGDETECT_AVAILABLE:
        try:
            return Language.find(normalized).to_tag()
        except:
            pass
    
    # Default to English if not found
    return "en"