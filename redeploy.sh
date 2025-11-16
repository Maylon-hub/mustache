#!/bin/bash
set -e

echo "🚀 Parando containers antigos..."
docker compose down

echo "🏗️ Rebuildando imagens Docker..."
docker compose build --no-cache

echo "📦 Subindo containers..."
docker compose up -d

echo "📜 Exibindo últimos logs do Flask e Celery..."
docker compose logs flask --tail=50
docker compose logs celery --tail=50

echo "✅ Redeploy concluído! Acesse: http://localhost:5001"
