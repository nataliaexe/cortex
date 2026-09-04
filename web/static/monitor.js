// System Monitor Page JavaScript
class SystemMonitorPage {
    constructor() {
        this.ws = null;
        this.refreshInterval = null;
        this.logsPaused = false;
        this.performanceChart = null;
        this.performanceData = {
            labels: [],
            datasets: [{
                label: 'CPU',
                data: [],
                borderColor: '#00ff88',
                backgroundColor: 'rgba(0, 255, 136, 0.1)',
                tension: 0.4
            }, {
                label: 'RAM',
                data: [],
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                tension: 0.4
            }]
        };
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.setupPerformanceChart();
        this.loadSystemData();
        this.startAutoRefresh();
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
        if (data.type === 'agent_status') {
            this.updateAgentStatus(data.agents);
        } else if (data.type === 'system_resources') {
            this.updateSystemResources(data.resources);
        } else if (data.type === 'task_queue') {
            this.updateTaskQueue(data.queue);
        } else if (data.type === 'log_entry') {
            this.addLogEntry(data.log);
        } else if (data.type === 'metrics_update') {
            this.updateMetrics(data.metrics);
        }
    }
    
    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshButton').addEventListener('click', () => {
            this.loadSystemData();
        });
        
        // Back button
        document.getElementById('backButton').addEventListener('click', () => {
            window.location.href = '/';
        });
        
        // Logs controls
        document.querySelector('.logs-button.clear').addEventListener('click', () => {
            document.getElementById('logsContainer').innerHTML = '';
        });
        
        document.querySelector('.logs-button.pause').addEventListener('click', (e) => {
            this.logsPaused = !this.logsPaused;
            e.target.textContent = this.logsPaused ? 'Retomar' : 'Pausar';
        });
        
        // Agent card clicks
        document.querySelectorAll('.agent-card').forEach(card => {
            card.addEventListener('click', () => {
                const agentName = card.querySelector('.agent-name').textContent;
                this.showAgentDetails(agentName);
            });
        });
    }
    
    setupPerformanceChart() {
        const ctx = document.getElementById('performanceChart').getContext('2d');
        
        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: this.performanceData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: '#a0a0b0',
                            font: { size: 10 }
                        },
                        grid: {
                            color: '#2a2a3e'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#ffffff',
                            font: { size: 11 },
                            boxWidth: 12
                        }
                    }
                },
                elements: {
                    point: {
                        radius: 0
                    }
                }
            }
        });
    }
    
    loadSystemData() {
        // Load all system data
        this.loadAgentStatus();
        this.loadSystemResources();
        this.loadTaskQueue();
        this.loadMetrics();
    }
    
    loadAgentStatus() {
        fetch('/api/system/agents')
            .then(response => response.json())
            .then(data => {
                this.updateAgentStatus(data.agents);
            })
            .catch(error => {
                console.error('Error loading agent status:', error);
            });
    }
    
    loadSystemResources() {
        fetch('/api/system/resources')
            .then(response => response.json())
            .then(data => {
                this.updateSystemResources(data.resources);
            })
            .catch(error => {
                console.error('Error loading system resources:', error);
            });
    }
    
    loadTaskQueue() {
        fetch('/api/system/queue')
            .then(response => response.json())
            .then(data => {
                this.updateTaskQueue(data.queue);
            })
            .catch(error => {
                console.error('Error loading task queue:', error);
            });
    }
    
    loadMetrics() {
        fetch('/api/system/metrics')
            .then(response => response.json())
            .then(data => {
                this.updateMetrics(data.metrics);
            })
            .catch(error => {
                console.error('Error loading metrics:', error);
            });
    }
    
    updateAgentStatus(agents) {
        const agentsGrid = document.querySelector('.agents-grid');
        let onlineCount = 0;
        
        agents.forEach(agent => {
            if (agent.status === 'online' || agent.status === 'busy') {
                onlineCount++;
            }
        });
        
        document.getElementById('agentsOnline').textContent = `${onlineCount}/${agents.length} Online`;
        
        // Update agent cards
        agents.forEach(agent => {
            const cards = document.querySelectorAll('.agent-card');
            cards.forEach(card => {
                const name = card.querySelector('.agent-name').textContent;
                if (name.toLowerCase().includes(agent.name.toLowerCase())) {
                    const statusElement = card.querySelector('.agent-status');
                    statusElement.className = `agent-status ${agent.status}`;
                    statusElement.textContent = this.getStatusEmoji(agent.status) + ' ' + agent.status.charAt(0).toUpperCase() + agent.status.slice(1);
                    
                    card.className = `agent-card ${agent.status}`;
                    
                    // Update details
                    const details = card.querySelector('.agent-details');
                    if (agent.current_task) {
                        details.innerHTML = `
                            <span class="agent-detail">Tarefa: <strong>${agent.current_task}</strong></span>
                            <span class="agent-detail">Progresso: <strong>${agent.progress || 0}%</strong></span>
                        `;
                    }
                }
            });
        });
    }
    
    getStatusEmoji(status) {
        const emojis = {
            online: '🟢',
            busy: '🟡',
            idle: '⚪',
            offline: '🔴'
        };
        return emojis[status] || '⚪';
    }
    
    updateSystemResources(resources) {
        // Update CPU
        const cpuValue = resources.cpu || 0;
        document.getElementById('cpuValue').textContent = cpuValue;
        document.getElementById('cpuBar').style.width = `${cpuValue}%`;
        document.getElementById('cpuBar').className = `bar-fill ${this.getResourceClass(cpuValue)}`;
        
        // Update RAM
        const ramValue = resources.memory || 0;
        document.getElementById('ramValue').textContent = ramValue;
        document.getElementById('ramBar').style.width = `${ramValue}%`;
        document.getElementById('ramBar').className = `bar-fill ${this.getResourceClass(ramValue)}`;
        
        // Update GPU
        const gpuValue = resources.gpu || 0;
        document.getElementById('gpuValue').textContent = gpuValue;
        document.getElementById('gpuBar').style.width = `${gpuValue}%`;
        document.getElementById('gpuBar').className = `bar-fill ${this.getResourceClass(gpuValue)}`;
        
        // Update Disk
        const diskValue = resources.disk || 0;
        document.getElementById('diskValue').textContent = diskValue;
        document.getElementById('diskBar').style.width = `${diskValue}%`;
        document.getElementById('diskBar').className = `bar-fill ${this.getResourceClass(diskValue)}`;
        
        // Update system health badge
        const healthBadge = document.getElementById('systemHealth');
        const avgUsage = (cpuValue + ramValue + gpuValue) / 3;
        
        if (avgUsage < 50) {
            healthBadge.textContent = 'Saudável';
            healthBadge.style.color = 'var(--success)';
        } else if (avgUsage < 75) {
            healthBadge.textContent = 'Moderado';
            healthBadge.style.color = 'var(--warning)';
        } else {
            healthBadge.textContent = 'Crítico';
            healthBadge.style.color = 'var(--error)';
        }
        
        // Update performance chart
        this.updatePerformanceChart(cpuValue, ramValue);
    }
    
    getResourceClass(value) {
        if (value < 50) return '';
        if (value < 75) return 'warning';
        return 'error';
    }
    
    updatePerformanceChart(cpu, ram) {
        const now = new Date();
        const timeLabel = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        
        // Add new data
        this.performanceData.labels.push(timeLabel);
        this.performanceData.datasets[0].data.push(cpu);
        this.performanceData.datasets[1].data.push(ram);
        
        // Keep only last 20 data points
        if (this.performanceData.labels.length > 20) {
            this.performanceData.labels.shift();
            this.performanceData.datasets[0].data.shift();
            this.performanceData.datasets[1].data.shift();
        }
        
        // Update chart
        if (this.performanceChart) {
            this.performanceChart.update('none');
        }
    }
    
    updateTaskQueue(queue) {
        const queueList = document.getElementById('queueList');
        queueList.innerHTML = '';
        
        let pendingCount = 0;
        
        queue.forEach(task => {
            if (task.status === 'pending') {
                pendingCount++;
            }
            
            const queueItem = document.createElement('div');
            queueItem.className = `queue-item ${task.priority.toLowerCase()}`;
            
            const progressHtml = task.progress 
                ? `<div class="queue-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${task.progress}%"></div>
                    </div>
                    <span class="progress-text">${task.progress}%</span>
                </div>`
                : `<div class="queue-status">
                    <span class="status-badge ${task.status}">${task.status.charAt(0).toUpperCase() + task.status.slice(1)}</span>
                </div>`;
            
            queueItem.innerHTML = `
                <div class="queue-header">
                    <span class="queue-priority">${task.priority.toUpperCase()}</span>
                    <span class="queue-id">#${task.id}</span>
                </div>
                <div class="queue-content">
                    <span class="queue-task">${task.description}</span>
                    <span class="queue-agent">${this.getAgentEmoji(task.agent)} ${task.agent}</span>
                </div>
                ${progressHtml}
            `;
            
            queueList.appendChild(queueItem);
        });
        
        document.getElementById('queueCount').textContent = `${pendingCount} Pendentes`;
    }
    
    getAgentEmoji(agent) {
        const emojis = {
            assistant: '💬',
            programming: '💻',
            security: '🔒',
            evolution: '🧠',
            system: '🔄'
        };
        return emojis[agent.toLowerCase()] || '📋';
    }
    
    updateMetrics(metrics) {
        document.getElementById('completedTasks').textContent = metrics.completed_tasks?.toLocaleString() || '0';
        document.getElementById('successRate').textContent = `${metrics.success_rate || 0}%`;
        document.getElementById('avgTime').textContent = `${metrics.avg_time || 0}s`;
        document.getElementById('tokensUsed').textContent = `${(metrics.tokens_used / 1000).toFixed(1)}K`;
        document.getElementById('actionsPerHour').textContent = metrics.actions_per_hour || 0;
    }
    
    addLogEntry(log) {
        if (this.logsPaused) return;
        
        const logsContainer = document.getElementById('logsContainer');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${log.level.toLowerCase()}`;
        
        const time = new Date(log.timestamp).toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
        
        logEntry.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-level">${log.level.toUpperCase()}</span>
            <span class="log-message">${log.message}</span>
        `;
        
        logsContainer.insertBefore(logEntry, logsContainer.firstChild);
        
        // Keep only last 50 log entries
        while (logsContainer.children.length > 50) {
            logsContainer.removeChild(logsContainer.lastChild);
        }
    }
    
    showAgentDetails(agentName) {
        // Navigate to specific agent page
        const agentPages = {
            'Assistente': '/',
            'Programming': '/dev',
            'Security': '/security',
            'Evolution': '/memory'
        };
        
        const page = agentPages[agentName];
        if (page) {
            window.location.href = page;
        }
    }
    
    startAutoRefresh() {
        // Refresh data every 5 seconds
        this.refreshInterval = setInterval(() => {
            this.loadSystemResources();
            this.loadTaskQueue();
        }, 5000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Initialize System Monitor page when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.systemMonitor = new SystemMonitorPage();
});