// Gênesis Córtex - Dashboard JavaScript
// Neural Synapse Theme

class CortexDashboard {
    constructor() {
        this.ws = null;
        this.messageCount = 0;
        this.startTime = Date.now();
        this.isConnected = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.updateStatus();
        this.startUptimeCounter();
    }
    
    setupEventListeners() {
        // Input field
        const userInput = document.getElementById('userInput');
        const sendButton = document.getElementById('sendButton');
        
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Voice button
        const voiceButton = document.getElementById('voiceButton');
        voiceButton.addEventListener('click', () => {
            this.toggleVoice();
        });
        
        // Quick actions
        document.querySelectorAll('.action-button').forEach(button => {
            button.addEventListener('click', () => {
                const action = button.dataset.action;
                this.executeQuickAction(action);
            });
        });
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.isConnected = true;
            this.updateConnectionStatus(true);
            console.log('WebSocket conectado');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
        
        this.ws.onclose = () => {
            this.isConnected = false;
            this.updateConnectionStatus(false);
            console.log('WebSocket desconectado');
            
            // Tentar reconectar após 5 segundos
            setTimeout(() => {
                this.connectWebSocket();
            }, 5000);
        };
    }
    
    handleWebSocketMessage(data) {
        if (data.type === 'response') {
            this.addMessage(data.content, 'system');
        } else if (data.type === 'error') {
            this.addMessage(`Erro: ${data.content}`, 'system');
        }
    }
    
    async sendMessage() {
        const userInput = document.getElementById('userInput');
        const message = userInput.value.trim();
        
        if (!message) return;
        
        // Adiciona mensagem do usuário
        this.addMessage(message, 'user');
        userInput.value = '';
        
        // Incrementa contador
        this.messageCount++;
        this.updateStats();
        
        // Envia via WebSocket se conectado
        if (this.isConnected && this.ws) {
            this.ws.send(message);
        } else {
            // Fallback para HTTP
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message })
                });
                
                const data = await response.json();
                this.addMessage(data.response, 'system');
            } catch (error) {
                this.addMessage('Erro ao enviar mensagem', 'system');
            }
        }
    }
    
    addMessage(content, type) {
        const chatContainer = document.getElementById('chatContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = `<p>${this.escapeHtml(content)}</p>`;
        
        messageDiv.appendChild(messageContent);
        chatContainer.appendChild(messageDiv);
        
        // Scroll para baixo
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    toggleVoice() {
        const voiceButton = document.getElementById('voiceButton');
        voiceButton.classList.toggle('active');
        
        if (voiceButton.classList.contains('active')) {
            // Ativar reconhecimento de voz
            this.startVoiceRecognition();
        } else {
            // Parar reconhecimento de voz
            this.stopVoiceRecognition();
        }
    }
    
    startVoiceRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.lang = 'pt-BR';
            this.recognition.continuous = true;
            this.recognition.interimResults = false;
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[event.results.length - 1][0].transcript;
                document.getElementById('userInput').value = transcript;
            };
            
            this.recognition.onerror = (event) => {
                console.error('Erro no reconhecimento de voz:', event.error);
                this.toggleVoice();
            };
            
            this.recognition.start();
        } else {
            alert('Reconhecimento de voz não suportado neste navegador');
            this.toggleVoice();
        }
    }
    
    stopVoiceRecognition() {
        if (this.recognition) {
            this.recognition.stop();
            this.recognition = null;
        }
    }
    
    async executeQuickAction(action) {
        const actions = {
            'system_info': 'Informações do sistema',
            'security_scan': 'Iniciando scan de segurança',
            'dependency_check': 'Verificando dependências'
        };
        
        const message = actions[action] || action;
        this.addMessage(message, 'user');
        
        // Executa ação correspondente
        try {
            let endpoint;
            if (action === 'system_info') {
                endpoint = '/api/system/info';
            } else if (action === 'security_scan') {
                endpoint = '/api/security/scan';
            } else if (action === 'dependency_check') {
                endpoint = '/api/security/dependencies';
            }
            
            if (endpoint) {
                const response = await fetch(endpoint);
                const data = await response.json();
                this.addMessage(JSON.stringify(data, null, 2), 'system');
            }
        } catch (error) {
            this.addMessage(`Erro ao executar ação: ${error.message}`, 'system');
        }
    }
    
    async updateStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // Atualiza indicadores de status
            document.getElementById('motorStatus').textContent = data.status === 'running' ? 'Online' : 'Offline';
            document.getElementById('llmStatus').textContent = data.llm_enabled ? 'Ativo' : 'Inativo';
            document.getElementById('voiceStatus').textContent = data.voice_enabled ? 'Ativo' : 'Inativo';
            document.getElementById('securityStatus').textContent = data.security_enabled ? 'Ativo' : 'Inativo';
            
        } catch (error) {
            console.error('Erro ao atualizar status:', error);
        }
    }
    
    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        
        if (connected) {
            statusDot.classList.add('online');
            statusDot.classList.remove('offline');
            statusText.textContent = 'Conectado';
        } else {
            statusDot.classList.add('offline');
            statusDot.classList.remove('online');
            statusText.textContent = 'Desconectado';
        }
    }
    
    updateStats() {
        document.getElementById('messageCount').textContent = this.messageCount;
    }
    
    startUptimeCounter() {
        setInterval(() => {
            const uptime = Math.floor((Date.now() - this.startTime) / 1000);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            const seconds = uptime % 60;
            
            document.getElementById('uptime').textContent = 
                `${hours}h ${minutes}m ${seconds}s`;
        }, 1000);
    }
}

// Inicializa dashboard quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new CortexDashboard();
});

// Service Worker para PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(registration => {
                console.log('Service Worker registrado:', registration);
            })
            .catch(error => {
                console.log('Erro ao registrar Service Worker:', error);
            });
    });
}