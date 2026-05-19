"""
Upload endpoints for RAG document processing
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import os
import traceback
import tempfile
import shutil
from pathlib import Path

from backend.utils.file_loader import FileLoader
from backend.utils.text_splitter import TextSplitter
from backend.services.rag_pipeline import RAGPipeline


router = APIRouter(prefix="/upload", tags=["upload"])

# Global RAG pipeline instance
rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance"""
    global rag_pipeline
    if rag_pipeline is None:
        # Initialize with Groq API key from environment
        groq_api_key = os.getenv("GROQ_API_KEY")
        rag_pipeline = RAGPipeline(groq_api_key=groq_api_key)
    return rag_pipeline


@router.post("/document")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and process a document for RAG
    
    Args:
        file: Uploaded file (PDF, DOCX, TXT)
    
    Returns:
        Processing status and statistics
    """
    try:
        # Validate file type
        file_loader = FileLoader()
        supported_extensions = file_loader.get_supported_extensions()
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported types: {', '.join(supported_extensions)}"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # Write uploaded content to temp file
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Load document
            load_result = file_loader.load_file(temp_file_path)
            
            if not load_result['success']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to load document: {load_result['error']}"
                )
            
            # Split into chunks
            text_splitter = TextSplitter(chunk_size_words=400, overlap_words=50)
            chunks = text_splitter.create_chunks(load_result['content'])
            
            if not chunks:
                raise HTTPException(
                    status_code=400,
                    detail="No text content found in the document"
                )
            
            # Add to RAG pipeline
            pipeline = get_rag_pipeline()
            add_result = pipeline.add_document(chunks)
            
            if not add_result['success']:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process document: {add_result['error']}"
                )
            
            # Get chunk statistics
            chunk_stats = text_splitter.get_chunk_info(chunks)
            
            return {
                "success": True,
                "message": f"Document '{file.filename}' processed successfully",
                "filename": file.filename,
                "file_type": file_extension,
                "chunks_created": len(chunks),
                "chunk_stats": chunk_stats,
                "total_chunks_in_system": add_result['total_chunks']
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in /upload/document: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during upload: {str(e)}"
        )


@router.get("/documents")
async def get_uploaded_documents() -> Dict[str, Any]:
    """
    Get list of uploaded documents
    
    Returns:
        List of document sources and statistics
    """
    try:
        pipeline = get_rag_pipeline()
        stats = pipeline.get_stats()
        
        return {
            "success": True,
            "documents": stats.get('document_sources', []),
            "total_chunks": stats.get('vector_store', {}).get('total_vectors', 0),
            "embedding_cache_size": stats.get('embedding_service', {}).get('cached_embeddings', 0)
        }
        
    except Exception as e:
        # Return error details for debugging
        print(f"ERROR in /upload/documents: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Failed to get documents: {str(e)}",
            "details": str(type(e).__name__)
        }
        # Don't raise HTTPException for debugging


@router.delete("/document/{filename}")
async def delete_document(filename: str) -> Dict[str, Any]:
    """
    Delete a document from the RAG system
    
    Args:
        filename: Name of file to delete
    
    Returns:
        Deletion status
    """
    try:
        pipeline = get_rag_pipeline()
        delete_result = pipeline.delete_document(filename)
        
        if not delete_result['success']:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to delete document: {delete_result['error']}"
            )
        
        return {
            "success": True,
            "message": f"Document '{filename}' deleted successfully",
            "vectors_deleted": delete_result['vectors_deleted']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in /upload/document/{filename}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/stats")
async def get_system_stats() -> Dict[str, Any]:
    """
    Get RAG system statistics
    
    Returns:
        System statistics and performance metrics
    """
    try:
        pipeline = get_rag_pipeline()
        stats = pipeline.get_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        print(f"ERROR in /upload/stats: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system stats: {str(e)}"
        )


@router.post("/clear")
async def clear_all_documents() -> Dict[str, Any]:
    """
    Clear all documents from the RAG system
    
    Returns:
        Clear status
    """
    try:
        pipeline = get_rag_pipeline()
        pipeline.vector_store.clear_index()
        pipeline.embedding_service.clear_cache()
        pipeline.clear_memory()
        
        return {
            "success": True,
            "message": "All documents cleared from RAG system"
        }
        
    except Exception as e:
        print(f"ERROR in /upload/clear: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear documents: {str(e)}"
        )
