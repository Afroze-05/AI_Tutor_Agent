"""
Intent validation for technical domain restriction
"""
import re
import os
from typing import Tuple, List

# Technical keywords for fast validation
TECH_KEYWORDS = [
    'python', 'javascript', 'java', 'c++', 'c#', 'rust', 'golang', 'html', 'css', 'sql', 'nosql',
    'machine learning', 'deep learning', 'artificial intelligence', 'ai', 'ml', 'llm', 'nlp',
    'react', 'vue', 'angular', 'fastapi', 'flask', 'django', 'backend', 'frontend', 'fullstack',
    'api', 'rest', 'graphql', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'cloud', 'devops',
    'database', 'mongodb', 'postgresql', 'mysql', 'redis', 'git', 'github', 'programming', 'coding',
    'algorithm', 'data structure', 'dsa', 'sorting', 'searching', 'binary tree', 'linked list',
    'software engineering', 'web development', 'app development', 'mobile development',
    'debugging', 'compiler', 'interpreter', 'operating system', 'networking', 'linux', 'bash',
    'shell', 'security', 'cybersecurity', 'cryptography', 'blockchain', 'data science', 'big data',
    'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'pandas', 'numpy', 'matplotlib', 'seaborn'
]

# Rejected categories for prompt injection detection
REJECTED_KEYWORDS = [
    'food', 'recipe', 'biryani', 'pizza', 'cooking', 'chef', 'restaurant',
    'football', 'cricket', 'soccer', 'sports', 'match', 'player',
    'movie', 'film', 'actor', 'netflix', 'hollywood', 'bollywood',
    'politics', 'election', 'government', 'policy',
    'religion', 'god', 'prayer', 'faith',
    'relationship', 'dating', 'love', 'breakup',
    'ignore previous instructions', 'system prompt', 'act as', 'you are now'
]

def is_technical_query(query: str) -> Tuple[bool, str]:
    """
    Validate if the query is technical
    
    Returns:
        (is_technical, reason)
    """
    query_lower = query.lower().strip()
    
    # 1. Check for prompt injection patterns
    injection_patterns = [
        r"ignore previous instructions",
        r"system prompt",
        r"act as",
        r"you are now",
        r"tell me a recipe",
        r"how to cook",
        r"forget everything"
    ]
    for pattern in injection_patterns:
        if re.search(pattern, query_lower):
            return False, "Prompt injection attempt detected."

    # 2. Keyword-based validation
    # Check if any tech keyword is present
    has_tech_keyword = any(keyword in query_lower for keyword in TECH_KEYWORDS)
    
    # Check if any rejected keyword is present
    has_rejected_keyword = any(keyword in query_lower for keyword in REJECTED_KEYWORDS)
    
    # Simple logic: If it has tech keywords and no rejected keywords, it's likely tech
    # If it's too short, it might be general chit-chat
    if len(query_lower.split()) < 2:
        # Check if the single word is a tech keyword
        if query_lower in TECH_KEYWORDS:
            return True, "Single tech keyword."
        return False, "Query is too short or non-technical."

    if has_rejected_keyword and not has_tech_keyword:
        return False, "Non-technical topic detected (rejected category)."
    
    if has_tech_keyword:
        return True, "Technical keyword found."
    
    # 3. Basic heuristic for "How to", "What is", "Why" related to tech
    common_questions = ['how to', 'what is', 'explain', 'code', 'function', 'variable', 'error']
    if any(q in query_lower for q in common_questions) and len(query_lower) > 10:
        # This is a bit risky but we'll let the LLM handle it if it passes keywords
        # But we want STRICT restriction, so if no tech keywords, we might reject
        pass

    # Default to rejection for strictness if no tech indicators found
    return False, "Topic appears to be outside the technical scope of this AI Tutor."

def get_rejection_response() -> str:
    """Standard rejection message"""
    return "❌ This AI Tutor is restricted to technical and programming-related topics only. Please ask about coding, AI, ML, web development, software engineering, or related technical concepts."
