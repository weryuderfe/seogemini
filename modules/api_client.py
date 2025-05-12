import requests
import json
import time
from typing import Optional, List, Dict, Any

class GeminiClient:
    """Client for interacting with Google's Gemini API"""
    
    def __init__(self, api_keys: List[str]):
        """Initialize with one or more API keys for rotation"""
        self.api_keys = api_keys
        self.current_key_index = 0
        
        # Gemini model rotation sequence
        self.models = ["gemini-1.5-flash", "gemini-2.0-flash"]
        self.current_model_index = 0
    
    def _get_current_key(self) -> str:
        """Get the current API key"""
        if not self.api_keys:
            raise ValueError("No API keys available")
        return self.api_keys[self.current_key_index]
    
    def _get_current_model(self) -> str:
        """Get the current model"""
        return self.models[self.current_model_index]
    
    def _rotate_key(self) -> str:
        """Rotate to the next API key and return it"""
        if not self.api_keys:
            raise ValueError("No API keys available")
        
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return self._get_current_key()
    
    def _rotate_model(self) -> str:
        """Rotate to the next model and return it"""
        self.current_model_index = (self.current_model_index + 1) % len(self.models)
        return self._get_current_model()
    
    def generate_content(self, prompt: str, model: Optional[str] = None, 
                         temperature: float = 0.7, max_output_tokens: int = 8192, 
                         max_retries: int = 3) -> Optional[str]:
        """
        Send a request to the Gemini API and get a response
        
        Args:
            prompt: The text prompt to send to the API
            model: The model to use (defaults to current model in rotation)
            temperature: Controls randomness (higher = more random)
            max_output_tokens: Maximum length of generated content
            max_retries: Number of retry attempts
            
        Returns:
            Generated text content or None if all attempts fail
        """
        if not model:
            model = self._get_current_model()
        
        retry_count = 0
        
        while retry_count < max_retries:
            # Get current API key
            api_key = self._get_current_key()
            
            # Set up API request
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": max_output_tokens,
                    "stopSequences": []
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            try:
                # Make the API request
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                response_json = response.json()
                
                # Extract the generated text
                if "candidates" in response_json and len(response_json["candidates"]) > 0:
                    text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                    return text
                else:
                    # No valid response, rotate both API key and model
                    self._rotate_key()
                    self._rotate_model()
                    retry_count += 1
            
            except requests.exceptions.HTTPError as e:
                error_str = str(e)
                
                # Handle rate limiting
                if "429" in error_str and "Too Many Requests" in error_str:
                    # Rotate both API key and model
                    self._rotate_key()
                    self._rotate_model()
                    
                    # Wait before retrying
                    time.sleep(1.5)
                else:
                    # Other HTTP error, rotate API key and model
                    self._rotate_key()
                    self._rotate_model()
                
                retry_count += 1
            
            except Exception as e:
                # General exception, rotate API key and model
                self._rotate_key()
                self._rotate_model()
                retry_count += 1
        
        # If we've exhausted all retries
        return None

# Function to test if an API key is valid
def test_api_key(api_key: str) -> bool:
    """Test if a Gemini API key is valid by making a minimal request"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Hello"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 10,
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return True
    except:
        return False

# Create a function to initialize the client with available API keys
def get_gemini_client() -> GeminiClient:
    """Create and return a GeminiClient with available API keys"""
    try:
        with open("apikey.txt", "r") as file:
            api_keys = [line.strip() for line in file if line.strip()]
        
        if not api_keys:
            raise ValueError("No API keys found in apikey.txt")
        
        return GeminiClient(api_keys)
    
    except Exception as e:
        raise ValueError(f"Error initializing Gemini client: {str(e)}")