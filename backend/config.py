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
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    
    # File settings
    # On Render, use /tmp or a persistent mount if available
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", os.path.join(BASE_DIR, "outputs"))
    PDF_FILENAME: str = "ai_tutor_report.pdf"
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.GROQ_API_KEY:
            # Don't raise in dev if you want to use fallback
            if os.getenv("RENDER", "false").lower() == "true":
                raise ValueError("GROQ_API_KEY environment variable is required in production")
            print("WARNING: GROQ_API_KEY not found. Some AI features will be disabled.")
        
        # Ensure output dir exists
        if not os.path.exists(Config.OUTPUT_DIR):
            os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
            
        return True