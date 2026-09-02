# PROJETO GÊNESIS CÓRTEX

## Descrição do Projeto

A Gênesis Córtex é um assistente pessoal IA offline projetado para desenvolvimento de software, cybersecurity, robótica, neurociência e automação de sistema. O sistema opera 100% offline, garantindo privacidade total e independência de APIs corporativas.

## Arquitetura do Sistema

### Stack Tecnológica

- **Linguagem Principal:** Python 3.12+
- **LLM Local:** DeepSeek-R1-7B via Ollama
- **Voice:** Vosk (STT) + Piper TTS (TTS)
- **Memória:** SQLite (curto prazo) + LanceDB (longo prazo)
- **Web:** FastAPI + PWA (HTML/CSS/JS)
- **Containerização:** Docker/Podman

### Módulos Principais

#### 1. Core Engine
- **engine.py:** Orquestrador principal do sistema
- **task_executor.py:** Executor de 40+ ações do sistema
- **decision_protocol.py:** Protocolo de decisão híbrido (regras/LLM)
- **situational_awareness.py:** Consciência situacional do contexto
- **config_loader.py:** Gerenciamento de configuração YAML
- **semantic_matcher.py:** Matching semântico com Sentence-Transformers
- **local_llm.py:** Cliente Ollama para DeepSeek
- **secure_storage.py:** Armazenamento criptografado (AES-256-GCM)
- **system_actions.py:** Controle de ações do sistema operacional

#### 2. Security
- **universal_scanner.py:** Scanner multi-linguagem (7 linguagens)
- **binary_analyzer.py:** Análise estática de ELF/PE/Mach-O
- **dependency_checker.py:** Verificação de CVEs via OSV
- **report_generator.py:** Geração de relatórios Markdown
- **process_analyzer.py:** Análise avançada de processos
- **geolocation.py:** Geolocalização de IPs (offline/online)
- **packet_sniffer.py:** Captura e análise de pacotes
- **password_checker.py:** Verificador de força de senhas

#### 3. Voice
- **listener.py:** Captura de voz com Vosk
- **speaker.py:** Síntese de voz com Piper TTS
- **wake_word.py:** Detecção de "Ei Córtex"
- **conversation.py:** Gerenciador de conversação
- **background_service.py:** Serviço 24/7

#### 4. Self-Modification
- **capability_discovery.py:** Descoberta de lacunas no projeto
- **safe_editor.py:** Editor seguro com backup/rollback
- **sandbox_tester.py:** Testes em Docker antes de aplicar
- **continuous_evolution.py:** Ciclo contínuo de auto-evolução

#### 5. Web PWA
- **app.py:** FastAPI server
- **templates/index.html:** Interface neural synapse
- **static/**: CSS, JS, service-worker, manifest

## Funcionalidades Implementadas

### Motor de Regras (40+ Ações)

**Sistema:**
- system_info, disk_usage, memory_usage, network_status, running_processes

**Arquivos:**
- list_files, read_file, write_file, delete_file, create_directory

**Assistente Pessoal:**
- set_volume, set_brightness, create_note, list_notes, set_timer, set_reminder

**Segurança:**
- scan_ports, scan_processes, check_passwords, analyze_logs

**Desenvolvimento:**
- run_code, git_status, git_commit, docker_status

**Web:**
- web_search, download_file

**Conhecimento:**
- neuroscience_query, robotics_query, security_query

**Memória:**
- store_memory, retrieve_memory, search_memories

**Configuração:**
- update_config, reload_config

**Diagnóstico:**
- health_check, performance_test, diagnostic_report

**Backup:**
- create_backup, restore_backup

**Análise:**
- analyze_binary, analyze_dependencies, generate_report

**Rede:**
- ping_host, trace_route, dns_lookup

**Sistema:**
- shutdown, reboot, sleep

### Scanner de Segurança

**Linguagens Suportadas:**
- Python, Java, JavaScript, C/C++, Go, Rust, Assembly

**Regras Implementadas:**
- 300+ regras de segurança (7 arquivos YAML)
- Cobertura: eval/exec, SQL injection, XSS, buffer overflow, etc.

**Resultado Real:**
- 145 críticas + 445 altas = 590 vulnerabilidades encontradas no primeiro teste

### Sistema de Voz

**Componentes:**
- STT: Vosk (modelo pt-BR small)
- TTS: Piper TTS (Luciana/Faber)
- Wake Word: Detecção "Ei Córtex"
- Background: Serviço 24/7

**Status:**
- Implementado com fallback para modo texto

### Web Dashboard

**Características:**
- Tema Neural Synapse (dark mode)
- WebSocket para comunicação em tempo real
- PWA offline-first
- Interface responsiva

## Base de Conhecimento

### Neurociência
- **neuroanatomia_funcional.json:** Áreas de Brodmann, redes funcionais, neurotransmissores, EEG, transtorno bipolar

### Robótica
- **componentes.json:** Fontes ATX, motores DC/stepper/servo, sensores, microcontroladores, drivers

### Templates
- **fastapi_project.py:** Template para projetos FastAPI
- **docker_compose.yml:** Template para orquestração
- **dockerfile:** Template para containerização

## Configuração

### Arquivo config.yaml

**Seções Principais:**
- system: Configurações básicas do sistema
- llm: Configuração do DeepSeek via Ollama
- voice: Configuração de STT/TTS
- memory: Configuração de memória curto/longo prazo
- security: Configurações de criptografia e scanner
- web: Configuração do dashboard PWA
- self_modification: Configuração de auto-evolução

### Dependências

**requirements.txt:**
- Core: pyyaml, cryptography, psutil
- LLM: aiohttp, ollama
- ML: sentence-transformers, torch
- Web: fastapi, uvicorn, jinja2
- Security: requests
- Development: pytest, black, flake8

## Deploy

### Local

```bash
python core/engine.py
```

### Docker

```bash
docker-compose up -d
```

### Web Dashboard

```bash
python web/app.py
# Acesse: http://127.0.0.1:8000
```

## Metas e Roadmap

### Concluído ✅
- [x] Motor de regras com 40+ ações
- [x] Scanner de segurança multi-linguagem
- [x] Análise de binários
- [x] Verificação de dependências
- [x] Sistema de voz (STT/TTS)
- [x] Dashboard PWA
- [x] Auto-evolução básica
- [x] Base de conhecimento

### Em Progresso 🚧
- [ ] Integração EEG real
- [ ] Auto-correção de vulnerabilidades
- [ ] Interface PWA avançada

### Futuro 🔮
- [ ] App mobile (PWA instalável)
- [ ] IA comportamental avançada
- [ ] Previsão de ataques
- [ ] Chatbot de resposta a incidentes

## Princípios

1. **Offline-first:** 100% funcional sem internet
2. **Privacidade:** Dados locais, criptografia AES-256-GCM
3. **Autonomia:** Auto-evolução com sandbox
4. **Segurança:** Scanner integrado, análise de binários
5. **Versatilidade:** Múltiplas linguagens e domínios

## Manutenção

### Logs
- Localização: `logs/cortex.log`
- Nível: INFO (configurável)
- Rotação: 10MB, 5 backups

### Backups
- Localização: `backups/`
- Formato: timestamp + metadados
- Limpeza: Automática após 7 dias

### Atualizações
- Auto-evolução: Habilitável via config
- Sandbox: Testes em Docker antes de aplicar
- Rollback: Backup automático antes de mudanças

## Suporte

Para questões técnicas, consulte:
- README.md para instalação e uso
- Arquivos de código para implementação
- config.yaml para configuração

---

**Criadora:** Nana  
**Status:** Funcional (em evolução contínua)  
**Versão:** 1.0.0