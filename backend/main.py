import os
import traceback
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

import shutil
import tempfile

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Import database functions
from backend.database import init_db, save_conversation, get_conversations
from backend.agent import AgenticTutorSystem
from backend.routes.chat import router as chat_router
from backend.routes.upload import router as upload_router
from backend.tools.pdf_generator import PDFGenerator
from backend.utils.file_loader import FileLoader

# Define directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(title="VidMentor AI Chatbot")

# CORS — allow local dev + deployed frontend (set FRONTEND_URL / CORS_ORIGINS on Render)
def _cors_origins() -> List[str]:
    origins: List[str] = []
    frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
    if frontend_url:
        origins.append(frontend_url)
        # Also allow the netlify/vercel/onrender domain variations if provided
    
    extra = os.getenv("CORS_ORIGINS", "").strip()
    if extra:
        origins.extend(o.strip().rstrip("/") for o in extra.split(",") if o.strip())
    
    # Local development defaults
    origins.extend([
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ])
    
    # Check if we are in production
    is_prod = os.getenv("RENDER", "false").lower() == "true"
    
    if not is_prod or os.getenv("CORS_ALLOW_ALL", "").lower() in ("1", "true", "yes"):
        return ["*"]
        
    return list(dict.fromkeys(origins))


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents
ai_system = AgenticTutorSystem()

# Register API routers (must be before static file mount)
app.include_router(chat_router)
app.include_router(upload_router)

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"


class QuizRequest(BaseModel):
    topic: str
    level: str = "easy"


def _normalize_quiz_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        correct = q.get("correct_answer")
        if correct is None:
            correct = q.get("answer")
        normalized.append({
            "question": q.get("question") or q.get("q", ""),
            "options": q.get("options") or q.get("o", []),
            "correct_answer": correct,
            "explanation": q.get("explanation", ""),
        })
    return normalized

# Initialize DB on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("Database initialized successfully.")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "vidmentor-api"}


SERVE_STATIC = os.getenv("SERVE_STATIC", "true").lower() in ("1", "true", "yes")

# Root route — API info when static UI is disabled; otherwise serve index.html
@app.get("/")
async def serve_frontend():
    if not SERVE_STATIC:
        return {
            "service": "VidMentor AI API",
            "health": "/health",
            "docs": "/docs",
        }
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "Frontend not found at " + index_path}, status_code=404)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Check if the user is asking for a quiz (to maintain original agent flow if needed)
        # However, the frontend script.js handles "quiz on" by calling /quiz/generate
        # and standard chat by calling /chat/query.
        # This /chat endpoint seems to be a fallback or for the original non-RAG logic.
        
        # Process the input with the agentic system
        response = ai_system.process_input(request.message)
        
        # Extract response message for database storage
        ai_msg = response.get("message", "No response message.")
        topic = response.get("topic", "General")
        context = str(response.get("data", ""))
        
        # Save to SQLite database automatically
        save_conversation(
            session_id=request.session_id,
            subject=topic,
            user_message=request.message,
            ai_response=ai_msg,
            context_used=context
        )
        
        return response
    except Exception as e:
        print(f"Chat error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# History endpoint
@app.get("/history/{session_id}")
async def history_endpoint(session_id: str):
    try:
        history = get_conversations(session_id)
        # Format rows into dictionaries
        formatted_history = []
        for row in history:
            formatted_history.append({
                "id": row[0],
                "session_id": row[1],
                "subject": row[2],
                "user_message": row[3],
                "ai_response": row[4],
                "context_used": row[5],
                "timestamp": row[6]
            })
        return {"history": formatted_history}
    except Exception as e:
        print(f"History error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quiz/generate")
async def generate_quiz(request: QuizRequest):
    try:
        result = ai_system.quiz_gen.get_quiz(request.topic, request.level)
        if isinstance(result, dict) and result.get("type") == "non_technical_block":
            raise HTTPException(status_code=400, detail=result.get("response", "Non-technical topic"))
        questions = _normalize_quiz_questions(result if isinstance(result, list) else [])
        if not questions:
            raise HTTPException(status_code=500, detail="Failed to generate quiz questions")
        return {"questions": questions}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Quiz error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summary")
async def get_summary():
    return {"data": ai_system.summarizer.get_all()}


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    file_extension = os.path.splitext(file.filename or "")[1].lower()
    supported = FileLoader.get_supported_extensions()

    if file_extension not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types: {', '.join(supported)}",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_file_path = temp_file.name

    try:
        load_result = FileLoader.load_file(temp_file_path)
        if not load_result.get("success"):
            raise HTTPException(status_code=400, detail=load_result.get("error", "Failed to read resume"))

        text_parts = [chunk.get("text", "") for chunk in load_result.get("content", []) if chunk.get("text")]
        resume_text = "\n".join(text_parts).strip()
        if not resume_text:
            raise HTTPException(status_code=400, detail="No text content found in resume")

        analysis = ai_system.resume_analyzer.analyze(resume_text)
        return {"filename": file.filename, "analysis": analysis}
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@app.post("/report/download")
async def download_report(session_data: Dict[str, Any]):
    try:
        output_dir = os.path.join(BASE_DIR, "outputs")
        generator = PDFGenerator(output_dir=output_dir)
        result = generator.generate_learning_report(session_data)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "PDF generation failed"))
        return FileResponse(
            result["pdf_path"],
            media_type="application/pdf",
            filename=result["filename"],
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Report error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Mount frontend static files when serving UI from the API (disable on Render API-only service)
if SERVE_STATIC and os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENV", "development") == "development"
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
    )
