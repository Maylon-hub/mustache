#!/bin/bash
set -e
export COMPOSE_PROJECT_NAME=mustache
export MUSTACHE_WORKSPACE=/home/Documents/workspace
echo "🚀 Subindo containers do MustaCHE..."
docker compose up -d
echo "✅ Containers iniciados com sucesso!"
