"""
Text Splitter for RAG System
Splits documents into chunks with overlap for better context
"""
from typing import List, Dict, Any
import re
import os


class TextSplitter:
    """Handles splitting text into chunks with overlap"""
    
    def __init__(self, chunk_size_words: int = 400, overlap_words: int = 50):
        """
        Initialize text splitter
        
        Args:
            chunk_size_words: Target words per chunk (300-500 recommended)
            overlap_words: Words to overlap between chunks (50 recommended)
        """
        self.chunk_size_words = chunk_size_words
        self.overlap_words = overlap_words
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for better chunk boundaries"""
        # Split on sentence endings but keep them
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _count_words(self, text: str) -> int:
        """Count words in text"""
        return len(text.split())
    
    def create_chunks(self, text_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split document content into chunks with overlap
        
        Args:
            text_content: List of text segments with metadata
        
        Returns:
            List of chunks with text and metadata
        """
        chunks = []
        
        for content_item in text_content:
            text = content_item['text']
            metadata = {k: v for k, v in content_item.items() if k != 'text'}
            
            # Split into sentences first
            sentences = self._split_into_sentences(text)
            
            if not sentences:
                continue
            
            # Create chunks by combining sentences
            current_chunk_sentences = []
            current_word_count = 0
            
            for i, sentence in enumerate(sentences):
                sentence_word_count = self._count_words(sentence)
                
                # If adding this sentence exceeds chunk size, create chunk
                if (current_word_count + sentence_word_count > self.chunk_size_words and 
                    current_chunk_sentences):
                    
                    # Create chunk
                    chunk_text = ' '.join(current_chunk_sentences)
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_id': len(chunks),
                        'word_count': current_word_count,
                        'sentence_count': len(current_chunk_sentences)
                    })
                    
                    chunks.append({
                        'text': chunk_text,
                        'metadata': chunk_metadata
                    })
                    
                    # Start new chunk with overlap
                    overlap_sentences = self._get_overlap_sentences(current_chunk_sentences)
                    current_chunk_sentences = overlap_sentences + [sentence]
                    current_word_count = sum(self._count_words(s) for s in current_chunk_sentences)
                else:
                    current_chunk_sentences.append(sentence)
                    current_word_count += sentence_word_count
            
            # Handle remaining sentences
            if current_chunk_sentences:
                chunk_text = ' '.join(current_chunk_sentences)
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_id': len(chunks),
                    'word_count': current_word_count,
                    'sentence_count': len(current_chunk_sentences)
                })
                
                chunks.append({
                    'text': chunk_text,
                    'metadata': chunk_metadata
                })
        
        return chunks
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """
        Get sentences for overlap from previous chunk
        """
        overlap_word_count = 0
        overlap_sentences = []
        
        # Start from the end and work backwards
        for sentence in reversed(sentences):
            sentence_word_count = self._count_words(sentence)
            if overlap_word_count + sentence_word_count <= self.overlap_words:
                overlap_sentences.insert(0, sentence)
                overlap_word_count += sentence_word_count
            else:
                break
        
        return overlap_sentences
    
    def get_chunk_info(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about created chunks"""
        if not chunks:
            return {
                'total_chunks': 0,
                'avg_words_per_chunk': 0,
                'min_words': 0,
                'max_words': 0
            }
        
        word_counts = [chunk['metadata']['word_count'] for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_words_per_chunk': sum(word_counts) / len(word_counts),
            'min_words': min(word_counts),
            'max_words': max(word_counts),
            'total_words': sum(word_counts)
        }
