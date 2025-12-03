$ErrorActionPreference = "Stop"

# Garantir que o workspace esteja definido corretamente também no redeploy
$env:MUSTACHE_WORKSPACE = "D:\mustache-workspace"

Write-Host "Parando e removendo containers antigos..."
docker compose down --remove-orphans

Write-Host "Reconstruindo imagens Docker..."
docker compose build

Write-Host "Subindo novos containers..."
docker compose up -d --force-recreate

Write-Host "Aguardando containers iniciarem..."
Start-Sleep -Seconds 5

Write-Host "Logs recentes (Flask e Celery):"
docker compose logs --tail=20 flask
docker compose logs --tail=20 celery

Write-Host "Redeploy concluido! Acesse em http://localhost:5001"
