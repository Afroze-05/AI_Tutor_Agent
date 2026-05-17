"""
Configuration settings for AI Tutor
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Groq API settings
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    # File settings
    OUTPUT_DIR: str = "outputs"
    PDF_FILENAME: str = "ai_tutor_report.pdf"
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Debug print to confirm key is loaded
        print(f"DEBUG: GROQ_API_KEY loaded successfully (length: {len(Config.GROQ_API_KEY)})")
        return True