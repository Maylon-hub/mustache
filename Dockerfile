# -------------------------------------------------------
# 🧱 Etapa de Build: Instala dependências e compila pacotes
# -------------------------------------------------------
FROM python:3.9-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Instalar apenas as dependências de build necessárias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gfortran \
        libopenblas-dev \
        liblapack-dev \
        default-jdk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Atualizar pip e ferramentas básicas
RUN pip install --upgrade "pip<24.1" setuptools wheel

# Instalar dependências Python em um diretório separado
COPY requirements.txt ./requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# -------------------------------------------------------
# 🐍 Etapa Final: Imagem de produção leve
# -------------------------------------------------------
FROM python:3.9-slim AS final

WORKDIR /app

# Instalar apenas as dependências de sistema necessárias para rodar a aplicação
RUN apt-get update && apt-get install -y --no-install-recommends libopenblas-dev liblapack-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar as dependências pré-compiladas da etapa de build e instalá-las
COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Criar diretórios de log
RUN mkdir -p logs/flask logs/celery

# Expor porta Flask
EXPOSE 5000

# -------------------------------------------------------
# 🚀 Comando de inicialização para produção
# -------------------------------------------------------
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "mustache:app"]
