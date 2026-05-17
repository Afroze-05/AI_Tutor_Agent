"""
AI Summarizer Tool
Uses Groq API for text summarization and Q&A
"""
from typing import Dict, Any, List, Optional
from config import Config

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
        
    def answer_question(self, text: str, question: str) -> str:
        """
        Answer question based on text using Groq
        
        Args:
            text: Source text
            question: Question to answer
            
        Returns:
            Answer based on text
        """
        if self.use_llm:
            try:
                response = self.client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on provided educational content. Use only the given context to answer."},
                        {"role": "user", "content": f"Context: {text}\n\nQuestion: {question}"}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Groq Q&A failed: {str(e)}")
        
        # Fallback to keyword-based answer extraction
        return self._fallback_answer_question(text, question)
            
    def extract_topics(self, text: str) -> List[str]:
        """
        Extract topics from text using Groq
        
        Args:
            text: Input text
            
        Returns:
            List of topics
        """
        if self.use_llm:
            try:
                response = self.client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts key topics from educational content. Return topics as a comma-separated list."},
                        {"role": "user", "content": f"Extract the main topics from this text:\n\n{text}"}
                    ],
                    max_tokens=100,
                    temperature=0.7
                )
                topics_text = response.choices[0].message.content.strip()
                return [topic.strip() for topic in topics_text.split(',')]
            except Exception as e:
                print(f"Groq topic extraction failed: {str(e)}")
        
        # Fallback to simple keyword extraction
        return self._fallback_extract_topics(text)
        
    def extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from text using Groq
        
        Args:
            text: Input text
            
        Returns:
            List of key points
        """
        if self.use_llm:
            try:
                response = self.client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts key points from educational content. Return each key point on a new line."},
                        {"role": "user", "content": f"Extract the key points from this text:\n\n{text}"}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                points_text = response.choices[0].message.content.strip()
                return [point.strip() for point in points_text.split('\n') if point.strip()]
            except Exception as e:
                print(f"Groq key point extraction failed: {str(e)}")
        
        # Fallback to simple sentence extraction
        return self._fallback_extract_key_points(text)
    
    def _fallback_summarize(self, text: str) -> str:
        """Simple fallback summarization"""
        sentences = text.split('.')
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not meaningful_sentences:
            return "No meaningful content found to summarize."
        
        # Return first 3 sentences as summary
        summary = '. '.join(meaningful_sentences[:3]) + '.'
        return summary
    
    def _fallback_answer_question(self, text: str, question: str) -> str:
        """Simple fallback Q&A"""
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
    
    def _fallback_extract_topics(self, text: str) -> List[str]:
        """Simple fallback topic extraction"""
        import re
        from collections import Counter
        
        # Extract words and count frequency
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        word_freq = Counter(word for word in words if word not in {'this', 'that', 'with', 'from', 'they', 'have', 'been', 'would', 'could', 'should'})
        
        # Get most common words as topics
        topics = []
        for word, count in word_freq.most_common(5):
            if count >= 2:  # Only include words that appear at least twice
                topics.append(word.capitalize())
        
        return topics or ["General topic"]
    
    def _fallback_extract_key_points(self, text: str) -> List[str]:
        """Simple fallback key point extraction"""
        sentences = text.split('.')
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        # Return first 5 meaningful sentences as key points
        return meaningful_sentences[:5] or ["No key points found."]
