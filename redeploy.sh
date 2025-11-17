#!/bin/bash
set -e

echo "🛡️ Forçando o AppArmor a descarregar todos os perfis do kernel..."
sudo service apparmor force-reload

echo "🚀 Parando e removendo quaisquer containers antigos restantes..."
docker compose down --remove-orphans

echo "🏗️ Reconstruindo imagens Docker (usando cache se possível)..."
docker compose build

echo "📦 Subindo novos containers..."
docker compose up -d --force-recreate

echo "🛡️ Recarregando o AppArmor para restaurar a segurança do sistema..."
sudo systemctl restart apparmor.service

echo "⏳ Aguardando os containers estabilizarem..."
sleep 5

echo "📜 Exibindo logs recentes do Flask e Celery..."
docker compose logs --tail=50 flask
docker compose logs --tail=50 celery

echo "✅ Redeploy concluído! A aplicação deve estar acessível em http://localhost:5001"
