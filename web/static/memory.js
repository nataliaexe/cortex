// Memory & Learning Page JavaScript
class MemoryPage {
    constructor() {
        this.ws = null;
        this.learningEnabled = false;
        this.searchResults = [];
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadMemoryData();
        this.loadEvolutionMetrics();
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
        if (data.type === 'learning_status') {
            this.updateLearningStatus(data.enabled);
        } else if (data.type === 'learning_cycle_complete') {
            this.handleLearningCycleComplete(data.results);
        } else if (data.type === 'new_insight') {
            this.addInsight(data.insight);
        } else if (data.type === 'memory_update') {
            this.updateMemoryStats(data.stats);
        }
    }
    
    setupEventListeners() {
        // Enable learning button
        document.getElementById('enableLearningButton').addEventListener('click', () => {
            this.toggleLearning();
        });
        
        // Run cycle button
        document.getElementById('runCycleButton').addEventListener('click', () => {
            this.runLearningCycle();
        });
        
        // Back button
        document.getElementById('backButton').addEventListener('click', () => {
            window.location.href = '/';
        });
        
        // Search
        document.getElementById('searchButton').addEventListener('click', () => {
            this.searchMemory();
        });
        
        document.getElementById('memorySearch').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchMemory();
            }
        });
        
        // Knowledge cards
        document.querySelectorAll('.knowledge-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const card = e.target.closest('.knowledge-card');
                const category = card.querySelector('.knowledge-category').textContent;
                this.exploreKnowledge(category);
            });
        });
        
        // Search results
        document.getElementById('searchResults').addEventListener('click', (e) => {
            const result = e.target.closest('.search-result');
            if (result) {
                this.showSearchResultDetails(result);
            }
        });
    }
    
    loadMemoryData() {
        // Load learning timeline
        this.loadLearningTimeline();
        
        // Load knowledge base stats
        this.loadKnowledgeStats();
        
        // Load insights
        this.loadInsights();
    }
    
    loadLearningTimeline() {
        fetch('/api/evolution/timeline')
            .then(response => response.json())
            .then(data => {
                this.updateTimeline(data.timeline);
            })
            .catch(error => {
                console.error('Error loading timeline:', error);
            });
    }
    
    updateTimeline(timeline) {
        const timelineContainer = document.getElementById('learningTimeline');
        timelineContainer.innerHTML = '';
        
        timeline.forEach(item => {
            const timelineItem = document.createElement('div');
            timelineItem.className = 'timeline-item';
            
            timelineItem.innerHTML = `
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                    <span class="timeline-date">${item.date}</span>
                    <span class="timeline-title">${item.title}</span>
                    <span class="timeline-description">${item.description}</span>
                    <span class="timeline-stats">${item.stats}</span>
                </div>
            `;
            
            timelineContainer.appendChild(timelineItem);
        });
        
        document.getElementById('cycleCount').textContent = `${timeline.length} Ciclos`;
    }
    
    loadKnowledgeStats() {
        fetch('/api/knowledge/stats')
            .then(response => response.json())
            .then(data => {
                this.updateKnowledgeStats(data);
            })
            .catch(error => {
                console.error('Error loading knowledge stats:', error);
            });
    }
    
    updateKnowledgeStats(stats) {
        const cards = document.querySelectorAll('.knowledge-card');
        
        cards.forEach(card => {
            const category = card.querySelector('.knowledge-category').textContent.toLowerCase();
            const categoryStats = stats[category];
            
            if (categoryStats) {
                const statsContainer = card.querySelector('.knowledge-stats');
                statsContainer.innerHTML = '';
                
                Object.entries(categoryStats).forEach(([key, value]) => {
                    const stat = document.createElement('span');
                    stat.className = 'knowledge-stat';
                    stat.innerHTML = `${key.charAt(0).toUpperCase() + key.slice(1)}: <strong>${value}</strong>`;
                    statsContainer.appendChild(stat);
                });
            }
        });
        
        let totalItems = 0;
        Object.values(stats).forEach(categoryStats => {
            Object.values(categoryStats).forEach(value => {
                totalItems += parseInt(value) || 0;
            });
        });
        
        document.getElementById('knowledgeCount').textContent = `${totalItems} Itens`;
    }
    
    loadInsights() {
        fetch('/api/evolution/insights')
            .then(response => response.json())
            .then(data => {
                this.updateInsights(data.insights);
            })
            .catch(error => {
                console.error('Error loading insights:', error);
            });
    }
    
    updateInsights(insights) {
        const insightsList = document.getElementById('insightsList');
        insightsList.innerHTML = '';
        
        insights.forEach(insight => {
            const insightItem = document.createElement('div');
            insightItem.className = 'insight-item';
            
            const icons = {
                optimization: '💡',
                security: '🔍',
                usage: '📈',
                performance: '⚡',
                pattern: '🔮'
            };
            
            insightItem.innerHTML = `
                <div class="insight-icon">${icons[insight.type] || '💡'}</div>
                <div class="insight-content">
                    <span class="insight-title">${insight.title}</span>
                    <span class="insight-description">${insight.description}</span>
                    <span class="insight-time">${this.formatTime(insight.timestamp)}</span>
                </div>
            `;
            
            insightsList.appendChild(insightItem);
        });
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (days > 0) {
            return `${days} dia${days > 1 ? 's' : ''} atrás`;
        } else if (hours > 0) {
            return `${hours} hora${hours > 1 ? 's' : ''} atrás`;
        } else if (minutes > 0) {
            return `${minutes} minuto${minutes > 1 ? 's' : ''} atrás`;
        } else {
            return 'Agora mesmo';
        }
    }
    
    loadEvolutionMetrics() {
        fetch('/api/evolution/metrics')
            .then(response => response.json())
            .then(data => {
                this.updateEvolutionMetrics(data.metrics);
            })
            .catch(error => {
                console.error('Error loading evolution metrics:', error);
            });
    }
    
    updateEvolutionMetrics(metrics) {
        document.getElementById('cyclesCompleted').textContent = metrics.cycles_completed || 0;
        document.getElementById('improvementsApplied').textContent = metrics.improvements_applied || 0;
        document.getElementById('patternsDiscovered').textContent = metrics.patterns_discovered || 0;
        document.getElementById('bugsFixed').textContent = metrics.bugs_fixed || 0;
        document.getElementById('performanceGain').textContent = `${(metrics.performance_gain || 0).toFixed(1)}%`;
        
        // Update memory stats
        document.getElementById('embeddingCount').textContent = metrics.embedding_count || 0;
        document.getElementById('solutionCount').textContent = metrics.solution_count || 0;
        document.getElementById('errorCount').textContent = metrics.error_count || 0;
        
        // Update memory usage
        const memoryUsage = metrics.memory_usage || 0;
        document.getElementById('memoryFill').style.width = `${memoryUsage}%`;
        document.getElementById('memoryText').textContent = `${memoryUsage.toFixed(1)}% usado`;
    }
    
    toggleLearning() {
        const button = document.getElementById('enableLearningButton');
        
        if (this.learningEnabled) {
            // Disable learning
            fetch('/api/evolution/disable', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                this.updateLearningStatus(false);
                button.textContent = '▶️ Habilitar Learning';
            })
            .catch(error => {
                console.error('Error disabling learning:', error);
            });
        } else {
            // Enable learning
            fetch('/api/evolution/enable', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                this.updateLearningStatus(true);
                button.textContent = '⏸️ Desabilitar Learning';
            })
            .catch(error => {
                console.error('Error enabling learning:', error);
            });
        }
    }
    
    updateLearningStatus(enabled) {
        this.learningEnabled = enabled;
        const statusElement = document.getElementById('learningStatus');
        const button = document.getElementById('enableLearningButton');
        
        if (enabled) {
            statusElement.textContent = 'Learning: Enabled';
            statusElement.classList.add('active');
            button.textContent = '⏸️ Desabilitar Learning';
        } else {
            statusElement.textContent = 'Learning: Disabled';
            statusElement.classList.remove('active');
            button.textContent = '▶️ Habilitar Learning';
        }
    }
    
    runLearningCycle() {
        const button = document.getElementById('runCycleButton');
        button.disabled = true;
        button.textContent = '⏳ Executando...';
        
        fetch('/api/evolution/cycle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'completed') {
                this.handleLearningCycleComplete(data);
            } else {
                alert('Erro ao executar ciclo: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error running learning cycle:', error);
            alert('Erro ao executar ciclo de aprendizado');
        })
        .finally(() => {
            button.disabled = false;
            button.textContent = '🔄 Executar Ciclo';
        });
    }
    
    handleLearningCycleComplete(results) {
        // Add to timeline
        const timelineContainer = document.getElementById('learningTimeline');
        const timelineItem = document.createElement('div');
        timelineItem.className = 'timeline-item';
        
        const now = new Date().toISOString();
        const date = new Date(now).toLocaleString('pt-BR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        timelineItem.innerHTML = `
            <div class="timeline-marker"></div>
            <div class="timeline-content">
                <span class="timeline-date">${date}</span>
                <span class="timeline-title">Ciclo de Aprendizado #${results.cycle_id}</span>
                <span class="timeline-description">${results.summary}</span>
                <span class="timeline-stats">+${results.improvements_applied} melhorias aplicadas</span>
            </div>
        `;
        
        timelineContainer.insertBefore(timelineItem, timelineContainer.firstChild);
        
        // Update metrics
        this.loadEvolutionMetrics();
        
        // Show notification
        this.showNotification('Ciclo de aprendizado concluído com sucesso!');
    }
    
    searchMemory() {
        const query = document.getElementById('memorySearch').value.trim();
        
        if (!query) {
            return;
        }
        
        fetch('/api/memory/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        })
        .then(response => response.json())
        .then(data => {
            this.updateSearchResults(data.results);
        })
        .catch(error => {
            console.error('Error searching memory:', error);
        });
    }
    
    updateSearchResults(results) {
        const searchResultsContainer = document.getElementById('searchResults');
        searchResultsContainer.innerHTML = '';
        
        if (results.length === 0) {
            searchResultsContainer.innerHTML = '<div class="no-results">Nenhum resultado encontrado</div>';
            return;
        }
        
        results.forEach(result => {
            const searchResult = document.createElement('div');
            searchResult.className = 'search-result';
            searchResult.dataset.resultId = result.id;
            
            searchResult.innerHTML = `
                <div class="result-header">
                    <span class="result-score">${result.score.toFixed(2)}</span>
                    <span class="result-type">${result.type}</span>
                </div>
                <div class="result-content">
                    <span class="result-title">${result.title}</span>
                    <span class="result-description">${result.description}</span>
                </div>
            `;
            
            searchResultsContainer.appendChild(searchResult);
        });
    }
    
    showSearchResultDetails(resultElement) {
        const resultId = resultElement.dataset.resultId;
        
        fetch(`/api/memory/result/${resultId}`)
            .then(response => response.json())
            .then(data => {
                alert(`Detalhes:\n\nTítulo: ${data.title}\nTipo: ${data.type}\nDescrição: ${data.description}\nConteúdo: ${data.content}`);
            })
            .catch(error => {
                console.error('Error loading result details:', error);
            });
    }
    
    exploreKnowledge(category) {
        // Navigate to knowledge explorer or show modal
        alert(`Explorando categoria: ${category}\n\nFuncionalidade de exploração de conhecimento será implementada em breve.`);
    }
    
    addInsight(insight) {
        const insightsList = document.getElementById('insightsList');
        const insightItem = document.createElement('div');
        insightItem.className = 'insight-item';
        
        const icons = {
            optimization: '💡',
            security: '🔍',
            usage: '📈',
            performance: '⚡',
            pattern: '🔮'
        };
        
        insightItem.innerHTML = `
            <div class="insight-icon">${icons[insight.type] || '💡'}</div>
            <div class="insight-content">
                <span class="insight-title">${insight.title}</span>
                <span class="insight-description">${insight.description}</span>
                <span class="insight-time">Agora mesmo</span>
            </div>
        `;
        
        insightsList.insertBefore(insightItem, insightsList.firstChild);
        
        // Keep only last 10 insights
        while (insightsList.children.length > 10) {
            insightsList.removeChild(insightsList.lastChild);
        }
    }
    
    updateMemoryStats(stats) {
        document.getElementById('embeddingCount').textContent = stats.embeddings || 0;
        document.getElementById('solutionCount').textContent = stats.solutions || 0;
        document.getElementById('errorCount').textContent = stats.errors || 0;
        
        const memoryUsage = stats.usage || 0;
        document.getElementById('memoryFill').style.width = `${memoryUsage}%`;
        document.getElementById('memoryText').textContent = `${memoryUsage.toFixed(1)}% usado`;
    }
    
    showNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success);
            color: var(--bg-primary);
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Initialize Memory page when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.memoryPage = new MemoryPage();
});