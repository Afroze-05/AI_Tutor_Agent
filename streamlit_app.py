import streamlit as st
import requests
import os
import json
import time
from typing import List, Dict, Any, Optional

# --- Configuration ---
BACKEND_URL = st.sidebar.text_input(
    "Backend URL", 
    value=os.getenv("BACKEND_URL", "http://localhost:8000"),
    help="Enter the URL of your deployed FastAPI backend (e.g., https://your-backend.onrender.com)"
)

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if "quiz_state" not in st.session_state:
    st.session_state.quiz_state = None

# --- Page Config ---
st.set_page_config(
    page_title="VidMentor AI Tutor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Styles ---
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #6366f1;
        color: white;
    }
    .stTextInput>div>div>input {
        background-color: #1e293b;
        color: #f8fafc;
    }
    .bot-msg {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        border-left: 4px solid #6366f1;
    }
    .user-msg {
        background-color: #334155;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        text-align: right;
        border-right: 4px solid #10b981;
    }
    .source-tag {
        font-size: 0.8rem;
        background: rgba(99, 102, 241, 0.2);
        padding: 2px 8px;
        border-radius: 4px;
        margin-right: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("🤖 AI Tutor Agent")
    st.markdown("---")
    
    st.subheader("📁 Learning Documents")
    uploaded_file = st.file_uploader("Upload PDF/Doc for RAG", type=["pdf", "docx", "txt"])
    if uploaded_file:
        if st.button("Process Document"):
            with st.spinner("Analyzing document..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                try:
                    res = requests.post(f"{BACKEND_URL}/upload/document", files=files)
                    if res.status_code == 200:
                        st.success(f"Processed: {uploaded_file.name}")
                    else:
                        st.error("Failed to process document")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.quiz_state = None
        st.rerun()

    st.subheader("📊 System Status")
    try:
        health = requests.get(f"{BACKEND_URL}/health").json()
        if health.get("status") == "ok":
            st.success("Backend Online")
    except:
        st.error("Backend Offline")

# --- Chat Logic ---
def chat_with_agent(message: str):
    payload = {
        "message": message,
        "session_id": st.session_state.session_id,
        "use_rag": True,
        "top_k": 3
    }
    try:
        # We try the RAG endpoint first as it's the most advanced
        res = requests.post(f"{BACKEND_URL}/chat/query", json=payload)
        if res.status_code == 200:
            return res.json()
        
        # Fallback to standard agent chat if RAG endpoint is not available or fails
        res = requests.post(f"{BACKEND_URL}/chat", json=payload)
        return res.json()
    except Exception as e:
        return {"answer": f"Connection Error: {str(e)}", "sources": []}

# --- Quiz Interface ---
def start_quiz(topic: str, level: str):
    try:
        res = requests.post(f"{BACKEND_URL}/quiz/generate", json={"topic": topic, "level": level})
        if res.status_code == 200:
            st.session_state.quiz_state = {
                "questions": res.json()["questions"],
                "current_idx": 0,
                "score": 0,
                "topic": topic
            }
            st.rerun()
        else:
            st.error("Could not generate quiz")
    except Exception as e:
        st.error(f"Error: {e}")

# --- Main UI ---
st.title("🎓 VidMentor AI Learning Assistant")
st.caption("Technical AI Tutor specializing in Programming, AI, and CS")

# Display Quiz if active
if st.session_state.quiz_state:
    quiz = st.session_state.quiz_state
    if quiz["current_idx"] < len(quiz["questions"]):
        q = quiz["questions"][quiz["current_idx"]]
        st.info(f"**Quiz: {quiz['topic'].capitalize()}**")
        st.write(f"Question {quiz['current_idx']+1} of {len(quiz['questions'])}")
        st.subheader(q["question"])
        
        # Options
        ans = st.radio("Choose your answer:", q["options"], key=f"q_{quiz['current_idx']}")
        if st.button("Submit Answer"):
            correct_idx = q["correct_answer"]
            # Convert A/B/C/D if needed, but here it's index
            if q["options"].index(ans) == correct_idx:
                st.success("Correct! 🎉")
                st.session_state.quiz_state["score"] += 1
            else:
                st.error(f"Incorrect. The correct answer was: {q['options'][correct_idx]}")
                if q.get("explanation"):
                    st.write(f"💡 {q['explanation']}")
            
            time.sleep(2)
            st.session_state.quiz_state["current_idx"] += 1
            st.rerun()
    else:
        st.balloons()
        st.success(f"Quiz Completed! Your Score: {quiz['score']} / {len(quiz['questions'])}")
        if st.button("Return to Chat"):
            st.session_state.quiz_state = None
            st.rerun()
    st.stop()

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 View Sources"):
                for s in msg["sources"]:
                    st.markdown(f"- **{s['filename']}**: {s['text'][:200]}...")

# Chat Input
if prompt := st.chat_input("Ask me about Python, React, AI, or type 'quiz on [topic]'"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Check for quiz command
    if prompt.lower().startswith("quiz on "):
        topic = prompt.lower().replace("quiz on ", "").strip()
        st.info(f"Generating quiz on {topic}...")
        col1, col2, col3 = st.columns(3)
        if col1.button("Easy"): start_quiz(topic, "easy")
        if col2.button("Medium"): start_quiz(topic, "medium")
        if col3.button("Hard"): start_quiz(topic, "hard")
    else:
        # Normal Chat
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                data = chat_with_agent(prompt)
                
                # Check for technical block
                if data.get("type") == "non_technical_block":
                    answer = data.get("message")
                    sources = []
                else:
                    answer = data.get("answer") or data.get("message")
                    sources = data.get("sources", [])
                
                st.markdown(answer)
                if sources:
                    with st.expander("📚 View Sources"):
                        for s in sources:
                            st.markdown(f"- **{s['filename']}**: {s['text'][:200]}...")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources
                })
