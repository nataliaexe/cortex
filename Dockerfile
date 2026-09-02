# Gênesis Córtex - Dockerfile
# Containerização do projeto

FROM python:3.12-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código do projeto
COPY . .

# Cria diretórios necessários
RUN mkdir -p data logs reports backups

# Expõe porta para web app
EXPOSE 8000

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV CORTEX_CONFIG=/app/config.yaml

# Comando de execução
CMD ["python", "core/engine.py"]