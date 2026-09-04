// Chat Page JavaScript
class ChatPage {
    constructor() {
        this.ws = null;
        this.messages = [];
        this.currentAgent = 'assistant';
        this.voiceEnabled = false;
        this.currentTheme = 'neural-synapse';
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadSettings();
        this.startVoiceMonitoring();
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.addSystemMessage('Conectado ao Córtex');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.addSystemMessage('Erro de conexão. Usando modo offline.');
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.addSystemMessage('Desconectado. Tentando reconectar...');
            setTimeout(() => this.setupWebSocket(), 5000);
        };
    }
    
    handleWebSocketMessage(data) {
        if (data.type === 'response') {
            this.addAssistantMessage(data.content);
        } else if (data.type === 'agent_suggestion') {
            this.showAgentSuggestion(data);
        } else if (data.type === 'status') {
            this.updateStatus(data);
        }
    }
    
    setupEventListeners() {
        // Send message
        const sendButton = document.getElementById('sendButton');
        const messageInput = document.getElementById('messageInput');
        
        sendButton.addEventListener('click', () => this.sendMessage());
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Quick actions
        document.querySelectorAll('.quick-action').forEach(button => {
            button.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                this.executeQuickAction(action);
            });
        });
        
        // Automation items
        document.querySelectorAll('.automation-item').forEach(button => {
            button.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.executeAutomation(action);
            });
        });
        
        // System controls
        document.getElementById('volumeControl').addEventListener('input', (e) => {
            this.setVolume(e.target.value);
        });
        
        document.getElementById('brightnessControl').addEventListener('input', (e) => {
            this.setBrightness(e.target.value);
        });
        
        // Agent suggestion
        document.getElementById('switchAgentButton').addEventListener('click', () => {
            this.switchToAgent('programming');
        });
        
        // Settings
        document.getElementById('settingsButton').addEventListener('click', () => {
            document.getElementById('settingsModal').style.display = 'flex';
        });
        
        document.getElementById('closeSettingsModal').addEventListener('click', () => {
            document.getElementById('settingsModal').style.display = 'none';
        });
        
        // Settings changes
        document.getElementById('modelSelect').addEventListener('change', (e) => {
            this.changeModel(e.target.value);
        });
        
        document.getElementById('voiceSelect').addEventListener('change', (e) => {
            this.changeVoice(e.target.value);
        });
        
        document.getElementById('themeSelect').addEventListener('change', (e) => {
            this.changeTheme(e.target.value);
        });
        
        // Voice button
        document.getElementById('voiceButton').addEventListener('click', () => {
            this.toggleVoice();
        });
        
        // Add reminder
        document.getElementById('addReminderButton').addEventListener('click', () => {
            this.addReminder();
        });
        
        // Add note
        document.getElementById('addNoteButton').addEventListener('click', () => {
            this.addNote();
        });
    }
    
    sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.addUserMessage(message);
        input.value = '';
        
        // Send via WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'message',
                content: message,
                agent: this.currentAgent
            }));
        } else {
            // Fallback to HTTP API
            this.sendMessageViaAPI(message);
        }
    }
    
    async sendMessageViaAPI(message) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            this.addAssistantMessage(data.response);
        } catch (error) {
            console.error('Error sending message:', error);
            this.addSystemMessage('Erro ao enviar mensagem');
        }
    }
    
    addUserMessage(content) {
        this.addMessage('user', content);
    }
    
    addAssistantMessage(content) {
        this.addMessage('assistant', content);
        
        // Speak if voice is enabled
        if (this.voiceEnabled) {
            this.speak(content);
        }
    }
    
    addSystemMessage(content) {
        this.addMessage('system', content);
    }
    
    addMessage(type, content) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `<p>${this.escapeHtml(content)}</p>`;
        
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push({ type, content, timestamp: new Date() });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showAgentSuggestion(data) {
        const suggestion = document.getElementById('agentSuggestion');
        const suggestionText = suggestion.querySelector('.suggestion-text');
        const switchButton = document.getElementById('switchAgentButton');
        
        suggestionText.textContent = data.message;
        switchButton.textContent = `Trocar para ${data.agent} Agent`;
        switchButton.dataset.agent = data.agent;
        
        suggestion.style.display = 'block';
    }
    
    switchToAgent(agent) {
        this.currentAgent = agent;
        document.getElementById('agentSuggestion').style.display = 'none';
        this.addSystemMessage(`Mudando para ${agent} agent...`);
        
        // Navigate to agent page
        if (agent === 'programming') {
            window.location.href = '/dev';
        } else if (agent === 'security') {
            window.location.href = '/security';
        }
    }
    
    executeQuickAction(action) {
        const actions = {
            'open_youtube': 'Abra o YouTube',
            'set_timer': 'Defina um timer de 5 minutos',
            'create_note': 'Crie uma nota sobre ideias de projeto',
            'system_info': 'Mostre informações do sistema'
        };
        
        const message = actions[action];
        if (message) {
            document.getElementById('messageInput').value = message;
            this.sendMessage();
        }
    }
    
    executeAutomation(action) {
        const automations = {
            'open_app': 'open_app',
            'play_music': 'play_music',
            'search': 'search'
        };
        
        const automation = automations[action];
        if (automation) {
            this.sendCommand(automation);
        }
    }
    
    async sendCommand(command, params = {}) {
        try {
            const response = await fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command, params })
            });
            
            const data = await response.json();
            this.addSystemMessage(data.message);
        } catch (error) {
            console.error('Error executing command:', error);
            this.addSystemMessage('Erro ao executar comando');
        }
    }
    
    setVolume(value) {
        this.sendCommand('set_volume', { value });
    }
    
    setBrightness(value) {
        this.sendCommand('set_brightness', { value });
    }
    
    addReminder() {
        const time = prompt('Hora do lembrete (ex: 14:00):');
        const message = prompt('Mensagem do lembrete:');
        
        if (time && message) {
            this.sendCommand('set_reminder', { time, message });
            
            const remindersList = document.getElementById('remindersList');
            const reminderDiv = document.createElement('div');
            reminderDiv.className = 'reminder-item';
            reminderDiv.innerHTML = `
                <span class="reminder-time">${time}</span>
                <span class="reminder-text">${message}</span>
            `;
            remindersList.appendChild(reminderDiv);
        }
    }
    
    addNote() {
        const content = prompt('Conteúdo da nota:');
        
        if (content) {
            this.sendCommand('create_note', { content });
            
            const notesList = document.getElementById('notesList');
            const noteDiv = document.createElement('div');
            noteDiv.className = 'note-item';
            noteDiv.innerHTML = `<span class="note-text">${content}</span>`;
            notesList.appendChild(noteDiv);
        }
    }
    
    toggleVoice() {
        this.voiceEnabled = !this.voiceEnabled;
        const button = document.getElementById('voiceButton');
        button.classList.toggle('active', this.voiceEnabled);
        
        if (this.voiceEnabled) {
            this.addSystemMessage('Voz ativada. Diga "Ei Córtex" para comandos de voz.');
        } else {
            this.addSystemMessage('Voz desativada.');
        }
    }
    
    startVoiceMonitoring() {
        // Implement voice monitoring using Web Speech API
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = 'pt-BR';
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[event.results.length - 1][0].transcript;
                
                if (transcript.toLowerCase().includes('ei córtex')) {
                    const command = transcript.replace(/ei córtex/i, '').trim();
                    if (command) {
                        document.getElementById('messageInput').value = command;
                        this.sendMessage();
                    }
                }
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
            };
            
            // Start recognition if voice is enabled
            if (this.voiceEnabled) {
                this.recognition.start();
            }
        } else {
            console.log('Speech recognition not supported');
        }
    }
    
    speak(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'pt-BR';
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            speechSynthesis.speak(utterance);
        }
    }
    
    changeModel(model) {
        this.sendCommand('change_model', { model });
        this.addSystemMessage(`Modelo alterado para ${model}`);
    }
    
    changeVoice(voice) {
        this.sendCommand('change_voice', { voice });
        this.addSystemMessage(`Voz alterada para ${voice}`);
    }
    
    changeTheme(theme) {
        this.currentTheme = theme;
        document.body.className = `theme-${theme}`;
        this.sendCommand('change_theme', { theme });
        this.addSystemMessage(`Tema alterado para ${theme}`);
    }
    
    updateStatus(data) {
        // Update status indicators
        if (data.online) {
            document.querySelector('.status-indicator').classList.add('online');
            document.querySelector('.status-indicator').classList.remove('offline');
        } else {
            document.querySelector('.status-indicator').classList.remove('online');
            document.querySelector('.status-indicator').classList.add('offline');
        }
    }
    
    loadSettings() {
        // Load settings from localStorage or API
        const savedTheme = localStorage.getItem('cortex_theme');
        if (savedTheme) {
            this.changeTheme(savedTheme);
            document.getElementById('themeSelect').value = savedTheme;
        }
        
        const savedVoice = localStorage.getItem('cortex_voice');
        if (savedVoice) {
            document.getElementById('voiceSelect').value = savedVoice;
        }
    }
    
    saveSettings() {
        localStorage.setItem('cortex_theme', this.currentTheme);
        localStorage.setItem('cortex_voice', document.getElementById('voiceSelect').value);
    }
}

// Initialize chat page when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatPage = new ChatPage();
});