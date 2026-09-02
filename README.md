# Gênesis Córtex - IA Assistente Pessoal Offline

**Status:** Funcional (em evolução contínua)  
**Arquitetura:** Híbrida (Motor de Regras + LLM Local + Memória Vetorial + Auto-Evolução)

## 🌟 Visão Geral

A Gênesis Córtex (apelido: Córtex / Cort / CTX) é uma **assistente pessoal e ferramenta de programação e cybersecurity offline** projetada para:

- **Desenvolvimento full-stack** (Python, JavaScript, Java, C, Assembly, Go, Rust, Kernel Linux)
- **Cybersecurity** (scanner universal de vulnerabilidades, análise de binários, verificação de dependências)
- **Robótica com lixo eletrônico** (componentes de sucata, motores, sensores, EEG DIY)
- **Neurociência** (neuroanatomia funcional, farmacologia bipolar, EEG, modelos computacionais)
- **Assistência pessoal** (notas, voz, lembretes, automação de sistema)

**Princípio fundamental:** 100% offline, privada, sem filtros corporativos, sem APIs pagas.

## 🏗️ Arquitetura Técnica

### Stack Principal

| Camada | Tecnologia | Justificativa |
|--------|------------|---------------|
| **Core Engine** | Python 3.12+ | AST, subprocess, threading, integração SO |
| **Voz (STT)** | Vosk (modelo pt-BR small) | 100% offline, leve, português |
| **Voz (TTS)** | Piper TTS | Offline, vozes M/F (Luciana/Faber) |
| **LLM Local** | DeepSeek-R1-7B via Ollama | Conversa fluida, raciocínio, offline |
| **Busca Semântica** | Sentence-Transformers (MiniLM) | Matching de intenções além de palavras-chave |
| **Memória Curto Prazo** | SQLite | Conversas recentes, estado da sessão |
| **Memória Longo Prazo** | LanceDB (vetorial) | Embeddings, busca semântica |
| **Comunicação** | Redis (localhost) | Pub/sub entre módulos |
| **Containerização** | Docker/Podman | Sandbox de auto-evolução |
| **Interface** | PWA (FastAPI + HTML/CSS/JS) | Dashboard local |

## 📁 Estrutura do Projeto

```
cortex/
├── core/                          # Motor principal
│   ├── engine.py                  # Orquestrador principal
│   ├── task_executor.py           # Executor de ações (40+ métodos)
│   ├── decision_protocol.py       # Protocolo de decisão 50/50
│   ├── situational_awareness.py   # Consciência situacional
│   ├── config_loader.py           # Carregador de config YAML
│   ├── semantic_matcher.py        # Matching semântico (MiniLM)
│   ├── local_llm.py               # Cliente Ollama (DeepSeek)
│   ├── secure_storage.py          # Criptografia AES-256-GCM
│   ├── system_actions.py          # Controle de SO
│   └── self_modification/         # Auto-evolução
│       ├── capability_discovery.py
│       ├── safe_editor.py
│       ├── sandbox_tester.py
│       └── continuous_evolution.py
├── security/                      # Módulos de segurança
│   ├── universal_scanner.py       # Scanner multi-linguagem
│   ├── binary_analyzer.py         # Análise de ELF/PE estática
│   ├── dependency_checker.py       # OSV local (CVEs conhecidas)
│   ├── report_generator.py        # Relatórios Markdown
│   ├── process_analyzer.py        # Análise de processos
│   ├── geolocation.py             # Geolocalização de IPs
│   ├── packet_sniffer.py          # Análise de pacotes
│   ├── password_checker.py        # Verificador de senhas
│   └── rules/                     # Regras de segurança
│       ├── python.yaml
│       ├── java.yaml
│       ├── javascript.yaml
│       ├── c_cpp.yaml
│       ├── go.yaml
│       ├── rust.yaml
│       └── assembly.yaml
├── voice/                         # Módulos de voz
│   ├── listener.py                # Captura com Vosk
│   ├── speaker.py                 # Piper TTS (switch M/F)
│   ├── wake_word.py               # Detecção "Ei Córtex"
│   ├── conversation.py            # Matching de intenções
│   └── background_service.py      # Wake word 24/7
├── personality/                   # Personalidade
│   ├── base_training.json         # 102+ intents
│   ├── custom_overrides.json      # Overrides manuais
│   └── voice_profiles/            # Perfis de voz
│       ├── feminino.toml
│       └── masculino.toml
├── knowledge_base/                # Base de conhecimento
│   ├── neurociencia/
│   │   └── neuroanatomia_funcional.json
│   ├── robotica_lixo/
│   │   └── componentes.json
│   └── templates/
│       ├── fastapi_project.py
│       ├── docker_compose.yml
│       └── dockerfile
├── web/                           # PWA Dashboard
│   ├── app.py                     # FastAPI server
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       ├── app.js
│       ├── service-worker.js
│       └── manifest.json
├── config.yaml                    # Configuração principal
├── requirements.txt               # Dependências Python
├── Dockerfile                     # Containerização
├── docker-compose.yml             # Orquestração
└── README.md                      # Este arquivo
```

## 🚀 Instalação e Uso

### Pré-requisitos

- Python 3.12+
- Docker/Podman (opcional, para sandbox)
- Ollama (para LLM local)

### Instalação

```bash
# Clone o repositório
git clone <repository-url>
cd cortex

# Cria ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instala dependências
pip install -r requirements.txt

# Instala Ollama (para LLM)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull deepseek-r1:7b
```

### Configuração

Edite `config.yaml` conforme suas necessidades:

```yaml
llm:
  enabled: true
  provider: "ollama"
  model: "deepseek-r1:7b"
  api_url: "http://localhost:11434"

voice:
  enabled: false  # Requer modelos Vosk/Piper
```

### Execução

```bash
# Modo interativo (CLI)
python core/engine.py

# Serviço de voz em background
python voice/background_service.py

# Dashboard web
python web/app.py
# Acesse: http://127.0.0.1:8000

# Docker Compose
docker-compose up -d
```

## 🔧 Funcionalidades

### Motor de Regras (40+ ações)

- **Sistema:** info, disco, memória, rede, processos
- **Arquivos:** listar, ler, escrever, deletar, criar diretórios
- **Assistente:** volume, brilho, notas, timer, lembretes
- **Segurança:** scan de portas, processos, senhas, logs
- **Desenvolvimento:** executar código, git, docker
- **Rede:** ping, traceroute, DNS lookup

### Scanner de Segurança

- **Multi-linguagem:** Python, Java, JavaScript, C/C++, Go, Rust, Assembly
- **Análise de binários:** ELF, PE, Mach-O
- **Verificação de dependências:** OSV local para CVEs
- **Relatórios:** Markdown com SHA-256

### Sistema de Voz

- **STT:** Vosk (modelo pt-BR)
- **TTS:** Piper TTS (Luciana/Faber)
- **Wake Word:** Detecção "Ei Córtex"
- **Background:** Serviço 24/7

### Auto-Evolução

- **Descoberta de lacunas:** Análise de PROJETO.md vs implementação
- **Editor seguro:** Backup automático + rollback
- **Sandbox:** Testes em Docker antes de aplicar
- **Evolução contínua:** Ciclo automático de melhorias

### Dashboard PWA

- **Tema:** Neural Synapse (dark mode)
- **WebSocket:** Comunicação em tempo real
- **Offline-first:** Service Worker + manifest
- **Responsivo:** Mobile-friendly

## 📊 Estatísticas do Projeto

- **Arquivos Python:** 20+ módulos
- **Regras de segurança:** 7 linguagens, 300+ regras
- **Intenções:** 102+ intents treinadas
- **Linhas de código:** ~15,000
- **Funcionalidades:** 50+ ações implementadas

## 🔒 Segurança

- **Criptografia:** AES-256-GCM para memórias
- **Sandbox:** Docker para auto-evolução
- **Offline-first:** Sem APIs externas
- **Privacidade:** Dados locais apenas

### Governança de ferramentas

As ferramentas do Córtex passam por uma política central em `core/governance.py`:

- leituras e escritas são limitadas a `governance.allowed_paths`;
- escrita, exclusão, comandos, execução de código, commits, downloads e controle de energia exigem confirmação explícita;
- comandos aceitam somente `argv` (não `shell=True`) e ações perigosas são bloqueadas;
- downloads ficam em quarentena lógica: são validados por tamanho/SHA-256 e nunca executados;
- `logs/audit.jsonl` registra solicitação, decisão e resultado, com segredos mascarados.

Para uma integração de UI/API, passe a confirmação no contexto da execução:

```python
await executor.execute_intent("write_file", {"path": "nota.txt", "content": "..."},
                              {"confirmed_actions": ["write_file"]})
```

### Modelos locais

O Córtex espera `deepseek-r1:7b` para raciocínio e `qwen2.5-coder:7b` para tarefas de código. Ele detecta ambos em `/api/models/status` ou pela ação `model_status`, mas nunca os baixa automaticamente. Após instalar o Ollama, baixe apenas os que desejar:

```bash
ollama pull deepseek-r1:7b
ollama pull qwen2.5-coder:7b
```

## 🧱 Roadmap Futuro

| Prioridade | Funcionalidade |
|------------|----------------|
| Alta | Interface PWA com visual "Neural Synapse" avançado |
| Alta | Ajuste fino do DeepSeek (quantização, timeout) |
| Média | Integração EEG real (hardware físico) |
| Média | Auto-correção de vulnerabilidades |
| Baixa | App mobile (PWA instalável) |

## 📝 Licença

Este projeto é mantido por Nana e segue princípios de software livre e privacidade digital.

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📞 Suporte

Para suporte, consulte a documentação em `PROJETO.md` ou abra uma issue no repositório.

---

**Voto de Minerva:** SEMPRE da criadora.
