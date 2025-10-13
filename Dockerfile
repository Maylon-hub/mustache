# -------------------------------------------------------
# 🐍 Base image
# -------------------------------------------------------
FROM python:3.9-slim AS base

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Instalar dependências do sistema (mantendo as suas originais)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gfortran \
        libopenblas-dev \
        liblapack-dev \
        default-jdk \
        python3-dev \
        pkg-config \
        git \
        curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Atualizar pip e ferramentas básicas
RUN pip install --upgrade "pip<24.1" setuptools wheel

# -------------------------------------------------------
# 🧱 Instalar dependências Python com cache
# -------------------------------------------------------
COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------
# 📦 Copiar aplicação
# -------------------------------------------------------
COPY . .

# Criar diretórios de log
RUN mkdir -p logs/flask logs/celery

# Expor porta Flask
EXPOSE 5000

# -------------------------------------------------------
# 🚀 Comando de inicialização
# -------------------------------------------------------
# Opção 1: modo desenvolvimento (igual ao seu atual)
# CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

# Opção 2: modo produção (recomendado)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "mustache:app"]
