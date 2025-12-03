$ErrorActionPreference = "Stop"

# Configuração de variáveis de ambiente
$env:COMPOSE_PROJECT_NAME = "mustache"

# Definindo o workspace no drive D: como solicitado
$env:MUSTACHE_WORKSPACE = "D:\Documents\mustache-workspace"

# Cria o diretório de workspace se não existir
if (-not (Test-Path -Path $env:MUSTACHE_WORKSPACE)) {
    Write-Host "Criando diretorio de workspace em: $env:MUSTACHE_WORKSPACE"
    New-Item -ItemType Directory -Force -Path $env:MUSTACHE_WORKSPACE | Out-Null
}

Write-Host "Iniciando containers do MustaCHE..."
Write-Host "Workspace configurado em: $env:MUSTACHE_WORKSPACE"

docker compose up -d

Write-Host "Containers iniciados com sucesso!"
Write-Host "Acesse a aplicacao em: http://localhost:5001"
