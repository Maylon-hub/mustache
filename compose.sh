#!/bin/bash

# --------------------------------------------------------
# 🚀 MustaCHE - Build Script (compose.sh)
# --------------------------------------------------------

# Parar imediatamente se houver erro
set -e

# Verificar argumento do workspace
if [ -z "$1" ]; then
  echo "❌ Erro: você deve informar o caminho do workspace."
  echo "👉 Exemplo: ./compose.sh /home/usuario/mustache-workspace"
  exit 1
fi

# --------------------------------------------------------
# 🌍 Variáveis de ambiente
# --------------------------------------------------------
export COMPOSE_PROJECT_NAME=mustache
export MUSTACHE_WORKSPACE=$1

echo "📦 Iniciando build do projeto MustaCHE..."
echo "🗂️  Workspace: $MUSTACHE_WORKSPACE"
echo "------------------------------------------------------"

# --------------------------------------------------------
# 🏗️ Preparar diretórios locais
# --------------------------------------------------------
mkdir -p "$MUSTACHE_WORKSPACE"
mkdir -p logs/flask logs/celery
chmod -R a+rwx "$MUSTACHE_WORKSPACE" logs

# --------------------------------------------------------
# ⚙️ Gerar o script run.sh atualizado
# --------------------------------------------------------
cat <<EOF > run.sh
#!/bin/bash
set -e
export COMPOSE_PROJECT_NAME=mustache
export MUSTACHE_WORKSPACE=$MUSTACHE_WORKSPACE
echo "🚀 Subindo containers do MustaCHE..."
docker compose up -d
echo "✅ Containers iniciados com sucesso!"
EOF

chmod +x run.sh

# --------------------------------------------------------
# 🧱 Construir a aplicação
# --------------------------------------------------------
echo "🔧 Construindo imagens Docker..."
docker compose build --no-cache --compress

echo "✅ Build concluído!"
echo "👉 Para iniciar o projeto, execute: ./run.sh"
