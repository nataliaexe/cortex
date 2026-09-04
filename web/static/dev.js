// Dev Agent Page JavaScript
class DevAgentPage {
    constructor() {
        this.editor = null;
        this.currentFile = 'core/engine.py';
        this.ws = null;
        this.taskStatus = 'idle';
        this.iterationCount = 0;
        
        this.init();
    }
    
    init() {
        this.setupMonacoEditor();
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadFileTree();
        this.loadGitStatus();
    }
    
    setupMonacoEditor() {
        require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' }});
        
        require(['vs/editor/editor.main'], function() {
            window.devAgent.editor = monaco.editor.create(document.getElementById('monacoEditor'), {
                value: this.getFileContent('core/engine.py'),
                language: 'python',
                theme: 'vs-dark',
                automaticLayout: true,
                fontSize: 14,
                lineNumbers: 'on',
                minimap: { enabled: true },
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                tabSize: 4,
                insertSpaces: true
            });
            
            // Update stats on content change
            window.devAgent.editor.onDidChangeModelContent(() => {
                window.devAgent.updateEditorStats();
            });
            
            window.devAgent.updateEditorStats();
        }.bind(this));
    }
    
    getFileContent(filename) {
        // Sample content - in production, load from API
        const sampleContents = {
            'core/engine.py': `#!/usr/bin/env python3
"""
Gênesis Córtex - Motor Principal
Orquestrador central do sistema
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .task_executor import TaskExecutor
from .decision_protocol import DecisionProtocol
from .semantic_matcher import SemanticMatcher
from .model_router import ModelRouter
from .governance import Governance


class CortexEngine:
    """Motor principal do Córtex"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.task_executor = TaskExecutor(config)
        self.decision_protocol = DecisionProtocol(config)
        self.semantic_matcher = SemanticMatcher(config)
        self.model_router = ModelRouter(config)
        self.governance = Governance(config)
        
        self.is_running = False
        
    async def start(self) -> None:
        """Inicia o motor do Córtex"""
        self.logger.info("Iniciando motor do Córtex")
        self.is_running = True
        await self.task_executor.initialize()
        
    async def stop(self) -> None:
        """Para o motor do Córtex"""
        self.logger.info("Parando motor do Córtex")
        self.is_running = False
        await self.task_executor.cleanup()
        
    async def process_input(self, user_input: str) -> str:
        """Processa entrada do usuário"""
        self.logger.info(f"Processando input: {user_input}")
        
        # Detectar intenção
        intent = await self.semantic_matcher.match_intent(user_input, {})
        
        # Protocolo de decisão
        decision = await self.decision_protocol.decide(user_input, intent, {})
        
        # Executar ação
        if decision.action == "execute_task":
            result = await self.task_executor.execute_intent(
                intent.intent,
                intent.parameters,
                {}
            )
            return result
        elif decision.action == "ask_llm":
            response = await self.model_router.route_request(
                prompt=user_input,
                task_type=intent.intent
            )
            return response
        else:
            return "Ação não reconhecida"
`,
            'core/task_executor.py': `#!/usr/bin/env python3
"""
Gênesis Córtex - Task Executor
Executa ações mapeadas (40+ métodos)
"""

import asyncio
import logging
import subprocess
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta

from .capabilities import ComputerControl, InternetTools, NetworkTools
from .governance import Governance


class TaskExecutor:
    """Executor de tarefas e ações do sistema"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.governance = Governance(config)
        self.computer = ComputerControl(self.governance)
        self.network = NetworkTools(config)
        self.internet = InternetTools(config, self.governance)
        self.action_map = self._build_action_map()
        
    def _build_action_map(self) -> Dict[str, callable]:
        """Constrói mapa de ações disponíveis"""
        return {
            "system_info": self.get_system_info,
            "disk_usage": self.get_disk_usage,
            "memory_usage": self.get_memory_usage,
            # ... mais ações
        }
        
    async def execute_intent(self, intent: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Executa uma intenção específica"""
        if intent not in self.action_map:
            return f"Ação '{intent}' não implementada"
            
        decision = self.governance.authorize(intent, parameters, context)
        self.governance.audit(intent, decision, params=parameters)
        
        if not decision.allowed:
            if decision.requires_confirmation:
                return f"CONFIRMAÇÃO NECESSÁRIA: {decision.reason}"
            return f"AÇÃO BLOQUEADA: {decision.reason}"
            
        try:
            action = self.action_map[intent]
            result = await action(parameters, context)
            self.governance.audit(intent, decision, params=parameters, outcome="completed")
            return str(result)
        except Exception as e:
            self.logger.error(f"Erro ao executar {intent}: {e}")
            self.governance.audit(intent, decision, params=parameters, outcome=f"failed: {type(e).__name__}")
            return f"Erro ao executar ação: {str(e)}"
`
        };
        
        return sampleContents[filename] || '// Arquivo não encontrado';
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            setTimeout(() => this.setupWebSocket(), 5000);
        };
    }
    
    handleWebSocketMessage(data) {
        if (data.type === 'task_update') {
            this.updateTaskStatus(data);
        } else if (data.type === 'terminal_output') {
            this.addTerminalOutput(data.output);
        } else if (data.type === 'file_update') {
            this.updateFileContent(data.file, data.content);
        }
    }
    
    setupEventListeners() {
        // Refresh files
        document.getElementById('refreshFiles').addEventListener('click', () => {
            this.loadFileTree();
        });
        
        // File tree clicks
        document.querySelectorAll('.tree-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.classList.contains('tree-icon')) return;
                
                if (item.classList.contains('tree-item--folder')) {
                    item.classList.toggle('expanded');
                } else {
                    const fileName = item.querySelector('.tree-name').textContent;
                    this.openFile(fileName);
                }
            });
        });
        
        // Save button
        document.getElementById('saveButton').addEventListener('click', () => {
            this.saveCurrentFile();
        });
        
        // Format button
        document.getElementById('formatButton').addEventListener('click', () => {
            this.formatCode();
        });
        
        // Run tests
        document.getElementById('runTestsButton').addEventListener('click', () => {
            this.runTests();
        });
        
        // Git commit
        document.getElementById('gitCommitButton').addEventListener('click', () => {
            this.gitCommit();
        });
        
        // Back button
        document.getElementById('backButton').addEventListener('click', () => {
            window.location.href = '/';
        });
        
        // Task buttons
        document.getElementById('planButton').addEventListener('click', () => {
            this.executeTaskAction('plan');
        });
        
        document.getElementById('codeButton').addEventListener('click', () => {
            this.executeTaskAction('code');
        });
        
        document.getElementById('testButton').addEventListener('click', () => {
            this.executeTaskAction('test');
        });
        
        document.getElementById('fixButton').addEventListener('click', () => {
            this.executeTaskAction('fix');
        });
        
        // New task modal
        document.getElementById('newTaskButton').addEventListener('click', () => {
            document.getElementById('newTaskModal').style.display = 'flex';
        });
        
        document.getElementById('closeTaskModal').addEventListener('click', () => {
            document.getElementById('newTaskModal').style.display = 'none';
        });
        
        document.getElementById('cancelTaskButton').addEventListener('click', () => {
            document.getElementById('newTaskModal').style.display = 'none';
        });
        
        document.getElementById('submitTaskButton').addEventListener('click', () => {
            this.submitNewTask();
        });
        
        // Terminal input
        document.getElementById('terminalInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.executeTerminalCommand(e.target.value);
                e.target.value = '';
            }
        });
        
        // Terminal controls
        document.querySelector('.terminal-button.clear').addEventListener('click', () => {
            document.getElementById('terminalOutput').innerHTML = '';
        });
    }
    
    openFile(filename) {
        this.currentFile = filename;
        
        // Update tab
        const tabsContainer = document.getElementById('editorTabs');
        tabsContainer.innerHTML = `
            <div class="tab active" data-file="${filename}">
                <span class="tab-name">${filename}</span>
                <span class="tab-close">×</span>
            </div>
        `;
        
        // Load file content
        if (this.editor) {
            const content = this.getFileContent(filename);
            this.editor.setValue(content);
            
            // Update language based on extension
            const ext = filename.split('.').pop();
            const languages = {
                'py': 'python',
                'js': 'javascript',
                'html': 'html',
                'css': 'css',
                'json': 'json',
                'md': 'markdown'
            };
            
            const language = languages[ext] || 'plaintext';
            monaco.editor.setModelLanguage(this.editor.getModel(), language);
            
            document.getElementById('language').textContent = language.charAt(0).toUpperCase() + language.slice(1);
        }
        
        this.updateEditorStats();
    }
    
    updateEditorStats() {
        if (!this.editor) return;
        
        const content = this.editor.getValue();
        const lines = content.split('\n').length;
        const chars = content.length;
        
        document.getElementById('lineCount').textContent = lines;
        document.getElementById('charCount').textContent = chars.toLocaleString();
    }
    
    saveCurrentFile() {
        if (!this.editor) return;
        
        const content = this.editor.getValue();
        
        // Send to API
        fetch('/api/files/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file: this.currentFile,
                content: content
            })
        })
        .then(response => response.json())
        .then(data => {
            this.addTerminalOutput(`Arquivo ${this.currentFile} salvo com sucesso`, 'success');
        })
        .catch(error => {
            this.addTerminalOutput(`Erro ao salvar arquivo: ${error}`, 'error');
        });
    }
    
    formatCode() {
        if (!this.editor) return;
        
        // Format using Monaco's built-in formatter
        this.editor.getAction('editor.action.formatDocument').run();
        this.addTerminalOutput('Código formatado', 'success');
    }
    
    runTests() {
        this.addTerminalOutput('> pytest tests/ -v');
        
        fetch('/api/tests/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            this.addTerminalOutput(data.output);
            if (data.success) {
                this.addTerminalOutput(`✅ ${data.passed}/${data.total} tests passed`, 'success');
            } else {
                this.addTerminalOutput(`❌ ${data.failed} tests failed`, 'error');
            }
        })
        .catch(error => {
            this.addTerminalOutput(`Erro ao executar testes: ${error}`, 'error');
        });
    }
    
    gitCommit() {
        const message = prompt('Mensagem do commit:');
        if (!message) return;
        
        this.addTerminalOutput(`> git commit -m "${message}"`);
        
        fetch('/api/git/commit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        })
        .then(response => response.json())
        .then(data => {
            this.addTerminalOutput(data.output, 'success');
            this.loadGitStatus();
        })
        .catch(error => {
            this.addTerminalOutput(`Erro ao fazer commit: ${error}`, 'error');
        });
    }
    
    executeTaskAction(action) {
        this.addTerminalOutput(`> Executando ação: ${action}`);
        
        fetch('/api/agent/programming/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        })
        .then(response => response.json())
        .then(data => {
            this.updateTaskStatus(data);
            this.addTerminalOutput(data.message);
        })
        .catch(error => {
            this.addTerminalOutput(`Erro ao executar ação: ${error}`, 'error');
        });
    }
    
    submitNewTask() {
        const description = document.getElementById('taskDescription').value;
        const priority = document.getElementById('taskPriority').value;
        const context = document.getElementById('taskContext').value;
        
        if (!description) {
            alert('Por favor, descreva a tarefa');
            return;
        }
        
        document.getElementById('newTaskModal').style.display = 'none';
        
        fetch('/api/agent/programming/task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                description,
                priority,
                context
            })
        })
        .then(response => response.json())
        .then(data => {
            this.addTerminalOutput(`Tarefa submetida: ${data.task_id}`, 'success');
            this.addHistoryItem(description, 'in-progress');
        })
        .catch(error => {
            this.addTerminalOutput(`Erro ao submeter tarefa: ${error}`, 'error');
        });
        
        // Clear form
        document.getElementById('taskDescription').value = '';
        document.getElementById('taskContext').value = '';
    }
    
    executeTerminalCommand(command) {
        this.addTerminalOutput(`> ${command}`);
        
        fetch('/api/terminal/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        })
        .then(response => response.json())
        .then(data => {
            this.addTerminalOutput(data.output);
        })
        .catch(error => {
            this.addTerminalOutput(`Erro: ${error}`, 'error');
        });
    }
    
    addTerminalOutput(output, type = '') {
        const terminalOutput = document.getElementById('terminalOutput');
        const line = document.createElement('div');
        line.className = `terminal-line ${type}`;
        line.textContent = output;
        terminalOutput.appendChild(line);
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }
    
    updateTaskStatus(data) {
        if (data.status) {
            this.taskStatus = data.status;
            document.getElementById('currentStatus').textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
            document.getElementById('agentStatus').textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
            
            if (data.status === 'busy') {
                document.getElementById('agentStatus').classList.add('busy');
            } else {
                document.getElementById('agentStatus').classList.remove('busy');
            }
        }
        
        if (data.iteration !== undefined) {
            this.iterationCount = data.iteration;
            document.getElementById('iterationCount').textContent = `${data.iteration}/5`;
        }
        
        if (data.progress !== undefined) {
            document.getElementById('progressFill').style.width = `${data.progress}%`;
        }
    }
    
    addHistoryItem(title, status = 'in-progress') {
        const historyList = document.getElementById('historyList');
        const item = document.createElement('div');
        item.className = `history-item ${status}`;
        
        const icon = status === 'completed' ? '✅' : '🔄';
        const time = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        
        item.innerHTML = `
            <span class="history-icon">${icon}</span>
            <div class="history-content">
                <span class="history-title">${title}</span>
                <span class="history-time">${time}</span>
            </div>
        `;
        
        historyList.insertBefore(item, historyList.firstChild);
    }
    
    loadFileTree() {
        // In production, load from API
        fetch('/api/files/tree')
            .then(response => response.json())
            .then(data => {
                // Update file tree
                console.log('File tree loaded:', data);
            })
            .catch(error => {
                console.error('Error loading file tree:', error);
            });
    }
    
    loadGitStatus() {
        fetch('/api/git/status')
            .then(response => response.json())
            .then(data => {
                const gitStatus = document.getElementById('gitStatus');
                gitStatus.innerHTML = '';
                
                data.files.forEach(file => {
                    const item = document.createElement('div');
                    item.className = `git-item ${file.status}`;
                    item.innerHTML = `
                        <span class="git-status-letter">${file.letter}</span>
                        <span class="git-file">${file.path}</span>
                    `;
                    gitStatus.appendChild(item);
                });
            })
            .catch(error => {
                console.error('Error loading git status:', error);
            });
    }
    
    updateFileContent(file, content) {
        if (file === this.currentFile && this.editor) {
            this.editor.setValue(content);
        }
    }
}

// Initialize Dev Agent page when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.devAgent = new DevAgentPage();
});