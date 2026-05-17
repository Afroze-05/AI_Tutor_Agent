// AI Programming Tutor - Frontend JavaScript
class AIProgrammingTutor {
    constructor() {
        this.apiBaseUrl = 'http://127.0.0.1:8000';
        this.sessionId = 'default';
        this.init();
    }

    init() {
        this.initChatbot();
        this.checkApiHealth();
    }

    async checkApiHealth() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            if (!response.ok) {
                console.error('API is not available. Please check if the backend is running.');
            }
        } catch (error) {
            console.error('Health check failed:', error);
            console.error('Cannot connect to the API. Please ensure the backend server is running.');
        }
    }

    // Chatbot functionality
    initChatbot() {
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendChatBtn = document.getElementById('sendChatBtn');
        this.chatLoading = document.getElementById('chatLoading');
        this.charCount = document.getElementById('charCount');
        
        // Chat event listeners
        this.sendChatBtn.addEventListener('click', () => this.sendChatMessage());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });
        
        // Character counter
        this.chatInput.addEventListener('input', () => {
            this.updateCharCount();
        });
        
        // Focus input on load
        this.chatInput.focus();
    }

    updateCharCount() {
        const length = this.chatInput.value.length;
        this.charCount.textContent = length;
        
        if (length >= 450) {
            this.charCount.style.color = 'var(--danger-color)';
        } else if (length >= 400) {
            this.charCount.style.color = 'var(--warning-color)';
        } else {
            this.charCount.style.color = 'var(--text-secondary)';
        }
    }

    async sendChatMessage() {
        const message = this.chatInput.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addUserMessage(message);
        
        // Clear input and reset character count
        this.chatInput.value = '';
        this.updateCharCount();
        
        // Show loading state
        this.showChatLoading();
        
        try {
            // Call chat API
            const response = await fetch(`${this.apiBaseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.addBotMessage(data.response);
            } else {
                this.addBotMessage('Sorry, I encountered an error. Please try again.');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.addBotMessage('Sorry, I\'m having trouble connecting. Please check your internet connection and try again.');
        } finally {
            this.hideChatLoading();
            this.chatInput.focus();
        }
    }

    addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'user-message';
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="message-content">
                <p>${this.escapeHtml(message)}</p>
            </div>
        `;
        
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'bot-message';
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                ${this.formatBotMessage(message)}
            </div>
        `;
        
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    formatBotMessage(message) {
        // Convert markdown-style code blocks to HTML
        let formatted = this.escapeHtml(message);
        
        // Handle code blocks with language detection
        formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, language, code) => {
            const lang = language || 'code';
            return `<pre data-language="${lang.toUpperCase()}"><code>${this.escapeHtml(code.trim())}</code></pre>`;
        });
        
        // Handle inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Handle bold text
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Handle line breaks
        formatted = formatted.replace(/\n\n/g, '</p><p>');
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Wrap in paragraphs
        if (!formatted.startsWith('<p>')) {
            formatted = `<p>${formatted}</p>`;
        }
        
        return formatted;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showChatLoading() {
        this.chatLoading.style.display = 'block';
        this.sendChatBtn.disabled = true;
        this.chatInput.disabled = true;
    }

    hideChatLoading() {
        this.chatLoading.style.display = 'none';
        this.sendChatBtn.disabled = false;
        this.chatInput.disabled = false;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AIProgrammingTutor();
});
