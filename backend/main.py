import os
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

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Root route to serve index.html
@app.get("/")
async def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "Frontend not found at " + index_path}, status_code=404)

# Chat endpoint
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
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
        raise HTTPException(status_code=500, detail=str(e))


# Mount frontend directory for static assets (js, css) — must be last
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
