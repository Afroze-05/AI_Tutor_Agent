"""
Lightweight Embedding Service for RAG System
Uses TF-IDF and semantic hashing for understanding without PyTorch dependency
"""
import os
import numpy as np
from typing import List, Dict, Any, Optional
import pickle
from pathlib import Path
import math
from collections import Counter
import re


class LightEmbeddingService:
    """Handles text embedding creation using lightweight semantic approach"""
    
    def __init__(self, cache_dir: str = None):
        """
        Initialize embedding service
        
        Args:
            cache_dir: Directory to cache embeddings
        """
        default_dir = os.path.join(os.path.dirname(__file__), "..", "data", "embeddings")
        self.cache_dir = cache_dir or os.getenv("EMBEDDING_CACHE_DIR", default_dir)
        self.embedding_cache = {}
        self.vocab = {}  # For TF-IDF
        self.idf_cache = {}
        
        # Create cache directory
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        # Load cache
        self._load_cache()
        
        print("Light Embedding Service initialized (TF-IDF + Semantic Hash)")
    
    def _load_cache(self):
        """Load cached embeddings if available"""
        cache_file = os.path.join(self.cache_dir, "light_embedding_cache.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.embedding_cache = data.get('embeddings', {})
                    self.vocab = data.get('vocab', {})
                    self.idf_cache = data.get('idf_cache', {})
                print(f"Loaded {len(self.embedding_cache)} cached embeddings")
            except Exception as e:
                print(f"Failed to load cache: {str(e)}")
                self.embedding_cache = {}
                self.vocab = {}
                self.idf_cache = {}
    
    def _save_cache(self):
        """Save embeddings to cache"""
        cache_file = os.path.join(self.cache_dir, "light_embedding_cache.pkl")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'embeddings': self.embedding_cache,
                    'vocab': self.vocab,
                    'idf_cache': self.idf_cache
                }, f)
        except Exception as e:
            print(f"Failed to save cache: {str(e)}")
    
    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text into tokens"""
        # Convert to lowercase and split
        text = text.lower()
        # Remove special characters but keep programming symbols
        text = re.sub(r'[^\w\s\-\>\.\,\;\:\(\)\[\]\{\}\/\*\+\=\%]', ' ', text)
        tokens = text.split()
        
        # Filter out very short tokens
        tokens = [token for token in tokens if len(token) >= 2]
        
        return tokens
    
    def _get_programming_semantic_features(self, text: str) -> np.ndarray:
        """Extract programming-specific semantic features"""
        programming_keywords = {
            'python': ['python', 'def', 'class', 'import', 'self', '__init__', 'print', 'len', 'list', 'dict'],
            'java': ['java', 'public', 'private', 'static', 'void', 'main', 'string', 'int', 'boolean'],
            'c': ['c', 'printf', 'scanf', 'include', 'stdio', 'main', 'int', 'float', 'char'],
            'html': ['html', 'tag', 'div', 'span', 'class', 'id', 'href', 'src', 'alt'],
            'css': ['css', 'color', 'background', 'margin', 'padding', 'display', 'position', 'width'],
            'oop': ['class', 'object', 'inheritance', 'polymorphism', 'encapsulation', 'method', 'attribute'],
            'variables': ['variable', 'var', 'let', 'const', 'declare', 'assign', 'initialize'],
            'functions': ['function', 'def', 'return', 'parameter', 'argument', 'call', 'invoke'],
            'loops': ['loop', 'for', 'while', 'do', 'iterate', 'repeat', 'break', 'continue'],
            'data_types': ['int', 'float', 'string', 'boolean', 'array', 'list', 'dict', 'object'],
            'syntax': ['syntax', 'semicolon', 'comma', 'bracket', 'parenthesis', 'operator']
        }
        
        features = np.zeros(len(programming_keywords), dtype=np.float32)
        text_lower = text.lower()
        
        for i, (category, keywords) in enumerate(programming_keywords.items()):
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += text_lower.count(keyword)
            features[i] = min(score / 10.0, 1.0)  # Normalize to 0-1
        
        return features
    
    def _get_tfidf_embedding(self, text: str) -> np.ndarray:
        """Create TF-IDF based embedding"""
        tokens = self._preprocess_text(text)
        
        if not tokens:
            return np.zeros(384, dtype=np.float32)
        
        # Calculate term frequencies
        tf_counter = Counter(tokens)
        max_freq = max(tf_counter.values())
        
        # Create TF-IDF vector (simplified)
        embedding = np.zeros(384, dtype=np.float32)
        
        for i, (token, tf) in enumerate(tf_counter.items()):
            if i >= 384:  # Limit to 384 dimensions
                break
            
            # Normalized TF
            tf_normalized = tf / max_freq
            
            # Simplified IDF (inverse document frequency approximation)
            idf = math.log(1 + 1000 / (1 + self.vocab.get(token, 1)))
            
            # TF-IDF score
            tfidf = tf_normalized * idf
            
            # Hash to position
            position = hash(token) % 384
            embedding[position] += tfidf
        
        # Add semantic features
        semantic_features = self._get_programming_semantic_features(text)
        # Blend TF-IDF with semantic features
        embedding[:len(semantic_features)] = 0.7 * embedding[:len(semantic_features)] + 0.3 * semantic_features
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector as numpy array
        """
        # Check cache first
        text_hash = hash(text)
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
        
        # Generate new embedding
        try:
            embedding = self._get_tfidf_embedding(text)
            
            # Cache embedding
            self.embedding_cache[text_hash] = embedding
            self._save_cache()
            
            return embedding
        except Exception as e:
            print(f"Failed to generate embedding: {str(e)}")
            # Return zero embedding as fallback
            return np.zeros(384, dtype=np.float32)
    
    def get_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Get embeddings for multiple texts using batch processing
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for text in texts:
            embedding = self.get_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get dimension of embeddings"""
        return 384
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache = {}
        self.vocab = {}
        self.idf_cache = {}
        cache_file = os.path.join(self.cache_dir, "light_embedding_cache.pkl")
        if os.path.exists(cache_file):
            os.remove(cache_file)
        print("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cached_embeddings': len(self.embedding_cache),
            'cache_dir': self.cache_dir,
            'model': 'light-tfidf-semantic',
            'embedding_dimension': self.get_embedding_dimension(),
            'vocab_size': len(self.vocab)
        }
    
    def similarity_search(self, query_embedding: np.ndarray, 
                         candidate_embeddings: List[np.ndarray],
                         top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find most similar embeddings using cosine similarity
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top results to return
        
        Returns:
            List of similarity results with indices and scores
        """
        similarities = []
        
        for i, candidate_embedding in enumerate(candidate_embeddings):
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, candidate_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(candidate_embedding)
            )
            similarities.append({
                'index': i,
                'similarity': float(similarity)
            })
        
        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
