"""
Agentic AI Learning Chatbot Core Logic
Implements a multi-agent system: Chat, Tutor, Career, Quiz, Summary, History, and Report agents.
"""
import os
import traceback
from typing import Dict, Any, List, Optional
import json
import os

def is_technical_query(query: str) -> bool:
    """Check if query is technical in nature"""
    technical_keywords = [
        "python", "java", "c++", "javascript", "react", "node", "api",
        "database", "sql", "machine learning", "ai", "data science",
        "algorithm", "ds", "os", "computer networks", "cloud",
        "coding", "programming", "development", "debug", "error",
        "engineering", "electronics", "mechanical", "civil",
        "iot", "robotics", "cybersecurity", "blockchain",
        "html", "css", "web", "frontend", "backend",
        "software", "hardware", "network", "security", "mobile",
        "app", "application", "system", "architecture",
        "framework", "library", "package", "module",
        "function", "method", "class", "object", "variable",
        "array", "list", "dictionary", "string", "integer",
        "float", "boolean", "loop", "condition", "statement",
        "git", "github", "version control", "testing", "deployment",
        "server", "client", "request", "response", "json", "xml",
        "docker", "kubernetes", "microservices", "rest", "graphql"
    ]
    
    query = query.lower()
    return any(word in query for word in technical_keywords)

class TutorAgent:
    """Agent responsible for explaining programming topics"""
    def __init__(self):
        self.knowledge = {
            "react": {
                "definition": "React is a powerful JavaScript library for building user interfaces, primarily for single-page applications.",
                "uses": ["Web development", "Mobile apps (React Native)", "UI components", "Dynamic dashboards"],
                "features": ["Component-based architecture", "Virtual DOM", "Declarative UI", "JSX", "Hooks"],
                "explanation": "React allows developers to create large web applications that can change data, without reloading the page. Its main goal is to be fast, scalable, and simple.",
                "relevance": "Most popular frontend library used by Meta, Netflix, and Airbnb."
            },
            "python": {
                "definition": "Python is a high-level, interpreted, general-purpose programming language known for its readability.",
                "uses": ["Data Science", "Web Development", "AI/ML", "Automation", "Scientific Computing"],
                "features": ["Easy syntax", "Dynamically typed", "Extensive libraries", "Interpreted", "Object-oriented"],
                "explanation": "Python's design philosophy emphasizes code readability with its use of significant indentation. Its language constructs as well as its object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects.",
                "relevance": "The primary language for AI, Machine Learning, and Data Science worldwide."
            },
            "java": {
                "definition": "Java is a high-level, class-based, object-oriented programming language designed to have as few implementation dependencies as possible.",
                "uses": ["Enterprise software", "Android apps", "Big Data", "Server-side applications"],
                "features": ["Platform independence", "Strong typing", "Multi-threading", "Robust memory management", "Secure"],
                "explanation": "Java is a 'Write Once, Run Anywhere' (WORA) language, meaning that compiled Java code can run on all platforms that support Java without the need for recompilation.",
                "relevance": "Backbone of most large-scale enterprise systems and Android ecosystem."
            },
            "html": {
                "definition": "HTML (HyperText Markup Language) is the standard markup language for documents designed to be displayed in a web browser.",
                "uses": ["Structuring web content", "Creating links", "Defining layout", "Embedding media"],
                "features": ["Tag-based structure", "Semantic elements", "Standardized", "Cross-browser support"],
                "explanation": "HTML provides the skeleton of a website. It uses various tags to define headings, paragraphs, links, images, and other content types.",
                "relevance": "The fundamental building block of the entire World Wide Web."
            },
            "css": {
                "definition": "CSS (Cascading Style Sheets) is a style sheet language used for describing the presentation of a document written in HTML.",
                "uses": ["Styling websites", "Layout design", "Animations", "Responsive design"],
                "features": ["Selectors", "Box model", "Flexbox/Grid", "Media queries", "Variables"],
                "explanation": "CSS is used to control the style of a web document in a simple and easy way. It handles the look and feel part of a web page.",
                "relevance": "Essential for creating modern, beautiful, and responsive user experiences."
            }
        }

    def get_info(self, topic: str) -> Optional[Dict[str, Any]]:
        topic = topic.lower().strip()
        return self.knowledge.get(topic)

class CareerAgent:
    """Agent responsible for suggesting learning roadmaps based on career goals"""
    def suggest_path(self, interest: str) -> Optional[Dict[str, Any]]:
        interest = interest.lower()
        if "web" in interest:
            return {
                "goal": "MERN Stack Developer",
                "roadmap": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Express", "MongoDB"]
            }
        elif "ai" in interest or "machine learning" in interest or "ml" in interest:
            return {
                "goal": "AI/ML Engineer",
                "roadmap": ["Python", "Mathematics", "Data Science (Pandas/NumPy)", "Machine Learning (Scikit-Learn)", "Deep Learning (PyTorch/TensorFlow)"]
            }
        return None

class QuizAgent:
    """Agent responsible for generating quizzes on demand"""
    def __init__(self):
        # Import Groq client for LLM-based quiz generation
        try:
            from groq import Groq
            self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.use_llm = True
        except ImportError:
            self.use_llm = False
            print("Groq not available, using fallback quizzes")
        
        # Fallback quizzes for when LLM fails
        self.fallback_quizzes = {
            "python": {
                "easy": [
                    {"question": "What is the correct extension for Python files?", "options": [".pt", ".py", ".pyt", ".pw"], "answer": 1, "explanation": "Python files use the .py extension."},
                    {"question": "How do you start a comment in Python?", "options": ["//", "/*", "#", "--"], "answer": 2, "explanation": "Python uses the # symbol for single-line comments."},
                    {"question": "Which of these is a Python data type?", "options": ["List", "Object", "Component", "Tag"], "answer": 0, "explanation": "List is a built-in Python data type."},
                    {"question": "What does 'pip' stand for?", "options": ["Pip Installs Packages", "Python Install Program", "Preferred Install Package", "Point In Place"], "answer": 0, "explanation": "Pip stands for 'Pip Installs Packages'."},
                    {"question": "Which function is used to output text?", "options": ["echo()", "console.log()", "print()", "write()"], "answer": 2, "explanation": "print() is used to output text in Python."}
                ],
                "medium": [
                    {"question": "Which data type is immutable?", "options": ["List", "Dictionary", "Set", "Tuple"], "answer": 3, "explanation": "Tuple is immutable in Python."},
                    {"question": "What is a lambda function?", "options": ["A recursive function", "An anonymous function", "A global function", "A private function"], "answer": 1, "explanation": "Lambda functions are anonymous functions in Python."},
                    {"question": "How do you create a virtual environment?", "options": ["python -m venv venv", "npm install venv", "pip install env", "python create env"], "answer": 0, "explanation": "Use 'python -m venv venv' to create a virtual environment."},
                    {"question": "What is __init__ in Python?", "options": ["A destructor", "A constructor", "A decorator", "A module"], "answer": 1, "explanation": "__init__ is a constructor method in Python classes."},
                    {"question": "Which library is used for Data Science?", "options": ["React", "Pandas", "Express", "Tailwind"], "answer": 1, "explanation": "Pandas is widely used for Data Science in Python."}
                ],
                "hard": [
                    {"question": "What is the Global Interpreter Lock (GIL)?", "options": ["A thread synchronization mechanism", "A memory management tool", "A security feature", "A debugging tool"], "answer": 0, "explanation": "The GIL is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecode at the same time."},
                    {"question": "What is the difference between __str__ and __repr__?", "options": ["No difference", "__str__ is for users, __repr__ is for developers", "__str__ is faster", "__repr__ is for printing"], "answer": 1, "explanation": "__str__ returns a user-friendly string representation, while __repr__ returns an unambiguous developer representation."},
                    {"question": "What is metaprogramming in Python?", "options": ["Writing programs about programs", "Programming with metadata", "Creating meta data", "Programming at a higher level"], "answer": 0, "explanation": "Metaprogramming involves writing code that manipulates other code as data."},
                    {"question": "What is the MRO in Python?", "options": ["Method Resolution Order", "Memory Reference Object", "Multiple Return Object", "Meta Runtime Object"], "answer": 0, "explanation": "MRO stands for Method Resolution Order, which determines the order in which base classes are searched when looking for methods."},
                    {"question": "What is the difference between shallow and deep copy?", "options": ["No difference", "Shallow copy copies references, deep copy copies objects", "Deep copy is faster", "Shallow copy is more memory efficient"], "answer": 1, "explanation": "Shallow copy copies object references, while deep copy creates new copies of all objects found within the original."}
                ]
            },
            "java": {
                "easy": [
                    {"question": "What is the extension of Java files?", "options": [".js", ".jv", ".java", ".ja"], "answer": 2, "explanation": "Java files use the .java extension."},
                    {"question": "Which company developed Java?", "options": ["Microsoft", "Sun Microsystems", "Google", "Apple"], "answer": 1, "explanation": "Java was developed by Sun Microsystems, now owned by Oracle."},
                    {"question": "What is the entry point of a Java program?", "options": ["start()", "main()", "init()", "run()"], "answer": 1, "explanation": "The main() method is the entry point of a Java program."},
                    {"question": "Which keyword is used to create an object?", "options": ["make", "create", "new", "init"], "answer": 2, "explanation": "The 'new' keyword is used to create objects in Java."},
                    {"question": "Is Java platform-independent?", "options": ["Yes", "No", "Depends on OS", "Only on Windows"], "answer": 0, "explanation": "Java is platform-independent due to its 'Write Once, Run Anywhere' nature."}
                ],
                "medium": [
                    {"question": "What is polymorphism in Java?", "options": ["Multiple inheritance", "Method overloading/overriding", "Memory management", "Type safety"], "answer": 1, "explanation": "Polymorphism allows method overloading and overriding in Java."},
                    {"question": "What is the difference between ArrayList and LinkedList?", "options": ["No difference", "ArrayList uses array, LinkedList uses nodes", "LinkedList is faster", "ArrayList uses linked list"], "answer": 1, "explanation": "ArrayList uses a dynamic array, while LinkedList uses a doubly-linked list."},
                    {"question": "What is the purpose of the 'final' keyword?", "options": ["To end a program", "To make constants", "To finalize methods", "To stop inheritance"], "answer": 1, "explanation": "The 'final' keyword is used to create constants in Java."},
                    {"question": "What is an interface in Java?", "options": ["A concrete class", "An abstract type with method signatures", "A data structure", "A design pattern"], "answer": 1, "explanation": "An interface is an abstract type that contains method signatures."},
                    {"question": "What is garbage collection in Java?", "options": ["Manual memory management", "Automatic memory management", "Data cleanup", "Code optimization"], "answer": 1, "explanation": "Garbage collection is the automatic process of reclaiming memory."}
                ],
                "hard": [
                    {"question": "What is the Java Memory Model?", "options": ["Memory layout", "Thread synchronization rules", "Memory allocation", "Garbage collection"], "answer": 1, "explanation": "The Java Memory Model defines the rules for how threads interact through memory."},
                    {"question": "What is the difference between == and equals()?", "options": ["No difference", "== compares references, equals() compares values", "== is faster", "equals() is for primitives"], "answer": 1, "explanation": "== compares object references, while equals() compares object values."},
                    {"question": "What is a Java Stream?", "options": ["File I/O stream", "A sequence of elements for functional operations", "Network stream", "Data stream"], "answer": 1, "explanation": "Java Stream is a sequence of elements that supports functional operations."},
                    {"question": "What is the difference between checked and unchecked exceptions?", "options": ["No difference", "Checked must be handled, unchecked don't have to", "Checked are runtime, unchecked are compile-time", "Unchecked are more serious"], "answer": 1, "explanation": "Checked exceptions must be handled or declared, while unchecked exceptions don't require handling."},
                    {"question": "What is the purpose of the volatile keyword?", "options": ["To make variables constant", "To ensure visibility across threads", "To optimize performance", "To prevent inheritance"], "answer": 1, "explanation": "The volatile keyword ensures that changes to a variable are immediately visible to other threads."}
                ]
            }
        }

    def get_quiz(self, topic: str, level: str = "easy") -> List[Dict[str, Any]]:
        """Generate quiz questions using LLM with fallback to hardcoded quizzes"""
        topic = topic.lower()
        level = level.lower()
        
        # Technical query filter - check if topic is technical
        if not is_technical_query(topic):
            return {
                "type": "non_technical_block",
                "response": "I am an AI Tutor for technical knowledge (programming, engineering, and technology). Please ask a technical topic for quiz generation.",
                "questions": []
            }
        
        # Try LLM generation first
        if self.use_llm:
            try:
                questions = self._generate_quiz_with_llm(topic, level)
                if self._validate_quiz(questions):
                    print(f"✅ Successfully generated {len(questions)} quiz questions for {topic} ({level})")
                    return questions
                else:
                    print(f"❌ LLM quiz validation failed for {topic} ({level}), using fallback")
            except Exception as e:
                print(f"❌ LLM quiz generation failed for {topic} ({level}): {str(e)}")
        
        # Use fallback quizzes
        print(f"📚 Using fallback quiz for {topic} ({level})")
        return self._get_fallback_quiz(topic, level)

    def _generate_quiz_with_llm(self, topic: str, level: str) -> List[Dict[str, Any]]:
        """Generate quiz using Groq LLM with strict JSON output"""
        
        # Force structured JSON output prompt
        prompt = f"""Generate exactly 5 multiple choice questions on {topic} with {level} level.

Return ONLY valid JSON in this exact format:

{{
"questions": [
{{
"question": "string",
"options": ["A", "B", "C", "D"],
"answer": "A",
"explanation": "string"
}}
]
}}

Rules:
- Exactly 5 questions
- 4 options each
- One correct answer (A, B, C, or D)
- No extra text outside JSON
- Valid JSON only"""

        try:
            models = ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"]
            
            for model in models:
                try:
                    response = self.groq_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a strict AI Tutor. You ONLY answer technical questions related to programming, engineering, and technology. If the user asks anything non-technical (food, movies, general topics), you MUST refuse and say: 'I am an AI Tutor for technical knowledge. Please ask a technical question.' Do not explain non-technical topics."},
                            {"role": "system", "content": "You are a quiz generator that always returns valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1500
                    )
                    
                    raw_response = response.choices[0].message.content.strip()
                    print(f"🔍 Raw LLM response for {topic} ({level}): {raw_response[:100]}...")
                    
                    # Parse JSON safely
                    data = json.loads(raw_response)
                    
                    if "questions" in data and isinstance(data["questions"], list):
                        # Convert to frontend format
                        formatted_questions = []
                        for q in data["questions"]:
                            formatted_q = {
                                "question": q["question"],
                                "options": q["options"],
                                "correct_answer": ord(q["answer"]) - ord('A'),  # Convert A/B/C/D to 0/1/2/3
                                "explanation": q.get("explanation", "No explanation available.")
                            }
                            formatted_questions.append(formatted_q)
                        
                        return formatted_questions
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error with {model}: {str(e)}")
                    continue
                except Exception as e:
                    print(f"❌ Model {model} error: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"CRITICAL Agent Error: {str(e)}")
            traceback.print_exc()
            return {
                "type": "error",
                "message": f"AI service error: {type(e).__name__}. Please check backend logs.",
                "data": None
            }

    def _validate_quiz(self, questions: List[Dict[str, Any]]) -> bool:
        """Validate quiz structure"""
        if not isinstance(questions, list) or len(questions) != 5:
            return False
        
        for q in questions:
            if not isinstance(q, dict):
                return False
            if not all(key in q for key in ["question", "options", "correct_answer", "explanation"]):
                return False
            if not isinstance(q["options"], list) or len(q["options"]) != 4:
                return False
            if not isinstance(q["correct_answer"], int) or q["correct_answer"] < 0 or q["correct_answer"] > 3:
                return False
        
        return True

    def _get_fallback_quiz(self, topic: str, level: str) -> List[Dict[str, Any]]:
        """Get fallback quiz for topic and level"""
        # Try exact topic match
        if topic in self.fallback_quizzes and level in self.fallback_quizzes[topic]:
            return self.fallback_quizzes[topic][level]
        
        # Try Python as default
        if "python" in self.fallback_quizzes and level in self.fallback_quizzes["python"]:
            return self.fallback_quizzes["python"][level]
        
        # Final fallback - Python easy
        return self.fallback_quizzes["python"]["easy"]

class ResumeAnalysisAgent:
    """Agent responsible for analyzing resumes and providing feedback"""
    def analyze(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        # Simple rule-based analysis
        summary = "Resume successfully analyzed. Found key sections including experience and education."
        
        # Skill analysis
        frontend_skills = ["html", "css", "javascript", "react", "vue", "angular", "tailwind"]
        backend_skills = ["python", "java", "node", "express", "mongodb", "sql", "postgresql", "django", "flask"]
        
        found_frontend = [s for s in frontend_skills if s in text_lower]
        found_backend = [s for s in backend_skills if s in text_lower]
        
        tech_score = min(100, (len(found_frontend) + len(found_backend)) * 15)
        creativity_score = 70 if "design" in text_lower or "creative" in text_lower else 50
        
        missing_skills = []
        if tech_score < 60:
            if len(found_frontend) < len(found_backend):
                missing_skills = ["React", "Advanced CSS", "JavaScript ES6+"]
            else:
                missing_skills = ["Node.js", "Database Management", "System Design"]
        
        suggestions = [
            "Quantify your achievements with metrics.",
            "Include a professional summary at the top.",
            "Ensure your technical skills match the target job description."
        ]
        
        roadmap = []
        if len(found_frontend) < 3:
            roadmap = ["HTML/CSS Mastery", "JavaScript Deep Dive", "React Framework Basics"]
        elif len(found_backend) < 3:
            roadmap = ["Python/Node.js Fundamentals", "REST API Development", "Database Schema Design"]
        else:
            roadmap = ["Cloud Deployment (AWS/Azure)", "Docker & Kubernetes", "Microservices Architecture"]
            
        return {
            "summary": summary,
            "skill_analysis": f"Detected {len(found_frontend)} frontend skills and {len(found_backend)} backend skills.",
            "creativity_score": creativity_score,
            "technical_score": tech_score,
            "missing_skills": missing_skills,
            "suggestions": suggestions,
            "tips": "Tailor your resume for each application to pass ATS filters.",
            "roadmap": roadmap
        }

class SummaryAgent:
    """Agent responsible for updating the real-time summary panel"""
    def __init__(self):
        self.session_summary = []

    def update(self, topic: str, data: Dict[str, Any]):
        # Avoid duplicate topics in summary
        if not any(item['topic'] == topic for item in self.session_summary):
            self.session_summary.append({
                "topic": topic.capitalize(),
                "definition": data.get("definition"),
                "key_points": data.get("features", [])[:3],
                "concepts": [data.get("relevance")]
            })

    def get_all(self):
        return self.session_summary


# creates all agents
class AgenticTutorSystem: 
    """Main Orchestrator for the Agentic AI system"""
    def __init__(self):
        self.tutor = TutorAgent()
        self.career = CareerAgent()
        self.quiz_gen = QuizAgent()
        self.summarizer = SummaryAgent()
        self.resume_analyzer = ResumeAnalysisAgent()
        self.chat_history = []

    def process_input(self, user_input: str) -> Dict[str, Any]:
        text = user_input.lower()
        response = {"type": "chat", "message": "", "data": None}
        
        # Technical query filter - check if query is technical
        if not is_technical_query(user_input):
            return {
                "type": "non_technical_block",
                "message": "I am an AI Tutor for technical knowledge (programming, engineering, and technology). Please ask a technical question.",
                "data": None
            }
        
        # 1. Intent Detection
        # Check for Quiz request
        if "quiz" in text:
            topic = "python" # default
            for t in ["react", "java", "html", "css", "python"]:
                if t in text:
                    topic = t
                    break
            response["type"] = "quiz_request"
            response["topic"] = topic
            response["message"] = f"I've detected you want a quiz on {topic.capitalize()}. Please select a difficulty level."
            return response

        # Check for Career interest
        if "interested in" in text or "want to build" in text or "career" in text:
            career_path = self.career.suggest_path(text)
            if career_path:
                response["type"] = "career"
                response["data"] = career_path
                response["message"] = f"Based on your interest, here is a professional roadmap to become a {career_path['goal']}:"
                return response

        # Check for Learning topic
        for topic in ["react", "python", "java", "html", "css"]:
            if topic in text:
                info = self.tutor.get_info(topic)
                if info:
                    self.summarizer.update(topic, info)
                    response["type"] = "learning"
                    response["topic"] = topic
                    response["data"] = info
                    response["message"] = f"Here is what I found about {topic.capitalize()}:"
                    return response

        # Default Chat Response
        response["message"] = "I'm your AI Learning Assistant. You can ask me about programming topics (React, Python, Java, etc.), request a quiz, or ask for career guidance."
        return response
