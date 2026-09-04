// Security Agent Page JavaScript
class SecurityAgentPage {
    constructor() {
        this.currentMode = 'scan';
        this.monitoringActive = false;
        this.ws = null;
        this.threats = [];
        this.networkCanvas = null;
        this.networkCtx = null;
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.setupNetworkCanvas();
        this.loadThreats();
        this.loadProcesses();
        this.startNetworkAnimation();
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
        if (data.type === 'threat_detected') {
            this.addThreat(data.threat);
        } else if (data.type === 'scan_progress') {
            this.updateScanProgress(data.progress);
        } else if (data.type === 'scan_complete') {
            this.handleScanComplete(data.results);
        } else if (data.type === 'network_traffic') {
            this.updateNetworkTraffic(data.traffic);
        } else if (data.type === 'process_alert') {
            this.handleProcessAlert(data.process);
        }
    }
    
    setupEventListeners() {
        // Mode buttons
        document.querySelectorAll('.mode-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchMode(e.target.dataset.mode);
            });
        });
        
        // Scan button
        document.getElementById('scanButton').addEventListener('click', () => {
            this.showScanModal();
        });
        
        // Start scan button
        document.getElementById('startScanButton').addEventListener('click', () => {
            this.showScanModal();
        });
        
        // Scan modal
        document.getElementById('closeScanModal').addEventListener('click', () => {
            document.getElementById('scanModal').style.display = 'none';
        });
        
        document.getElementById('cancelScanButton').addEventListener('click', () => {
            document.getElementById('scanModal').style.display = 'none';
        });
        
        document.getElementById('confirmScanButton').addEventListener('click', () => {
            this.startScan();
        });
        
        // Threat actions
        document.getElementById('exportReportButton').addEventListener('click', () => {
            this.exportReport();
        });
        
        document.getElementById('clearThreatsButton').addEventListener('click', () => {
            this.clearThreats();
        });
        
        // Refresh processes
        document.getElementById('refreshProcesses').addEventListener('click', () => {
            this.loadProcesses();
        });
        
        // Back button
        document.getElementById('backButton').addEventListener('click', () => {
            window.location.href = '/';
        });
        
        // Threat item clicks
        document.getElementById('threatsList').addEventListener('click', (e) => {
            const threatItem = e.target.closest('.threat-item');
            if (threatItem) {
                this.showThreatDetails(threatItem);
            }
        });
    }
    
    setupNetworkCanvas() {
        this.networkCanvas = document.getElementById('networkCanvas');
        this.networkCtx = this.networkCanvas.getContext('2d');
        
        // Set canvas size
        const resizeCanvas = () => {
            const container = this.networkCanvas.parentElement;
            this.networkCanvas.width = container.clientWidth;
            this.networkCanvas.height = container.clientHeight;
        };
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
    }
    
    startNetworkAnimation() {
        const animate = () => {
            this.drawNetworkVisualization();
            requestAnimationFrame(animate);
        };
        animate();
    }
    
    drawNetworkVisualization() {
        if (!this.networkCtx) return;
        
        const ctx = this.networkCtx;
        const width = this.networkCanvas.width;
        const height = this.networkCanvas.height;
        
        // Clear canvas
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, width, height);
        
        // Draw network nodes
        const nodes = [
            { x: width * 0.2, y: height * 0.3, type: 'server' },
            { x: width * 0.5, y: height * 0.5, type: 'router' },
            { x: width * 0.8, y: height * 0.3, type: 'client' },
            { x: width * 0.3, y: height * 0.7, type: 'server' },
            { x: width * 0.7, y: height * 0.7, type: 'client' }
        ];
        
        // Draw connections
        ctx.strokeStyle = '#2a2a3e';
        ctx.lineWidth = 2;
        
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                ctx.beginPath();
                ctx.moveTo(nodes[i].x, nodes[i].y);
                ctx.lineTo(nodes[j].x, nodes[j].y);
                ctx.stroke();
            }
        }
        
        // Draw nodes
        nodes.forEach(node => {
            ctx.beginPath();
            ctx.arc(node.x, node.y, 15, 0, Math.PI * 2);
            
            if (node.type === 'server') {
                ctx.fillStyle = '#00ff88';
            } else if (node.type === 'router') {
                ctx.fillStyle = '#00d4ff';
            } else {
                ctx.fillStyle = '#ffaa00';
            }
            
            ctx.fill();
            
            // Draw node icon
            ctx.fillStyle = '#0a0a1a';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            const icons = { server: '🖥️', router: '🔄', client: '💻' };
            ctx.fillText(icons[node.type], node.x, node.y);
        });
        
        // Draw traffic packets
        const time = Date.now() / 1000;
        for (let i = 0; i < 3; i++) {
            const t = (time + i * 0.5) % 1;
            const startNode = nodes[Math.floor(t * (nodes.length - 1))];
            const endNode = nodes[Math.floor(t * (nodes.length - 1)) + 1];
            
            if (startNode && endNode) {
                const x = startNode.x + (endNode.x - startNode.x) * t;
                const y = startNode.y + (endNode.y - startNode.y) * t;
                
                ctx.beginPath();
                ctx.arc(x, y, 4, 0, Math.PI * 2);
                ctx.fillStyle = '#ff4444';
                ctx.fill();
            }
        }
    }
    
    switchMode(mode) {
        this.currentMode = mode;
        
        // Update UI
        document.querySelectorAll('.mode-button').forEach(button => {
            button.classList.toggle('active', button.dataset.mode === mode);
        });
        
        const statusIndicator = document.getElementById('agentStatus');
        
        if (mode === 'monitor') {
            statusIndicator.classList.add('monitoring');
            statusIndicator.textContent = 'Monitoring';
            this.startMonitoring();
        } else {
            statusIndicator.classList.remove('monitoring');
            statusIndicator.textContent = 'Online';
            this.stopMonitoring();
        }
        
        // Send mode change to server
        fetch('/api/security/mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Mode changed:', data);
        })
        .catch(error => {
            console.error('Error changing mode:', error);
        });
    }
    
    startMonitoring() {
        this.monitoringActive = true;
        
        fetch('/api/security/monitor/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Monitoring started:', data);
        })
        .catch(error => {
            console.error('Error starting monitoring:', error);
        });
    }
    
    stopMonitoring() {
        this.monitoringActive = false;
        
        fetch('/api/security/monitor/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Monitoring stopped:', data);
        })
        .catch(error => {
            console.error('Error stopping monitoring:', error);
        });
    }
    
    showScanModal() {
        document.getElementById('scanModal').style.display = 'flex';
    }
    
    startScan() {
        const target = document.getElementById('scanTarget').value;
        const scanType = document.getElementById('scanType').value;
        const depth = document.getElementById('scanDepth').value;
        
        document.getElementById('scanModal').style.display = 'none';
        
        // Show progress
        document.getElementById('scanProgress').style.display = 'block';
        document.getElementById('scanProgressFill').style.width = '0%';
        document.getElementById('scanProgressText').textContent = 'Iniciando scan...';
        
        fetch('/api/security/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target, scanType, depth })
        })
        .then(response => response.json())
        .then(data => {
            if (data.scan_id) {
                this.pollScanProgress(data.scan_id);
            }
        })
        .catch(error => {
            console.error('Error starting scan:', error);
            document.getElementById('scanProgress').style.display = 'none';
        });
    }
    
    pollScanProgress(scanId) {
        const poll = () => {
            fetch(`/api/security/scan/${scanId}`)
                .then(response => response.json())
                .then(data => {
                    this.updateScanProgress(data.progress);
                    
                    if (data.status === 'completed') {
                        this.handleScanComplete(data.results);
                    } else if (data.status === 'failed') {
                        document.getElementById('scanProgress').style.display = 'none';
                        alert('Scan failed: ' + data.error);
                    } else {
                        setTimeout(poll, 1000);
                    }
                })
                .catch(error => {
                    console.error('Error polling scan progress:', error);
                    setTimeout(poll, 2000);
                });
        };
        poll();
    }
    
    updateScanProgress(progress) {
        document.getElementById('scanProgressFill').style.width = `${progress}%`;
        document.getElementById('scanProgressText').textContent = `Escaneando... ${progress}%`;
    }
    
    handleScanComplete(results) {
        document.getElementById('scanProgress').style.display = 'none';
        
        // Update threats
        if (results.threats) {
            results.threats.forEach(threat => {
                this.addThreat(threat);
            });
        }
        
        // Update scan results
        this.updateScanResults(results);
        
        // Update threat counts
        this.updateThreatCounts();
    }
    
    updateScanResults(results) {
        const scanResults = document.getElementById('scanResults');
        
        if (results.code_analysis) {
            this.updateResultCard('Análise de Código', results.code_analysis);
        }
        
        if (results.dependencies) {
            this.updateResultCard('Dependências', results.dependencies);
        }
        
        if (results.binaries) {
            this.updateResultCard('Binários', results.binaries);
        }
    }
    
    updateResultCard(title, data) {
        const cards = document.querySelectorAll('.result-card');
        for (const card of cards) {
            const cardTitle = card.querySelector('.result-title').textContent;
            if (cardTitle === title) {
                const stats = card.querySelector('.result-stats');
                stats.innerHTML = '';
                
                Object.entries(data).forEach(([key, value]) => {
                    const stat = document.createElement('span');
                    stat.className = 'result-stat';
                    stat.innerHTML = `${key.charAt(0).toUpperCase() + key.slice(1)}: <strong>${value}</strong>`;
                    stats.appendChild(stat);
                });
                break;
            }
        }
    }
    
    addThreat(threat) {
        this.threats.push(threat);
        
        const threatsList = document.getElementById('threatsList');
        const threatItem = document.createElement('div');
        threatItem.className = `threat-item ${threat.severity}`;
        threatItem.dataset.threatId = threat.id;
        
        const icons = {
            critical: '🔴',
            high: '🟠',
            medium: '🟡',
            low: '🟢'
        };
        
        const severities = {
            critical: 'CRÍTICA',
            high: 'ALTA',
            medium: 'MÉDIA',
            low: 'BAIXA'
        };
        
        threatItem.innerHTML = `
            <div class="threat-header">
                <span class="threat-icon">${icons[threat.severity]}</span>
                <span class="threat-severity">${severities[threat.severity]}</span>
            </div>
            <div class="threat-content">
                <span class="threat-title">${threat.title}</span>
                <span class="threat-location">${threat.location}</span>
            </div>
        `;
        
        threatsList.insertBefore(threatItem, threatsList.firstChild);
        
        this.updateThreatCounts();
    }
    
    updateThreatCounts() {
        const counts = {
            critical: 0,
            high: 0,
            medium: 0,
            low: 0
        };
        
        this.threats.forEach(threat => {
            counts[threat.severity]++;
        });
        
        document.getElementById('criticalCount').textContent = counts.critical;
        document.getElementById('highCount').textContent = counts.high;
        document.getElementById('mediumCount').textContent = counts.medium;
    }
    
    clearThreats() {
        this.threats = [];
        document.getElementById('threatsList').innerHTML = '';
        this.updateThreatCounts();
    }
    
    showThreatDetails(threatItem) {
        const threatId = threatItem.dataset.threatId;
        const threat = this.threats.find(t => t.id === threatId);
        
        if (threat) {
            alert(`Detalhes da Ameaça:\n\nTítulo: ${threat.title}\nLocalização: ${threat.location}\nDescrição: ${threat.description}\nRecomendação: ${threat.recommendation}`);
        }
    }
    
    exportReport() {
        const report = {
            timestamp: new Date().toISOString(),
            threats: this.threats,
            summary: {
                total: this.threats.length,
                critical: this.threats.filter(t => t.severity === 'critical').length,
                high: this.threats.filter(t => t.severity === 'high').length,
                medium: this.threats.filter(t => t.severity === 'medium').length,
                low: this.threats.filter(t => t.severity === 'low').length
            }
        };
        
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `security_report_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    loadProcesses() {
        fetch('/api/security/processes')
            .then(response => response.json())
            .then(data => {
                this.updateProcessList(data.processes);
            })
            .catch(error => {
                console.error('Error loading processes:', error);
            });
    }
    
    updateProcessList(processes) {
        const processList = document.getElementById('processList');
        processList.innerHTML = '';
        
        processes.forEach(process => {
            const processItem = document.createElement('div');
            processItem.className = `process-item ${process.suspicious ? 'suspicious' : 'normal'}`;
            
            processItem.innerHTML = `
                <span class="process-pid">${process.pid}</span>
                <span class="process-name">${process.name}</span>
                <span class="process-cpu">${process.cpu}%</span>
                <span class="process-mem">${process.memory}%</span>
            `;
            
            processList.appendChild(processItem);
        });
    }
    
    handleProcessAlert(process) {
        this.loadProcesses();
        
        // Add alert notification
        const alert = document.createElement('div');
        alert.className = 'threat-item critical';
        alert.innerHTML = `
            <div class="threat-header">
                <span class="threat-icon">⚠️</span>
                <span class="threat-severity">ALERTA</span>
            </div>
            <div class="threat-content">
                <span class="threat-title">Processo suspeito detectado: ${process.name}</span>
                <span class="threat-location">PID: ${process.pid}</span>
            </div>
        `;
        
        document.getElementById('threatsList').insertBefore(alert, document.getElementById('threatsList').firstChild);
    }
    
    updateNetworkTraffic(traffic) {
        // Update traffic visualization
        const trafficBars = document.querySelectorAll('.traffic-bar');
        trafficBars.forEach((bar, index) => {
            if (traffic[index] !== undefined) {
                bar.style.height = `${traffic[index]}%`;
            }
        });
    }
    
    loadThreats() {
        fetch('/api/security/threats')
            .then(response => response.json())
            .then(data => {
                data.threats.forEach(threat => {
                    this.addThreat(threat);
                });
            })
            .catch(error => {
                console.error('Error loading threats:', error);
            });
    }
}

// Initialize Security Agent page when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.securityAgent = new SecurityAgentPage();
});