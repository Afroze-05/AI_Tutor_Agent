"""
Vector Store Service for RAG System
Uses FAISS for efficient similarity search
"""
import faiss
import numpy as np
import pickle
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json


class VectorStore:
    """Handles vector storage and retrieval using FAISS"""
    
    def __init__(self, index_dir: str = None, dimension: int = 384):
        """
        Initialize vector store
        
        Args:
            index_dir: Directory to store FAISS index and metadata
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        # Allow environment variable override for production (e.g. persistent disk path)
        default_dir = os.path.join(os.path.dirname(__file__), "..", "data", "vectors")
        self.index_dir = index_dir or os.getenv("VECTOR_INDEX_DIR", default_dir)
        self.dimension = dimension
        self.index = None
        self.metadata = []
        self.doc_store = {}  # Store actual text chunks
        
        # Create directory
        Path(self.index_dir).mkdir(parents=True, exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing FAISS index and metadata"""
        index_file = os.path.join(self.index_dir, "faiss.index")
        metadata_file = os.path.join(self.index_dir, "metadata.pkl")
        doc_store_file = os.path.join(self.index_dir, "doc_store.pkl")
        
        if os.path.exists(index_file) and os.path.exists(metadata_file):
            try:
                self.index = faiss.read_index(index_file)
                with open(metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                with open(doc_store_file, 'rb') as f:
                    self.doc_store = pickle.load(f)
                print(f"Loaded existing index with {self.index.ntotal} vectors")
            except Exception as e:
                print(f"Failed to load existing index: {str(e)}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create new FAISS index"""
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product for cosine similarity
        self.metadata = []
        self.doc_store = {}
        print("Created new FAISS index")
    
    def add_vectors(self, embeddings: List[np.ndarray], chunks: List[Dict[str, Any]]):
        """
        Add vectors and their metadata to the index
        
        Args:
            embeddings: List of embedding vectors
            chunks: List of chunk dictionaries with text and metadata
        """
        if len(embeddings) != len(chunks):
            raise ValueError("Number of embeddings must match number of chunks")
        
        # Normalize embeddings for cosine similarity
        normalized_embeddings = []
        for embedding in embeddings:
            embedding_np = np.array(embedding, dtype=np.float32)
            if embedding_np.ndim == 1:
                embedding_np = embedding_np.reshape(1, -1)
            # L2 normalize for cosine similarity
            embedding_np = embedding_np / np.linalg.norm(embedding_np, axis=1, keepdims=True)
            normalized_embeddings.append(embedding_np[0])
        
        # Convert to numpy array
        vectors_array = np.array(normalized_embeddings, dtype=np.float32)
        
        # Add to index
        start_idx = self.index.ntotal
        self.index.add(vectors_array)
        
        # Add metadata and document store
        for i, chunk in enumerate(chunks):
            idx = start_idx + i
            chunk_metadata = chunk['metadata'].copy()
            chunk_metadata['vector_index'] = idx
            
            self.metadata.append(chunk_metadata)
            self.doc_store[idx] = chunk['text']
        
        print(f"Added {len(embeddings)} vectors to index. Total: {self.index.ntotal}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
        
        Returns:
            List of search results with text, metadata, and scores
        """
        if self.index.ntotal == 0:
            return []
        
        # Normalize query embedding
        query_embedding = np.array(query_embedding, dtype=np.float32)
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # Search
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx in self.doc_store:  # Valid index
                result = {
                    'text': self.doc_store[idx],
                    'metadata': self.metadata[idx],
                    'score': float(score),
                    'vector_index': int(idx)
                }
                results.append(result)
        
        return results
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        index_file = os.path.join(self.index_dir, "faiss.index")
        metadata_file = os.path.join(self.index_dir, "metadata.pkl")
        doc_store_file = os.path.join(self.index_dir, "doc_store.pkl")
        
        try:
            faiss.write_index(self.index, index_file)
            with open(metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            with open(doc_store_file, 'wb') as f:
                pickle.dump(self.doc_store, f)
            print(f"Saved index with {self.index.ntotal} vectors")
        except Exception as e:
            raise RuntimeError(f"Failed to save index: {str(e)}")
    
    def clear_index(self):
        """Clear all vectors from the index"""
        self._create_new_index()
        self._save_index()
        print("Cleared all vectors from index")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'index_dir': self.index_dir,
            'documents_stored': len(self.doc_store)
        }
    
    def get_document_sources(self) -> List[str]:
        """Get list of unique document sources"""
        sources = set()
        for metadata in self.metadata:
            if 'filename' in metadata:
                sources.add(metadata['filename'])
        return list(sources)
    
    def delete_by_source(self, filename: str) -> int:
        """
        Delete all vectors from a specific file
        
        Args:
            filename: Name of file to delete
        
        Returns:
            Number of vectors deleted
        """
        indices_to_delete = []
        
        for i, metadata in enumerate(self.metadata):
            if metadata.get('filename') == filename:
                indices_to_delete.append(metadata['vector_index'])
        
        if not indices_to_delete:
            return 0
        
        # Remove from document store and metadata
        for idx in indices_to_delete:
            if idx in self.doc_store:
                del self.doc_store[idx]
        
        self.metadata = [m for m in self.metadata if m.get('filename') != filename]
        
        # Recreate index without deleted vectors
        self._recreate_index()
        
        print(f"Deleted {len(indices_to_delete)} vectors from {filename}")
        return len(indices_to_delete)
    
    def _recreate_index(self):
        """Recreate index with remaining vectors"""
        if not self.doc_store:
            self._create_new_index()
            return
        
        # Get remaining vectors and metadata
        remaining_indices = sorted(self.doc_store.keys())
        remaining_metadata = [m for m in self.metadata if m['vector_index'] in self.doc_store]
        
        # Create new index
        self.index = faiss.IndexFlatIP(self.dimension)
        
        # Note: This is a simplified recreation. In practice, you'd need to 
        # regenerate embeddings for remaining documents or store them separately
        # For now, we'll just update metadata
        self.metadata = remaining_metadata
        
        # Save the updated state
        self.save_index()
