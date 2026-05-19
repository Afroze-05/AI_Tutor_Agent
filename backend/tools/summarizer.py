"""
AI Summarizer Tool
Uses Groq API for text summarization and Q&A
"""
from typing import Dict, Any, List, Optional
from backend.config import Config

class AISummarizer:
    """Groq-based text summarization and Q&A"""
    
    def __init__(self):
        """Initialize Groq client"""
        try:
            from groq import Groq
            self.client = Groq(api_key=Config.GROQ_API_KEY)
            self.use_llm = True
        except ImportError:
            self.use_llm = False
            print("Groq not available, using fallback summarization")
        
    def summarize(self, text: str) -> str:
        """
        Summarize text using Groq
        
        Args:
            text: Input text to summarize
            
        Returns:
            Summarized text
        """
        if self.use_llm:
            try:
                response = self.client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that summarizes educational content clearly and concisely."},
                        {"role": "user", "content": f"Please summarize this educational content:\n\n{text}"}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Groq summarization failed: {str(e)}")
        
        # Fallback to simple extraction
        return self._fallback_summarize(text)
    
    def _fallback_summarize(self, text: str) -> str:
        """Simple fallback summarization"""
        sentences = text.split('.')
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not meaningful_sentences:
            return "No meaningful content found to summarize."
        
        # Return first 3 sentences as summary
        summary = '. '.join(meaningful_sentences[:3]) + '.'
        return summary
    
    def answer_question(self, text: str, question: str) -> Dict[str, Any]:
        """
        Answer a user's question based on text content
        
        Args:
            text: Full text content
            question: User's question about content
            
        Returns:
            Dictionary containing answer
        """
        if self.use_llm:
            try:
                response = self.client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on provided text content."},
                        {"role": "user", "content": f"Based on this text:\n\n{text}\n\nAnswer this question: {question}"}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                return {
                    'success': True,
                    'answer': response.choices[0].message.content.strip(),
                    'question': question
                }
            except Exception as e:
                print(f"Groq Q&A failed: {str(e)}")
        
        # Fallback to keyword-based answer extraction
        answer = self._find_answer_in_text(text, question)
        return {
            'success': True,
            'answer': answer,
            'question': question
        }
    
    def _find_answer_in_text(self, text: str, question: str) -> str:
        """
        Find answer to question in text using keyword matching
        
        Args:
            text: Full text content
            question: User's question
            
        Returns:
            Answer based on text content
        """
        import re
        
        # Extract keywords from question
        question_words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        question_keywords = [word for word in question_words if len(word) > 3]
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Find sentences containing question keywords
        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            keyword_count = sum(1 for keyword in question_keywords if keyword in sentence_lower)
            if keyword_count > 0:
                relevant_sentences.append((sentence.strip(), keyword_count))
        
        # Sort by keyword count and return top relevant sentences
        relevant_sentences.sort(key=lambda x: x[1], reverse=True)
        
        if relevant_sentences:
            answer_sentences = [s[0] for s in relevant_sentences[:3]]
            return "Based on the content: " + " ".join(answer_sentences) + "."
        else:
            return "I couldn't find specific information about your question in the provided content."