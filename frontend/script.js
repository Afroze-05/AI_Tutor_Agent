const API_BASE = window.API_BASE || "http://127.0.0.1:8000";

// Elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const loader = document.getElementById('loader');
const clearChatBtn = document.getElementById('clearChatBtn');
const historyContainer = document.getElementById('historyContainer');
const summaryList = document.getElementById('summaryList');
const quizArea = document.getElementById('quizArea');
const resumeAnalysisArea = document.getElementById('resumeAnalysisArea');
const resumeUpload = document.getElementById('resumeUpload');
const downloadBtn = document.getElementById('downloadBtn');
const newChatBtn = document.getElementById('newChatBtn');

// RAG Elements
const documentUpload = document.getElementById('documentUpload');
const documentList = document.getElementById('documentList');
const clearDocumentsBtn = document.getElementById('clearDocumentsBtn');

// Chat Summary Download Elements
const downloadChatTxt = document.getElementById('downloadChatTxt');
const downloadChatPdf = document.getElementById('downloadChatPdf');

// State
let sessionData = {
    chats: [],
    currentChatId: null,
    summary: [],
    quizzes: [],
    careerPath: null,
    resumeAnalysis: null
};

// --- Initialization ---
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.onclick = () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`${btn.dataset.tab}Tab`).classList.add('active');
    };
});

// --- Helpers ---
const showLoader = () => loader.classList.remove('hidden');
const hideLoader = () => loader.classList.add('hidden');

function appendMessage(role, content, isHtml = false, sources = []) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;
    
    let messageContent = content;
    
    // Parse Markdown for bot messages
    if (role === 'bot' && !isHtml) {
        messageContent = parseMarkdown(content);
        isHtml = true;
    }
    
    // Add sources section if available
    if (sources && sources.length > 0) {
        messageContent += `<div class="sources-section" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 0.8rem; color: var(--accent-purple); margin-bottom: 8px;">📚 Sources:</div>
            ${sources.map((source, i) => `
                <div class="source-item" style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 4px; padding: 4px 8px; background: rgba(147,51,234,0.1); border-radius: 4px;">
                    <strong>${source.filename}</strong> (${source.location}) - Score: ${source.score}
                </div>
            `).join('')}
        </div>`;
    }
    
    if (isHtml) {
        msgDiv.innerHTML = `<div class="msg-content">${messageContent}</div>`;
    } else {
        msgDiv.textContent = content;
    }
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Add to current chat
    if (role === 'user' || role === 'bot') {
        const currentChat = getCurrentChat();
        currentChat.messages.push({ role, content, isHtml, sources });
        updateHistoryPanel();
        updatePdfButtonState();
    }
}

function parseMarkdown(text) {
    if (typeof marked !== 'undefined') {
        // Use marked.js for proper Markdown parsing
        let html = marked.parse(text);
        
        // Add custom styling for emoji headers
        html = html.replace(/^(🔷|🟢|🟣|🟡|🔴)\s+(.+)$/gm, '<div class="emoji-section">$1 $2</div>');
        
        // Add color classes to keywords
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="keyword-green">$1</strong>');
        
        return html;
    } else {
        // Fallback basic parsing if marked.js not loaded
        return text
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/`(.+?)`/g, '<code>$1</code>')
            .replace(/```python\n([\s\S]+?)```/g, '<pre><code class="python">$1</code></pre>')
            .replace(/---/g, '<hr>')
            .replace(/^\* (.+)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            .replace(/^(🔷|🟢|🟣|🟡|🔴)\s+(.+)$/gm, '<div class="emoji-section">$1 $2</div>');
    }
}

// --- Chat Management ---
function createNewChat() {
    const newChatId = 'chat_' + Date.now();
    const newChat = {
        id: newChatId,
        title: 'New Chat',
        messages: [],
        createdAt: new Date().toISOString()
    };
    
    sessionData.chats.push(newChat);
    sessionData.currentChatId = newChatId;
    
    // Clear chat window
    chatMessages.innerHTML = '';
    
    updateHistoryPanel();
    return newChatId;
}

function switchToChat(chatId) {
    sessionData.currentChatId = chatId;
    const chat = sessionData.chats.find(c => c.id === chatId);
    
    if (chat) {
        // Clear current chat window
        chatMessages.innerHTML = '';
        
        // Load chat messages
        chat.messages.forEach(msg => {
            appendMessage(msg.role, msg.content, msg.isHtml || false, msg.sources || []);
        });
    }
}

function getCurrentChat() {
    if (!sessionData.currentChatId) {
        return createNewChat();
    }
    return sessionData.chats.find(c => c.id === sessionData.currentChatId);
}

function updateChatTitle(chatId, message) {
    const chat = sessionData.chats.find(c => c.id === chatId);
    if (chat && chat.title === 'New Chat') {
        // Take first 3-5 words, remove extra spaces, capitalize properly
        const words = message.trim().split(/\s+/).slice(0, 5);
        const title = words.map(word => 
            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        ).join(' ');
        
        chat.title = title.length > 30 ? title.substring(0, 27) + '...' : title;
        updateHistoryPanel();
    }
}

// --- Chat Logic ---
async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Check for quiz intent
    const quizMatch = text.match(/quiz\s+on\s+(.+)/i);
    if (quizMatch) {
        const topic = quizMatch[1].trim();
        await startQuizFlow(topic);
        return;
    }

    // Ensure we have a current chat
    const currentChat = getCurrentChat();
    
    // Check if this is the first user message
    const isFirstMessage = currentChat.messages.length === 0;

    appendMessage('user', text);
    userInput.value = "";
    showLoader();
    
    // Update chat title after message is added
    if (isFirstMessage) {
        updateChatTitle(currentChat.id, text);
    }

    // Generate short summary
    await generateAndUpdateSummary(text);

    try {
        const response = await fetch(`${API_BASE}/chat/query`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text, use_rag: true, top_k: 3})
        });
        const data = await response.json();
        
        if (data.answer) {
            appendMessage('bot', data.answer, false, data.sources || []);
        } else {
            appendMessage('bot', 'Sorry, I couldn\'t process your request.');
        }
    } catch (e) {
        appendMessage('bot', 'Connection error. Please try again.');
    } finally {
        hideLoader();
    }
}

// --- Enhanced Quiz System ---
async function startQuizFlow(topic) {
    const currentChat = getCurrentChat();
    
    // Store quiz state
    currentChat.quizState = {
        topic: topic,
        level: null,
        questions: [],
        currentIndex: 0,
        score: 0,
        isActive: true
    };

    // Show difficulty selection in chat
    appendMessage('user', `quiz on ${topic}`);
    
    const difficultyButtons = `
        <div style="margin: 12px 0;">
            <p>Select difficulty level:</p>
            <div style="display: flex; gap: 8px; margin: 8px 0;">
                <button onclick="selectQuizDifficulty('easy')" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">Easy</button>
                <button onclick="selectQuizDifficulty('medium')" style="background: #f59e0b; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">Medium</button>
                <button onclick="selectQuizDifficulty('hard')" style="background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">Hard</button>
            </div>
        </div>
    `;
    
    appendMessage('bot', difficultyButtons, true);
}

async function selectQuizDifficulty(level) {
    const currentChat = getCurrentChat();
    if (!currentChat.quizState) return;
    
    currentChat.quizState.level = level;
    
    // Show loading message
    appendMessage('bot', `Generating ${level} quiz on ${currentChat.quizState.topic}...`, false);
    
    // Generate quiz
    try {
        const response = await fetch(`${API_BASE}/quiz/generate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({topic: currentChat.quizState.topic, level: level})
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Validate response structure
        if (!data || !data.questions || !Array.isArray(data.questions) || data.questions.length === 0) {
            throw new Error('Invalid quiz data received');
        }
        
        // Take exactly 5 questions
        currentChat.quizState.questions = data.questions.slice(0, 5);
        currentChat.quizState.currentIndex = 0;
        currentChat.quizState.score = 0;
        
        // Validate each question
        for (let i = 0; i < currentChat.quizState.questions.length; i++) {
            const q = currentChat.quizState.questions[i];
            if (!q.question || !q.options || !Array.isArray(q.options) || q.options.length !== 4) {
                throw new Error(`Invalid question structure at index ${i}`);
            }
        }
        
        // Show first question in quiz section
        showQuizQuestion();
        
        // Update chat to show quiz started
        appendMessage('bot', `✅ Starting ${level} quiz on ${currentChat.quizState.topic}! Check the Quiz tab.`, false);
        
    } catch (e) {
        console.error('Quiz generation error:', e);
        appendMessage('bot', `❌ Failed to generate quiz: ${e.message}. Please try again or choose a different topic.`, false);
        
        // Clear quiz state on error
        currentChat.quizState = null;
        
        // Reset quiz area
        const quizArea = document.getElementById('quizArea');
        quizArea.innerHTML = '<p class="empty-text">Start a quiz by typing "quiz on [topic]"</p>';
    }
}

function showQuizQuestion() {
    const currentChat = getCurrentChat();
    if (!currentChat.quizState) return;
    
    const { questions, currentIndex, score } = currentChat.quizState;
    if (currentIndex >= questions.length) {
        showQuizResult();
        return;
    }
    
    const question = questions[currentIndex];
    const quizArea = document.getElementById('quizArea');
    
    quizArea.innerHTML = `
        <div class="quiz-container">
            <h3>Q${currentIndex + 1}: ${question.question}</h3>
            <div class="quiz-options">
                ${question.options.map((option, index) => `
                    <div class="quiz-option" id="option-${index}" onclick="selectAnswer(${index})">
                        ${String.fromCharCode(65 + index)}. ${option}
                    </div>
                `).join('')}
            </div>
            <div class="quiz-progress">
                Question ${currentIndex + 1} of ${questions.length} | Score: ${score}/${currentIndex}
            </div>
        </div>
    `;
}

async function selectAnswer(selectedIndex) {
    const currentChat = getCurrentChat();
    if (!currentChat.quizState) return;
    
    const { questions, currentIndex } = currentChat.quizState;
    const question = questions[currentIndex];
    const isCorrect = selectedIndex === question.correct_answer;
    
    // Update score
    if (isCorrect) {
        currentChat.quizState.score++;
    }
    
    // Show feedback
    const options = document.querySelectorAll('.quiz-option');
    options.forEach((option, index) => {
        option.onclick = null; // Disable clicking
        if (index === selectedIndex) {
            option.style.backgroundColor = isCorrect ? '#10b981' : '#ef4444';
            option.style.color = 'white';
        }
        if (index === question.correct_answer) {
            option.style.backgroundColor = '#10b981';
            option.style.color = 'white';
        }
    });
    
    // Send explanation for wrong answers
    if (!isCorrect && question.explanation) {
        setTimeout(() => {
            appendMessage('bot', `💡 Explanation: ${question.explanation}`, false);
        }, 1000);
    }
    
    // Move to next question after delay
    setTimeout(() => {
        currentChat.quizState.currentIndex++;
        showQuizQuestion();
    }, 2000);
}

function showQuizResult() {
    const currentChat = getCurrentChat();
    if (!currentChat.quizState) return;
    
    const { score, questions, topic, level } = currentChat.quizState;
    const percentage = Math.round((score / questions.length) * 100);
    
    let feedback = '';
    if (percentage >= 80) {
        feedback = 'Excellent work! You have a strong understanding of this topic.';
    } else if (percentage >= 60) {
        feedback = 'Good job! Consider reviewing the concepts you missed.';
    } else {
        feedback = 'Keep practicing! Focus on the fundamental concepts.';
    }
    
    const quizArea = document.getElementById('quizArea');
    quizArea.innerHTML = `
        <div class="quiz-result">
            <h3>🎯 Quiz Completed!</h3>
            <div class="score-display">
                <div class="score-number">${score} / ${questions.length}</div>
                <div class="score-percentage">${percentage}%</div>
            </div>
            <p class="feedback">${feedback}</p>
            <button onclick="resetQuiz()" class="primary-btn">Take Another Quiz</button>
        </div>
    `;
    
    // Send result to chat
    appendMessage('bot', `Quiz completed! Your score: ${score}/${questions.length} (${percentage}%). ${feedback}`, false);
    
    // Clear quiz state
    currentChat.quizState = null;
}

function resetQuiz() {
    const currentChat = getCurrentChat();
    currentChat.quizState = null;
    
    const quizArea = document.getElementById('quizArea');
    quizArea.innerHTML = '<p class="empty-text">Start a quiz by typing "quiz on [topic]"</p>';
}

// --- Summary Generation ---
async function generateAndUpdateSummary(query) {
    try {
        const response = await fetch(`${API_BASE}/chat/generate-summary`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: query})
        });
        const data = await response.json();
        
        if (data.summary) {
            updateSummaryDisplay(data.summary);
        }
    } catch (e) {
        console.error('Error generating summary:', e);
    }
}

function updateSummaryDisplay(summary) {
    // Update summary in the summary section
    const summaryContent = document.getElementById('summaryList');
    if (summaryContent) {
        summaryContent.innerHTML = `
            <div class="summary-item" style="background: rgba(147,51,234,0.1); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                <p style="margin: 0; color: var(--text-primary);">${summary}</p>
            </div>
        `;
        // Store summary in current chat for PDF generation
        const currentChat = getCurrentChat();
        if (currentChat) {
            currentChat.summary = summary;
        }
        // Update PDF button state when summary is added
        updatePdfButtonState();
    }
}

function handleRAGResponse(res) {
    // Handle RAG response with sources
    if (res.answer) {
        appendMessage('bot', res.answer, false, res.sources || []);
        
        // Update UI elements
        updateSummaryPanel();
        downloadBtn.disabled = false;
    } else {
        appendMessage('bot', 'Sorry, I could not process your request.');
    }
}

function handleAIResponse(res) {
    if (res.type === 'learning') {
        const info = res.data;
        const html = `
            <p><strong>${res.topic.toUpperCase()}</strong></p>
            <p style="margin-top:8px;">${info.definition}</p>
            <div style="margin-top:12px;">
                <p><strong>Key Features:</strong></p>
                <ul style="padding-left:20px; margin-top:5px;">
                    ${info.features.map(f => `<li>${f}</li>`).join('')}
                </ul>
            </div>
            <p style="margin-top:12px;"><strong>Real-world Relevance:</strong> ${info.relevance}</p>
        `;
        appendMessage('bot', html, true);
        updateSummaryPanel();
        downloadBtn.disabled = false;
    } 
    else if (res.type === 'career') {
        sessionData.careerPath = res.data;
        const html = `
            <p><strong>${res.message}</strong></p>
            <div style="margin-top:10px; display:flex; flex-direction:column; gap:8px;">
                ${res.data.roadmap.map((step, i) => `
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="width:24px; height:24px; background:var(--accent-purple); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.7rem;">${i+1}</span>
                        <span>${step}</span>
                    </div>
                `).join('')}
            </div>
        `;
        appendMessage('bot', html, true);
    }
    else if (res.type === 'quiz_request') {
        const html = `
            <p>${res.message}</p>
            <div style="margin-top:12px; display:flex; gap:10px;">
                <button class="action-link" style="background:rgba(255,255,255,0.05); padding:8px 15px; border-radius:6px;" onclick="generateQuiz('${res.topic}', 'easy')">Easy</button>
                <button class="action-link" style="background:rgba(255,255,255,0.05); padding:8px 15px; border-radius:6px;" onclick="generateQuiz('${res.topic}', 'medium')">Medium</button>
                <button class="action-link" style="background:rgba(255,255,255,0.05); padding:8px 15px; border-radius:6px;" onclick="generateQuiz('${res.topic}', 'hard')">Hard</button>
            </div>
        `;
        appendMessage('bot', html, true);
    }
    else {
        appendMessage('bot', res.message);
    }
}

// --- Dynamic Components ---
async function updateSummaryPanel() {
    try {
        const res = await fetch(`${API_BASE}/summary`);
        const { data } = await res.json();
        sessionData.summary = data;
        
        if (data.length === 0) return;
        
        summaryList.innerHTML = data.map(item => `
            <div class="card">
                <h4>${item.topic}</h4>
                <p>${item.definition.substring(0, 80)}...</p>
                <div style="margin-top:8px; display:flex; flex-wrap:wrap; gap:5px;">
                    ${item.key_points.map(p => `<span style="font-size:0.65rem; background:rgba(147,51,234,0.1); color:var(--accent-purple); padding:2px 6px; border-radius:4px;">${p}</span>`).join('')}
                </div>
            </div>
        `).join('');
    } catch (e) { console.error(e); }
}

function updateHistoryPanel() {
    if (sessionData.chats.length === 0) {
        historyContainer.innerHTML = '<p class="empty-text">No previous conversations</p>';
        return;
    }

    const historyHtml = sessionData.chats.map(chat => `
        <div class="history-item ${chat.id === sessionData.currentChatId ? 'active' : ''}" 
             onclick="switchToChat('${chat.id}')"
             style="cursor: pointer; padding: 8px; margin: 4px 0; border-radius: 6px; 
                    ${chat.id === sessionData.currentChatId ? 'background: rgba(147,51,234,0.2);' : 'background: rgba(255,255,255,0.05);'}">
            <span>${chat.title}</span>
            <div style="font-size: 0.7rem; color: var(--text-dim); margin-top: 2px;">
                ${chat.messages.length} messages
            </div>
        </div>
    `).join('');

    historyContainer.innerHTML = historyHtml;
}

async function generateQuiz(topic, level) {
    showLoader();
    try {
        const res = await fetch(`${API_BASE}/quiz/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, level })
        });
        const data = await res.json();
        renderQuiz(data.questions, topic, level);
        switchTab('quiz');
        appendMessage('bot', `I've generated a <strong>${level}</strong> level quiz on <strong>${topic}</strong> in the right panel! 🎯`, true);
    } catch (e) {
        alert('Failed to generate quiz.');
    } finally {
        hideLoader();
    }
}

function renderQuiz(questions, topic, level) {
    let score = 0;
    let answered = 0;
    
    quizArea.innerHTML = `
        <div style="margin-bottom:15px;">
            <span style="font-size:0.7rem; color:var(--accent-purple); text-transform:uppercase; font-weight:bold;">${topic} • ${level}</span>
        </div>
    `;
    
    questions.forEach((q, qIdx) => {
        const div = document.createElement('div');
        div.className = 'quiz-item card';
        div.innerHTML = `
            <p style="margin-bottom:10px;">${q.q}</p>
            ${q.o.map((opt, oIdx) => `
                <button class="option-btn" onclick="handleQuizClick(this, ${oIdx}, ${q.a}, ${qIdx})">${opt}</button>
            `).join('')}
        `;
        quizArea.appendChild(div);
    });

    // Helper for quiz clicks
    window.handleQuizClick = (btn, selected, correct, qIdx) => {
        const parent = btn.parentElement;
        parent.querySelectorAll('button').forEach(b => b.disabled = true);
        
        if (selected === correct) {
            btn.classList.add('correct');
            score++;
        } else {
            btn.classList.add('wrong');
            parent.querySelectorAll('button')[correct].classList.add('correct');
        }
        
        answered++;
        if (answered === questions.length) {
            const finalLevel = score === questions.length ? "Advanced" : score >= 3 ? "Intermediate" : "Beginner";
            const resultHtml = `
                <div class="card" style="text-align:center; border-color:var(--accent-purple);">
                    <h4>Quiz Completed!</h4>
                    <p style="font-size:1.2rem; color:white; margin:10px 0;">Score: ${score}/${questions.length}</p>
                    <p>Level: <strong>${finalLevel}</strong></p>
                </div>
            `;
            quizArea.innerHTML += resultHtml;
            sessionData.quizzes.push({ topic, level, score, total: questions.length, result: finalLevel });
        }
    };
}

function switchTab(tabName) {
    document.querySelector(`.tab-btn[data-tab="${tabName}"]`).click();
}

// --- Resume Upload ---
resumeUpload.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    showLoader();
    try {
        const response = await fetch(`${API_BASE}/upload-resume`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        renderResumeAnalysis(data.analysis, data.filename);
        switchTab('resume');
        appendMessage('bot', `I've analyzed your resume **${data.filename}**. Check the Resume tab for detailed feedback!`, true);
    } catch (e) {
        alert('Failed to analyze resume.');
    } finally {
        hideLoader();
    }
};

function renderResumeAnalysis(analysis, filename) {
    sessionData.resumeAnalysis = analysis;
    resumeAnalysisArea.innerHTML = `
        <div class="card" style="border-color: var(--accent-purple);">
            <h4>Analysis: ${filename}</h4>
            <p>${analysis.summary}</p>
            
            <div style="margin-top:15px; display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                <div class="card" style="padding:10px; text-align:center;">
                    <p style="font-size:0.7rem; color:var(--text-dim);">Technical Score</p>
                    <p style="font-size:1.2rem; font-weight:bold; color:var(--accent-blue);">${analysis.technical_score}/100</p>
                </div>
                <div class="card" style="padding:10px; text-align:center;">
                    <p style="font-size:0.7rem; color:var(--text-dim);">Creativity Score</p>
                    <p style="font-size:1.2rem; font-weight:bold; color:var(--accent-purple);">${analysis.creativity_score}/100</p>
                </div>
            </div>

            <p style="margin-top:15px;"><strong>Missing Skills:</strong></p>
            <div style="display:flex; flex-wrap:wrap; gap:5px; margin-top:5px;">
                ${analysis.missing_skills.map(s => `<span style="font-size:0.7rem; background:rgba(239,68,68,0.1); color:#ef4444; padding:2px 8px; border-radius:4px;">${s}</span>`).join('')}
            </div>

            <p style="margin-top:15px;"><strong>Suggestions:</strong></p>
            <ul style="padding-left:20px; font-size:0.8rem; color:var(--text-dim); margin-top:5px;">
                ${analysis.suggestions.map(s => `<li>${s}</li>`).join('')}
            </ul>

            <p style="margin-top:15px;"><strong>Recommended Roadmap:</strong></p>
            <div style="margin-top:5px;">
                ${analysis.roadmap.map(step => `<div style="font-size:0.8rem; border-left:2px solid var(--accent-purple); padding-left:10px; margin-bottom:5px;">${step}</div>`).join('')}
            </div>
        </div>
    `;
}

// --- PDF Download ---
downloadBtn.onclick = async () => {
    showLoader();
    try {
        const response = await fetch(`${API_BASE}/report/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sessionData)
        });
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "learning_summary_pro.pdf";
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        alert('Failed to generate report.');
    } finally {
        hideLoader();
    }
};

// Function to update PDF button state
function updatePdfButtonState() {
    const currentChat = getCurrentChat();
    const hasMessages = currentChat && currentChat.messages.length > 0;
    const hasSummary = document.getElementById('summaryList').innerHTML.includes('<div class="summary-item">');
    
    downloadBtn.disabled = !(hasMessages || hasSummary);
}

// --- Document Upload Functions ---
function initializeDocumentUpload() {
    if (!documentUpload) {
        console.error('documentUpload element not found');
        return;
    }
    
    documentUpload.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        showLoader();
        try {
            const response = await fetch(`${API_BASE}/upload/document`, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.success) {
                appendMessage('bot', `📄 Document "${file.filename}" uploaded successfully! ${data.chunks_created} chunks processed. You can now ask questions about its content.`);
                updateDocumentList();
            } else {
                appendMessage('bot', `❌ Failed to upload document: ${data.error || 'Unknown error'}`);
            }
        } catch (e) {
            appendMessage('bot', '❌ Failed to upload document. Please try again.');
        } finally {
            hideLoader();
            // Reset file input
            documentUpload.value = '';
        }
    };
}

function initializeClearDocumentsBtn() {
    if (!clearDocumentsBtn) {
        console.error('clearDocumentsBtn element not found');
        return;
    }
    
    clearDocumentsBtn.onclick = async () => {
        if (!confirm('Clear all documents from the RAG system? This will remove all uploaded files.')) return;
        
        showLoader();
        try {
            const response = await fetch(`${API_BASE}/upload/clear`, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                appendMessage('bot', '🗑️ All documents cleared from the system.');
                updateDocumentList();
            } else {
                appendMessage('bot', '❌ Failed to clear documents.');
            }
        } catch (e) {
            appendMessage('bot', '❌ Failed to clear documents. Please try again.');
        } finally {
            hideLoader();
        }
    };
}

function initializeChatDownloadButtons() {
    if (!downloadChatTxt || !downloadChatPdf) {
        console.error('Chat download buttons not found');
        return;
    }
    
    downloadChatTxt.onclick = async () => {
        showLoader();
        try {
            const response = await fetch(`${API_BASE}/chat/download-summary?format=txt`, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                // Create and download file
                const blob = new Blob([data.content], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.filename;
                a.click();
                window.URL.revokeObjectURL(url);
                
                appendMessage('bot', `📄 Chat summary downloaded as ${data.filename}`);
            } else {
                // Handle the case where there's no chat history
                if (data.error && data.error.includes("No chat history")) {
                    appendMessage('bot', `💬 ${data.error} Start a conversation first, then try downloading the summary.`);
                } else {
                    appendMessage('bot', `❌ Failed to download summary: ${data.error || 'Unknown error'}`);
                }
            }
        } catch (e) {
            appendMessage('bot', '❌ Failed to download chat summary. Please try again.');
        } finally {
            hideLoader();
        }
    };
    
    downloadChatPdf.onclick = async () => {
        showLoader();
        try {
            const response = await fetch(`${API_BASE}/chat/download-summary?format=pdf`, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                // For now, download as TXT since PDF generation is complex
                const blob = new Blob([data.content], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.filename.replace('.pdf', '.txt'); // Download as TXT for now
                a.click();
                window.URL.revokeObjectURL(url);
                
                appendMessage('bot', `📋 Chat summary downloaded as ${data.filename.replace('.pdf', '.txt')} (PDF format coming soon)`);
            } else {
                // Handle the case where there's no chat history
                if (data.error && data.error.includes("No chat history")) {
                    appendMessage('bot', `💬 ${data.error} Start a conversation first, then try downloading the summary.`);
                } else {
                    appendMessage('bot', `❌ Failed to download summary: ${data.error || 'Unknown error'}`);
                }
            }
        } catch (e) {
            appendMessage('bot', '❌ Failed to download chat summary. Please try again.');
        } finally {
            hideLoader();
        }
    };
}

async function updateDocumentList() {
    try {
        const response = await fetch(`${API_BASE}/upload/documents`);
        const data = await response.json();
        
        if (data.success && data.documents.length > 0) {
            documentList.innerHTML = `
                <div style="margin-bottom: 15px;">
                    <div style="font-size: 0.8rem; color: var(--text-dim); margin-bottom: 8px;">
                        📚 ${data.documents.length} document(s) uploaded • ${data.total_chunks} chunks indexed
                    </div>
                    ${data.documents.map(doc => `
                        <div class="document-item" style="padding: 8px 12px; margin-bottom: 6px; background: rgba(255,255,255,0.05); border-radius: 6px; font-size: 0.8rem;">
                            📄 ${doc}
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            documentList.innerHTML = '<p class="empty-text">Upload documents to enable RAG-powered answers.</p>';
        }
    } catch (e) {
        console.error('Failed to update document list:', e);
    }
}

// --- Event Listeners ---
sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
});

clearChatBtn.addEventListener('click', async () => {
    if (!confirm('Clear all session data?')) return;
    showLoader();
    try {
        await fetch(`${API_BASE}/chat/clear-memory`, { method: 'POST' });
        location.reload();
    } catch (e) {
        alert('Failed to clear session.');
    } finally {
        hideLoader();
    }
});

// Event Listeners
sendBtn.onclick = sendMessage;
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

clearChatBtn.onclick = () => {
    if (confirm('Clear all chat history? This cannot be undone.')) {
        sessionData.chats = [];
        sessionData.currentChatId = null;
        chatMessages.innerHTML = '';
        updateHistoryPanel();
        appendMessage('bot', 'Chat history cleared. How can I help you today?');
    }
};

newChatBtn.onclick = () => {
    createNewChat();
    appendMessage('bot', 'New chat started! How can I help you today?');
};

// Auto-focus input on load
window.addEventListener('load', () => {
    userInput.focus();
    
    // Initialize RAG elements after DOM is ready
    setTimeout(() => {
        initializeDocumentUpload();
        initializeClearDocumentsBtn();
        initializeChatDownloadButtons();
        updateDocumentList(); // Load document list on startup
        createNewChat(); // Start with a new chat
        updatePdfButtonState(); // Initialize PDF button state
        console.log('AI Tutor Frontend Loaded with RAG capabilities + Chat Summary + Multiple Chats + PDF Fix');
    }, 100);
});
