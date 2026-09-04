// Settings Page JavaScript
class SettingsPage {
    constructor() {
        this.currentSection = 'models';
        this.settings = {};
        this.originalSettings = {};
        
        this.init();
    }
    
    init() {
        this.loadSettings();
        this.setupEventListeners();
        this.setupNavigation();
        this.setupFormListeners();
    }
    
    loadSettings() {
        fetch('/api/settings')
            .then(response => response.json())
            .then(data => {
                this.settings = data;
                this.originalSettings = JSON.parse(JSON.stringify(data));
                this.populateSettings();
            })
            .catch(error => {
                console.error('Error loading settings:', error);
            });
    }
    
    populateSettings() {
        // Models
        document.getElementById('reasoningModel').value = this.settings.models?.reasoning || 'deepseek-r1-7b';
        document.getElementById('codingModel').value = this.settings.models?.coding || 'qwen-coder-7b';
        document.getElementById('temperature').value = (this.settings.models?.temperature || 0.7) * 100;
        document.getElementById('maxTokens').value = this.settings.models?.max_tokens || 4096;
        document.getElementById('llmTimeout').value = this.settings.models?.timeout || 30;
        
        // Voice
        document.getElementById('voiceEngine').value = this.settings.voice?.engine || 'piper';
        document.getElementById('piperVoice').value = this.settings.voice?.piper_voice || 'luciana';
        document.getElementById('clonedVoice').value = this.settings.voice?.cloned_voice || '';
        document.getElementById('voiceSpeed').value = (this.settings.voice?.speed || 1.0) * 100;
        document.getElementById('voicePitch').value = this.settings.voice?.pitch || 0;
        document.getElementById('voiceVolume').value = this.settings.voice?.volume || 70;
        document.getElementById('voiceProfile').value = this.settings.voice?.profile || 'casual';
        
        // Memory
        document.getElementById('memoryType').value = this.settings.memory?.type || 'hybrid';
        document.getElementById('memorySize').value = this.settings.memory?.size || 1024;
        document.getElementById('memoryRetention').value = this.settings.memory?.retention || 30;
        document.getElementById('similarityThreshold').value = (this.settings.memory?.similarity_threshold || 0.7) * 100;
        
        // Security
        document.getElementById('permissionLevel').value = this.settings.security?.permission_level || 'moderate';
        document.getElementById('confirmDangerous').checked = this.settings.security?.confirm_dangerous !== false;
        document.getElementById('auditTrail').checked = this.settings.security?.audit_trail !== false;
        document.getElementById('allowedPaths').value = this.settings.security?.allowed_paths?.join('\n') || '/home/nana/cortex';
        document.getElementById('encryptionAlgorithm').value = this.settings.security?.encryption || 'aes-256-gcm';
        
        // Evolution
        document.getElementById('autoEvolution').checked = this.settings.evolution?.enabled || false;
        document.getElementById('cycleInterval').value = this.settings.evolution?.cycle_interval || 24;
        document.getElementById('maxIterations').value = this.settings.evolution?.max_iterations || 5;
        document.getElementById('dockerSandbox').checked = this.settings.evolution?.docker_sandbox !== false;
        document.getElementById('autoBackup').checked = this.settings.evolution?.auto_backup !== false;
        
        // Appearance
        this.setTheme(this.settings.appearance?.theme || 'neural-synapse');
        document.getElementById('fontSize').value = this.settings.appearance?.font_size || 'medium';
        document.getElementById('animations').checked = this.settings.appearance?.animations !== false;
        document.getElementById('notifications').checked = this.settings.appearance?.notifications !== false;
        
        // Backup
        document.getElementById('autoBackupEnabled').checked = this.settings.backup?.auto_enabled !== false;
        document.getElementById('backupFrequency').value = this.settings.backup?.frequency || 'daily';
        document.getElementById('backupLocation').value = this.settings.backup?.location || '/home/nana/cortex/backups';
        document.getElementById('backupRetention').value = this.settings.backup?.retention || 7;
        
        // Personality
        document.getElementById('personalityProfile').value = this.settings.personality?.profile || 'casual';
        document.getElementById('responseTone').value = this.settings.personality?.tone || 'neutral';
        document.getElementById('useEmojis').checked = this.settings.personality?.use_emojis !== false;
        document.getElementById('detailLevel').value = this.settings.personality?.detail_level || 'balanced';
        document.getElementById('assistantName').value = this.settings.personality?.assistant_name || 'Córtex';
        
        // Update range values
        this.updateRangeValues();
        
        // Load backup list
        this.loadBackupList();
    }
    
    updateRangeValues() {
        // Temperature
        const tempValue = document.getElementById('temperature').value;
        document.querySelector('#temperature + .range-value').textContent = (tempValue / 100).toFixed(1);
        
        // Voice Speed
        const speedValue = document.getElementById('voiceSpeed').value;
        document.querySelector('#voiceSpeed + .range-value').textContent = (speedValue / 100).toFixed(1) + 'x';
        
        // Voice Pitch
        const pitchValue = document.getElementById('voicePitch').value;
        document.querySelector('#voicePitch + .range-value').textContent = pitchValue;
        
        // Voice Volume
        const volumeValue = document.getElementById('voiceVolume').value;
        document.querySelector('#voiceVolume + .range-value').textContent = volumeValue + '%';
        
        // Similarity Threshold
        const similarityValue = document.getElementById('similarityThreshold').value;
        document.querySelector('#similarityThreshold + .range-value').textContent = (similarityValue / 100).toFixed(1);
    }
    
    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const section = item.dataset.section;
                this.switchSection(section);
            });
        });
    }
    
    switchSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.section === section);
        });
        
        // Update content
        document.querySelectorAll('.settings-section').forEach(sec => {
            sec.classList.toggle('active', sec.id === `${section}-section`);
        });
        
        this.currentSection = section;
    }
    
    setupFormListeners() {
        // Range inputs
        document.querySelectorAll('input[type="range"]').forEach(input => {
            input.addEventListener('input', () => {
                this.updateRangeValues();
            });
        });
        
        // Theme cards
        document.querySelectorAll('.theme-card').forEach(card => {
            card.addEventListener('click', () => {
                const theme = card.dataset.theme;
                this.setTheme(theme);
            });
        });
        
        // Save button
        document.getElementById('saveButton').addEventListener('click', () => {
            this.saveSettings();
        });
        
        // Reset button
        document.getElementById('resetButton').addEventListener('click', () => {
            this.resetSettings();
        });
        
        // Back button
        document.getElementById('backButton').addEventListener('click', () => {
            window.location.href = '/';
        });
        
        // Test models
        document.getElementById('testModelsButton').addEventListener('click', () => {
            this.testModels();
        });
        
        // Test voice
        document.getElementById('testVoiceButton').addEventListener('click', () => {
            this.testVoice();
        });
        
        // Download voices
        document.getElementById('downloadVoicesButton').addEventListener('click', () => {
            this.downloadVoices();
        });
        
        // Backup memory
        document.getElementById('backupMemoryButton').addEventListener('click', () => {
            this.backupMemory();
        });
        
        // Clear memory
        document.getElementById('clearMemoryButton').addEventListener('click', () => {
            this.clearMemory();
        });
        
        // Export audit
        document.getElementById('exportAuditButton').addEventListener('click', () => {
            this.exportAudit();
        });
        
        // Run evolution
        document.getElementById('runEvolutionButton').addEventListener('click', () => {
            this.runEvolution();
        });
        
        // Create backup
        document.getElementById('createBackupButton').addEventListener('click', () => {
            this.createBackup();
        });
        
        // Restore backup
        document.getElementById('restoreBackupButton').addEventListener('click', () => {
            this.restoreBackup();
        });
        
        // Test personality
        document.getElementById('testPersonalityButton').addEventListener('click', () => {
            this.testPersonality();
        });
    }
    
    setupEventListeners() {
        // Additional event listeners if needed
    }
    
    setTheme(theme) {
        document.body.className = `theme-${theme}`;
        
        // Update theme cards
        document.querySelectorAll('.theme-card').forEach(card => {
            card.classList.toggle('active', card.dataset.theme === theme);
        });
        
        // Update settings
        this.settings.appearance = this.settings.appearance || {};
        this.settings.appearance.theme = theme;
    }
    
    collectSettings() {
        return {
            models: {
                reasoning: document.getElementById('reasoningModel').value,
                coding: document.getElementById('codingModel').value,
                temperature: document.getElementById('temperature').value / 100,
                max_tokens: parseInt(document.getElementById('maxTokens').value),
                timeout: parseInt(document.getElementById('llmTimeout').value)
            },
            voice: {
                engine: document.getElementById('voiceEngine').value,
                piper_voice: document.getElementById('piperVoice').value,
                cloned_voice: document.getElementById('clonedVoice').value,
                speed: document.getElementById('voiceSpeed').value / 100,
                pitch: parseInt(document.getElementById('voicePitch').value),
                volume: parseInt(document.getElementById('voiceVolume').value),
                profile: document.getElementById('voiceProfile').value
            },
            memory: {
                type: document.getElementById('memoryType').value,
                size: parseInt(document.getElementById('memorySize').value),
                retention: parseInt(document.getElementById('memoryRetention').value),
                similarity_threshold: document.getElementById('similarityThreshold').value / 100
            },
            security: {
                permission_level: document.getElementById('permissionLevel').value,
                confirm_dangerous: document.getElementById('confirmDangerous').checked,
                audit_trail: document.getElementById('auditTrail').checked,
                allowed_paths: document.getElementById('allowedPaths').value.split('\n').filter(p => p.trim()),
                encryption: document.getElementById('encryptionAlgorithm').value
            },
            evolution: {
                enabled: document.getElementById('autoEvolution').checked,
                cycle_interval: parseInt(document.getElementById('cycleInterval').value),
                max_iterations: parseInt(document.getElementById('maxIterations').value),
                docker_sandbox: document.getElementById('dockerSandbox').checked,
                auto_backup: document.getElementById('autoBackup').checked
            },
            appearance: {
                theme: document.querySelector('.theme-card.active')?.dataset.theme || 'neural-synapse',
                font_size: document.getElementById('fontSize').value,
                animations: document.getElementById('animations').checked,
                notifications: document.getElementById('notifications').checked
            },
            backup: {
                auto_enabled: document.getElementById('autoBackupEnabled').checked,
                frequency: document.getElementById('backupFrequency').value,
                location: document.getElementById('backupLocation').value,
                retention: parseInt(document.getElementById('backupRetention').value)
            },
            personality: {
                profile: document.getElementById('personalityProfile').value,
                tone: document.getElementById('responseTone').value,
                use_emojis: document.getElementById('useEmojis').checked,
                detail_level: document.getElementById('detailLevel').value,
                assistant_name: document.getElementById('assistantName').value
            }
        };
    }
    
    saveSettings() {
        const newSettings = this.collectSettings();
        
        fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newSettings)
        })
        .then(response => response.json())
        .then(data => {
            this.settings = newSettings;
            this.originalSettings = JSON.parse(JSON.stringify(newSettings));
            this.showNotification('Configurações salvas com sucesso!');
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            this.showNotification('Erro ao salvar configurações', 'error');
        });
    }
    
    resetSettings() {
        if (confirm('Tem certeza que deseja resetar as configurações para os valores originais?')) {
            this.settings = JSON.parse(JSON.stringify(this.originalSettings));
            this.populateSettings();
            this.showNotification('Configurações resetadas');
        }
    }
    
    testModels() {
        const reasoningModel = document.getElementById('reasoningModel').value;
        const codingModel = document.getElementById('codingModel').value;
        
        this.showNotification('Testando modelos...');
        
        fetch('/api/models/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reasoning_model: reasoningModel, coding_model: codingModel })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Modelos testados com sucesso!');
            } else {
                this.showNotification('Erro ao testar modelos: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error testing models:', error);
            this.showNotification('Erro ao testar modelos', 'error');
        });
    }
    
    testVoice() {
        const engine = document.getElementById('voiceEngine').value;
        const voice = engine === 'piper' ? document.getElementById('piperVoice').value : document.getElementById('clonedVoice').value;
        
        this.showNotification('Testando voz...');
        
        fetch('/api/voice/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ engine, voice })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Voz testada com sucesso!');
            } else {
                this.showNotification('Erro ao testar voz: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error testing voice:', error);
            this.showNotification('Erro ao testar voz', 'error');
        });
    }
    
    downloadVoices() {
        this.showNotification('Baixando vozes do Piper...');
        
        fetch('/api/voice/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Vozes baixadas com sucesso!');
            } else {
                this.showNotification('Erro ao baixar vozes: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error downloading voices:', error);
            this.showNotification('Erro ao baixar vozes', 'error');
        });
    }
    
    backupMemory() {
        if (confirm('Deseja criar um backup da memória atual?')) {
            this.showNotification('Criando backup da memória...');
            
            fetch('/api/memory/backup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('Backup criado com sucesso!');
                } else {
                    this.showNotification('Erro ao criar backup: ' + data.error, 'error');
                }
            })
            .catch(error => {
                console.error('Error backing up memory:', error);
                this.showNotification('Erro ao criar backup', 'error');
            });
        }
    }
    
    clearMemory() {
        if (confirm('Tem certeza que deseja limpar toda a memória? Esta ação não pode ser desfeita.')) {
            this.showNotification('Limpando memória...');
            
            fetch('/api/memory/clear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('Memória limpa com sucesso!');
                } else {
                    this.showNotification('Erro ao limpar memória: ' + data.error, 'error');
                }
            })
            .catch(error => {
                console.error('Error clearing memory:', error);
                this.showNotification('Erro ao limpar memória', 'error');
            });
        }
    }
    
    exportAudit() {
        this.showNotification('Exportando audit trail...');
        
        fetch('/api/security/audit/export')
            .then(response => response.blob())
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `audit_trail_${Date.now()}.json`;
                a.click();
                URL.revokeObjectURL(url);
                this.showNotification('Audit trail exportado com sucesso!');
            })
            .catch(error => {
                console.error('Error exporting audit:', error);
                this.showNotification('Erro ao exportar audit', 'error');
            });
    }
    
    runEvolution() {
        if (confirm('Deseja executar um ciclo de evolução manual?')) {
            this.showNotification('Executando ciclo de evolução...');
            
            fetch('/api/evolution/cycle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    this.showNotification('Ciclo de evolução concluído com sucesso!');
                } else {
                    this.showNotification('Erro no ciclo: ' + data.error, 'error');
                }
            })
            .catch(error => {
                console.error('Error running evolution:', error);
                this.showNotification('Erro ao executar ciclo', 'error');
            });
        }
    }
    
    createBackup() {
        this.showNotification('Criando backup do sistema...');
        
        fetch('/api/backup/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Backup criado com sucesso!');
                this.loadBackupList();
            } else {
                this.showNotification('Erro ao criar backup: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error creating backup:', error);
            this.showNotification('Erro ao criar backup', 'error');
        });
    }
    
    restoreBackup() {
        const backupName = prompt('Nome do backup para restaurar:');
        if (backupName) {
            if (confirm(`Tem certeza que deseja restaurar o backup "${backupName}"? Esta ação não pode ser desfeita.`)) {
                this.showNotification('Restaurando backup...');
                
                fetch('/api/backup/restore', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ backup_name: backupName })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.showNotification('Backup restaurado com sucesso! Recarregando...');
                        setTimeout(() => location.reload(), 2000);
                    } else {
                        this.showNotification('Erro ao restaurar backup: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error restoring backup:', error);
                    this.showNotification('Erro ao restaurar backup', 'error');
                });
            }
        }
    }
    
    loadBackupList() {
        fetch('/api/backup/list')
            .then(response => response.json())
            .then(data => {
                this.updateBackupList(data.backups);
            })
            .catch(error => {
                console.error('Error loading backup list:', error);
            });
    }
    
    updateBackupList(backups) {
        const backupItems = document.getElementById('backupItems');
        backupItems.innerHTML = '';
        
        backups.forEach(backup => {
            const backupItem = document.createElement('div');
            backupItem.className = 'backup-item';
            
            const date = new Date(backup.timestamp).toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            backupItem.innerHTML = `
                <span class="backup-name">${backup.name}</span>
                <span class="backup-size">${backup.size}</span>
                <span class="backup-date">${date}</span>
                <button class="backup-action" data-backup="${backup.name}">Restaurar</button>
            `;
            
            backupItems.appendChild(backupItem);
        });
        
        // Add event listeners to restore buttons
        document.querySelectorAll('.backup-action').forEach(button => {
            button.addEventListener('click', (e) => {
                const backupName = e.target.dataset.backup;
                if (confirm(`Tem certeza que deseja restaurar o backup "${backupName}"?`)) {
                    this.restoreBackupByName(backupName);
                }
            });
        });
    }
    
    restoreBackupByName(backupName) {
        this.showNotification('Restaurando backup...');
        
        fetch('/api/backup/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ backup_name })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Backup restaurado com sucesso! Recarregando...');
                setTimeout(() => location.reload(), 2000);
            } else {
                this.showNotification('Erro ao restaurar backup: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error restoring backup:', error);
            this.showNotification('Erro ao restaurar backup', 'error');
        });
    }
    
    testPersonality() {
        const profile = document.getElementById('personalityProfile').value;
        const tone = document.getElementById('responseTone').value;
        
        this.showNotification('Testando personalidade...');
        
        fetch('/api/personality/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile, tone })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Resposta de teste com personalidade "${profile}":\n\n${data.response}`);
            } else {
                this.showNotification('Erro ao testar personalidade: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error testing personality:', error);
            this.showNotification('Erro ao testar personalidade', 'error');
        });
    }
    
    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? 'var(--success)' : 'var(--error)'};
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

// Initialize Settings page when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.settingsPage = new SettingsPage();
});