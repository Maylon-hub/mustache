#!/bin/bash
set -e

echo "🚀 Parando containers antigos..."
sudo docker compose down

echo "🏗️ Rebuildando imagens Docker..."
sudo docker compose build --no-cache

echo "📦 Subindo containers..."
sudo docker compose up -d

echo "📜 Exibindo últimos logs do Flask e Celery..."
sudo docker compose logs flask --tail=50
sudo docker compose logs celery --tail=50

echo "✅ Redeploy concluído! Acesse: http://localhost:5000"
