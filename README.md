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
| **Armazenamento relacional local** | SQLite | Usuários, sessões, conversas, tarefas, execuções, scans e auditoria |
| **Memória semântica** | LanceDB (vetorial) | Embeddings, busca semântica e conhecimento |
| **Estado temporário** | Redis (localhost) | Cache, filas, pub/sub e estado efêmero |
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
├── database/                      # Persistência relacional local
│   ├── connection.py               # Conexão SQLite e aplicação de migrações
│   ├── migrations/                 # Schema versionado
│   └── repositories/               # Acesso a dados sem SQL nas rotas
├── api/                            # API HTTP organizada
│   ├── routes/                     # Chat, tarefas, segurança e sistema
│   ├── schemas/                    # Contratos Pydantic
│   └── services/                   # Política entre intenção e execução
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

### Dados, governança e execução

SQLite é armazenamento relacional persistente local; o prazo de retenção é uma regra da aplicação. LanceDB permanece reservado à memória vetorial e Redis a cache, filas e estado temporário.

Toda ação deve seguir a cadeia abaixo. O LLM interpreta intenção e plano, mas não executa ferramentas diretamente:

```
Request → LLM/plano → Policy Engine → confirmação humana (se necessária)
        → executor/ferramenta → audit_events + logs/audit.jsonl
```

O schema inicial inclui `users`, `sessions`, `conversations`, `messages`, `projects`, `tasks`, `confirmations`, `executions`, `security_scans`, `findings`, `permissions`, `audit_events` e `system_settings`. A primeira inicialização cria `data/cortex.db`, que pode ser aberto no DBeaver com o driver SQLite.

Endpoints operacionais: `GET /api/health`, `GET /api/status`, `GET /api/metrics`, `GET /api/models/status`, `GET /api/governance/status`, `GET /api/audit-events`, `POST /api/chat` e `POST /api/tasks`.

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

- **Analisador estático de segurança com regras heurísticas específicas por linguagem:** Python, Java, JavaScript, C/C++, Go, Rust, Assembly
- **Análise de binários:** ELF, PE, Mach-O
- **Verificação de dependências:** OSV local para CVEs conhecidas
- **Relatórios:** Markdown com SHA-256
- **Nota:** O scanner usa regras heurísticas baseadas em padrões estáticos e não confirma necessariamente vulnerabilidades exploráveis. Requer análise humana para confirmação.

### Sistema de Voz

- **STT:** Vosk (modelo pt-BR)
- **TTS:** Piper TTS (Luciana/Faber)
- **Wake Word:** Detecção "Ei Córtex"
- **Background:** Serviço 24/7

### Self-Modification / Autonomous System Maintenance

- **Capacidade iterativa (desabilitada por padrão):** análise e proposta de melhorias; não é treinamento nem fine-tuning de LLM.
- **Descoberta de lacunas:** Análise de PROJETO.md vs implementação
- **Editor seguro:** Backup automático + rollback
- **Sandbox:** Testes em Docker antes de aplicar
- **Evolução contínua:** Ciclo automático de melhorias

### Roteamento de modelos

Antes da geração, o `ModelRouter` seleciona o perfil: `fast` e `coding` usam Qwen Coder; solicitações explicitamente complexas usam DeepSeek R1. O roteador não chama ferramentas: qualquer ação continua passando por análise de intenção, governança, confirmação humana e executor.

### Dashboard PWA

- **Tema:** Neural Synapse (dark mode)
- **WebSocket:** Comunicação em tempo real
- **Offline-first:** Service Worker + manifest
- **Responsivo:** Mobile-friendly

## 📊 Estatísticas do Projeto

- **Arquivos Python:** 20+ módulos
- **Regras de segurança:** 7 linguagens, 300+ regras heurísticas
- **Intenções:** 102+ intents treinadas
- **Linhas de código:** ~15,000
- **Status de funcionalidades:** Ver IMPLEMENTATION_STATUS.md para detalhes
  - **IMPLEMENTED:** Ações críticas de sistema, arquivos, segurança, rede e governança
  - **PARTIAL:** Funcionalidades de assistente pessoal, web, conhecimento e diagnóstico
  - **PLANNED:** Recursos avançados de backup, autenticação e interfaces completas

## 🔒 Segurança

- **Criptografia:** AES-256-GCM para dados sensíveis via secure_storage (não criptografa o arquivo SQLite inteiro)
- **Sandbox:** Docker para auto-evolução com propriedades de isolamento (sem rede, limites de CPU/memória, filesystem read-only, sem privilégios)
- **Offline-first:** Sem APIs externas
- **Privacidade:** Dados locais apenas
- **Nota:** Para criptografia completa do banco de dados, seria necessário usar SQLCipher ou solução similar

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
