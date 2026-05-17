"""
Chat endpoints with RAG integration
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.rag_pipeline import RAGPipeline


router = APIRouter(prefix="/chat", tags=["chat"])

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



class ChatRequest(BaseModel):
    message: str
    use_rag: Optional[bool] = True  # Use RAG (embedding + retrieval + LLM)
    top_k: Optional[int] = 5  # fetch 5 most relevant chunks Number of chunks to retrieve
# User → ChatRequest → Backend → RAGPipeline

class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
#   {"content": "Python is a language...", "score": 0.89},
#   {"content": "It is used for AI...", "score": 0.85}
    method: Optional[str] = None  # "rag" or "fallback"


class SummaryRequest(BaseModel):
    query: str


class SummaryResponse(BaseModel):
    summary: str


@router.post("/query", response_model=ChatResponse)
async def chat_with_rag(request: ChatRequest) -> Dict[str, Any]:
    """
    Chat with RAG-enabled question answering
    
    Args:
        request: Chat request with message and RAG settings
    
    Returns:
        Answer with sources
    """
    try:
        if not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        pipeline = get_rag_pipeline()
        
        if request.use_rag:
            # Use RAG pipeline
            result = pipeline.query(request.message, top_k=request.top_k)
            
            return {
                "answer": result['answer'],
                "sources": result.get('sources', []),
                "context_used": result.get('context_used', False),
                "rag_enabled": True,
                "chunks_retrieved": result.get('chunks_retrieved', 0)
            }
        else:
            # Fallback to basic response (without RAG)
            return {
                "answer": "RAG is disabled. Please enable RAG to get document-based answers.",
                "sources": [],
                "context_used": False,
                "rag_enabled": False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        # Return error details for debugging
        return {
            "answer": f"Error: {str(e)}",
            "sources": [],
            "context_used": False,
            "rag_enabled": False,
            "error_details": str(type(e).__name__)
        }
        # Don't raise HTTPException for debugging


@router.post("/clear-memory")
async def clear_chat_memory() -> Dict[str, Any]:
    """
    Clear chat memory
    
    Returns:
        Clear status
    """
    try:
        pipeline = get_rag_pipeline()
        pipeline.clear_memory()
        
        return {
            "success": True,
            "message": "Chat memory cleared successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear chat memory: {str(e)}"
        )


@router.get("/memory")
async def get_chat_memory() -> Dict[str, Any]:
    """
    Get current chat memory
    
    Returns:
        Chat memory content
    """
    try:
        pipeline = get_rag_pipeline()
        
        return {
            "success": True,
            "memory": pipeline.chat_memory,
            "memory_size": len(pipeline.chat_memory)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat memory: {str(e)}"
        )


@router.get("/health")
async def chat_health_check() -> Dict[str, Any]:
    """
    Health check for chat service
    
    Returns:
        Service health status
    """
    try:
        pipeline = get_rag_pipeline()
        stats = pipeline.get_stats()
        
        return {
            "success": True,
            "status": "healthy",
            "rag_enabled": True,
            "vector_store_size": stats['vector_store']['total_vectors'],
            "memory_size": len(pipeline.chat_memory)
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/explain-more")
async def explain_more(last_answer: str) -> Dict[str, Any]:
    """
    Get more detailed explanation of the last answer
    
    Args:
        last_answer: The previous answer to explain in more detail
    
    Returns:
        Detailed explanation
    """
    try:
        pipeline = get_rag_pipeline()
        
        # Create a follow-up query
        follow_up_query = f"Please explain this in more detail with examples: {last_answer}"
        
        # Query with RAG
        result = pipeline.query(follow_up_query, top_k=3)
        
        return {
            "answer": result['answer'],
            "sources": result.get('sources', []),
            "context_used": result.get('context_used', False),
            "type": "detailed_explanation"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating detailed explanation: {str(e)}"
        )


@router.post("/download-summary")
async def download_chat_summary(format: str = "txt") -> Dict[str, Any]:
    """
    Generate and download chat session summary
    
    Args:
        format: Download format ("txt" or "pdf")
    
    Returns:
        Summary content for download
    """
    try:
        from datetime import datetime
        pipeline = get_rag_pipeline()
        
        # Get chat memory
        chat_history = pipeline.chat_memory
        
        if not chat_history:
            return {
                "success": False,
                "error": "No chat history to summarize. Please have a conversation first.",
                "content": "## Chat Summary\n\nNo conversation history available.",
                "filename": f"empty_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "format": format
            }
        
        # Generate summary
        summary_lines = ["## Chat Summary\n"]
        
        # Add Q&A pairs
        for i, interaction in enumerate(chat_history, 1):
            summary_lines.append(f"Q{i}: {interaction['question']}")
            summary_lines.append(f"A{i}: {interaction['answer']}\n")
        
        # Extract key concepts (simple keyword extraction)
        all_text = " ".join([interaction['question'] + " " + interaction['answer'] for interaction in chat_history])
        
        # Common programming concepts to look for
        programming_concepts = [
            "Python", "Java", "C", "HTML", "CSS",
            "variables", "functions", "loops", "classes", "OOP",
            "data types", "syntax", "methods", "arrays", "strings"
        ]
        
        found_concepts = []
        for concept in programming_concepts:
            if concept.lower() in all_text.lower():
                found_concepts.append(concept)
        
        summary_lines.append("## Key Concepts")
        for concept in found_concepts:
            summary_lines.append(f"* {concept}")
        
        summary_content = "\n".join(summary_lines)
        
        # Generate filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_summary_{timestamp}.{format}"
        
        if format == "txt":
            return {
                "success": True,
                "content": summary_content,
                "filename": filename,
                "format": "txt"
            }
        elif format == "pdf":
            # For PDF, we'll return the content and let frontend handle PDF generation
            return {
                "success": True,
                "content": summary_content,
                "filename": filename,
                "format": "pdf",
                "note": "PDF generation should be handled on frontend"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported format. Use 'txt' or 'pdf'"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )


@router.post("/generate-summary", response_model=SummaryResponse)
async def generate_short_summary(request: SummaryRequest) -> Dict[str, Any]:
    """
    Generate a short 1-2 line summary based on user query
    
    Args:
        request: Summary request with query
        
    Returns:
        Short summary of the concept
    """
    try:
        pipeline = get_rag_pipeline()
        
        # Generate short summary using Groq
        prompt = f"Give a very short 1-2 line summary explaining the concept: {request.query}. Keep it simple and beginner-friendly."
        
        models = ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"]
        summary = None
        
        for model in models:
            try:
                response = pipeline.groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that provides short, simple explanations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=100  # Keep it short
                )
                summary = response.choices[0].message.content.strip()
                break
            except Exception as model_error:
                print(f"Groq Error with {model}:", str(model_error))
                continue
        
        if not summary:
            summary = "Unable to generate summary at this time."
        
        return {"summary": summary}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )
