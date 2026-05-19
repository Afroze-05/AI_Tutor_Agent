"""
Smart Study Assistant RAG Engine
Retrieval Augmented Generation for enhanced learning
"""
import json
import sqlite3
import os
from typing import Dict, List, Any, Optional, Tuple
from .ai_summarizer import AISummarizer
import re

class RAGEngine:
    """Retrieval Augmented Generation for knowledge enhancement"""
    
    def __init__(self, db_path: str = "study_assistant.db"):
        self.db_path = db_path
        self.ai_summarizer = AISummarizer()
        self.init_rag_tables()
    
    def init_rag_tables(self):
        """Initialize RAG-specific database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Document chunks table for better retrieval
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                chunk_text TEXT NOT NULL,
                metadata TEXT,  -- JSON metadata
                embedding_vector TEXT,  -- JSON array of embeddings
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Conversation history for context
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                context_used TEXT,  -- JSON of retrieved context
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_document(self, document_id: str, subject: str, topic: str, 
                    content: str, chunk_size: int = 500, 
                    metadata: Dict = None) -> bool:
        """
        Add document to knowledge base with chunking
        
        Args:
            document_id: Unique identifier for the document
            subject: Subject area
            topic: Specific topic
            content: Full document content
            chunk_size: Size of each chunk for retrieval
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            # Split content into chunks
            chunks = self._chunk_text(content, chunk_size)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for i, chunk in enumerate(chunks):
                cursor.execute(
                    """INSERT INTO document_chunks 
                       (document_id, chunk_index, subject, topic, chunk_text, metadata)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (document_id, i, subject, topic, chunk, 
                     json.dumps(metadata) if metadata else None)
                )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error adding document: {str(e)}")
            return False
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []
        
        # Simple chunking by sentences with overlap
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                # Keep last sentence for overlap
                current_chunk = [current_chunk[-1]] if current_chunk else []
                current_length = len(current_chunk[0]) if current_chunk else 0
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def retrieve_relevant_context(self, subject: str, query: str, 
                                 session_id: str = None, limit: int = 5) -> Dict:
        """
        Retrieve relevant context for RAG
        
        Args:
            subject: Subject area
            query: User query or topic
            session_id: Optional session for personalization
            limit: Number of chunks to retrieve
            
        Returns:
            Retrieved context and metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple keyword-based retrieval (in production, use vector similarity)
            query_terms = self._extract_keywords(query)
            
            # Build search query
            search_conditions = []
            search_params = [subject, limit]
            
            for term in query_terms:
                search_conditions.append("chunk_text LIKE ?")
                search_params.append(f"%{term}%")
            
            where_clause = "subject = ?"
            if search_conditions:
                where_clause += " AND (" + " OR ".join(search_conditions) + ")"
            
            cursor.execute(
                f"""SELECT document_id, chunk_index, topic, chunk_text, metadata
                   FROM document_chunks 
                   WHERE {where_clause}
                   ORDER BY chunk_index
                   LIMIT ?""",
                search_params
            )
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'document_id': row[0],
                    'chunk_index': row[1],
                    'topic': row[2],
                    'text': row[3],
                    'metadata': json.loads(row[4]) if row[4] else {}
                })
            
            conn.close()
            
            return {
                'success': True,
                'query': query,
                'subject': subject,
                'retrieved_chunks': results,
                'total_chunks': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Context retrieval failed: {str(e)}",
                'retrieved_chunks': []
            }
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query for search"""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
                     'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'what', 
                     'how', 'when', 'where', 'why', 'tell', 'explain', 'describe'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:5]  # Limit to top 5 keywords
    
    def generate_rag_response(self, subject: str, query: str, 
                            session_id: str = None) -> Dict:
        """
        Generate response using RAG
        
        Args:
            subject: Subject area
            query: User question or topic
            session_id: User session for personalization
            
        Returns:
            Enhanced response with retrieved context
        """
        try:
            # Retrieve relevant context
            context_result = self.retrieve_relevant_context(subject, query, session_id)
            
            if not context_result['success'] or not context_result['retrieved_chunks']:
                # Fallback to regular AI response
                return self._generate_fallback_response(subject, query)
            
            # Build context for AI
            context_text = self._build_context_text(context_result['retrieved_chunks'])
            
            # Generate enhanced response
            prompt = f"""
Based on the following context about {subject}, answer the user's question.

Context:
{context_text}

User Question: {query}

Instructions:
- Use the provided context to answer accurately
- If context doesn't contain the answer, say so clearly
- Provide specific details from the context
- Include citations to the source topics when relevant

Answer:
"""
            
            response = self.ai_summarizer.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable tutor providing accurate answers based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for factual responses
                max_tokens=800
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Save conversation
            self._save_conversation(session_id, subject, query, ai_response, 
                                   context_result['retrieved_chunks'])
            
            return {
                'success': True,
                'response': ai_response,
                'context_used': context_result['retrieved_chunks'],
                'sources': list(set(chunk['topic'] for chunk in context_result['retrieved_chunks'])),
                'rag_enhanced': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"RAG response generation failed: {str(e)}",
                'response': "I'm having trouble accessing my knowledge base. Let me help you with a general response instead."
            }
    
    def _build_context_text(self, chunks: List[Dict]) -> str:
        """Build formatted context text from chunks"""
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            context_parts.append(f"[Source: {chunk['topic']}]\n{chunk['text']}")
        
        return "\n\n".join(context_parts)
    
    def _generate_fallback_response(self, subject: str, query: str) -> Dict:
        """Generate fallback response without RAG"""
        try:
            prompt = f"""
As an expert in {subject}, answer the following question:

{query}

Provide a helpful, educational response that demonstrates expertise in the subject.
"""
            
            response = self.ai_summarizer.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert educator providing helpful answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=600
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            return {
                'success': True,
                'response': ai_response,
                'context_used': [],
                'sources': [],
                'rag_enhanced': False,
                'note': 'Response generated without specific context'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Fallback response failed: {str(e)}",
                'response': "I'm experiencing technical difficulties. Please try again later."
            }
    
    def _save_conversation(self, session_id: str, subject: str, 
                          user_message: str, ai_response: str, 
                          context_used: List[Dict]) -> bool:
        """Save conversation for future context"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO conversation_history 
                   (session_id, subject, user_message, ai_response, context_used)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, subject, user_message, ai_response, 
                 json.dumps(context_used) if context_used else None)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error saving conversation: {str(e)}")
            return False
    
    def get_conversation_history(self, session_id: str, subject: str = None, 
                                limit: int = 10) -> List[Dict]:
        """Get conversation history for context"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if subject:
                cursor.execute(
                    """SELECT user_message, ai_response, timestamp
                       FROM conversation_history 
                       WHERE session_id = ? AND subject = ?
                       ORDER BY timestamp DESC
                       LIMIT ?""",
                    (session_id, subject, limit)
                )
            else:
                cursor.execute(
                    """SELECT user_message, ai_response, timestamp
                       FROM conversation_history 
                       WHERE session_id = ?
                       ORDER BY timestamp DESC
                       LIMIT ?""",
                    (session_id, limit)
                )
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'user_message': row[0],
                    'ai_response': row[1],
                    'timestamp': row[2]
                })
            
            conn.close()
            return history
            
        except Exception as e:
            print(f"Error retrieving conversation history: {str(e)}")
            return []
    
        
    def get_knowledge_summary(self, subject: str) -> Dict:
        """Get summary of knowledge base for a subject"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get document count
            cursor.execute(
                "SELECT COUNT(DISTINCT document_id) FROM document_chunks WHERE subject = ?",
                (subject,)
            )
            doc_count = cursor.fetchone()[0]
            
            # Get topic count
            cursor.execute(
                "SELECT COUNT(DISTINCT topic) FROM document_chunks WHERE subject = ?",
                (subject,)
            )
            topic_count = cursor.fetchone()[0]
            
            # Get total chunks
            cursor.execute(
                "SELECT COUNT(*) FROM document_chunks WHERE subject = ?",
                (subject,)
            )
            chunk_count = cursor.fetchone()[0]
            
            # Get recent topics
            cursor.execute(
                """SELECT DISTINCT topic, COUNT(*) as chunk_count
                   FROM document_chunks 
                   WHERE subject = ?
                   GROUP BY topic
                   ORDER BY chunk_count DESC
                   LIMIT 5""",
                (subject,)
            )
            top_topics = [{'topic': row[0], 'chunks': row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'subject': subject,
                'documents': doc_count,
                'topics': topic_count,
                'total_chunks': chunk_count,
                'top_topics': top_topics
            }
            
        except Exception as e:
            return {
                'subject': subject,
                'error': f"Failed to get knowledge summary: {str(e)}"
            }
