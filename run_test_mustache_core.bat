@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo Teste de Instalação do MustaCHE Explorer (mustache-core)
echo ======================================================================
echo.

set "VENV_DIR=%TEMP%\mustache_test_venv"

echo [+] Criando ambiente virtual temporario em: %VENV_DIR%
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
python -m venv "%VENV_DIR%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Falha ao criar o ambiente virtual. Verifique se o Python esta no PATH.
    pause
    exit /b %ERRORLEVEL%
)

echo [+] Atualizando pip no ambiente isolado...
"%VENV_DIR%\Scripts\python.exe" -m pip install --quiet --upgrade pip

echo [+] Tentando instalar mustache-core a partir do TestPyPI...
echo     (Aguarde, baixando e configurando dependencias do PyPI...)
echo.

"%VENV_DIR%\Scripts\python.exe" -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mustache-core==0.1.0

if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo [FALHA] A instalacao falhou! 
    echo ======================================================================
    echo Causa provavel:
    echo O pacote 'core-sg' exige compilacao de modulos Cython (C++). Como voce esta
    echo usando o Python 3.13 e nao possui rodas (wheels) pre-compiladas no PyPI
    echo para esta versao, o pip tentou compilar a partir do codigo fonte (.tar.gz),
    echo o que requer os compiladores C++ (Microsoft Visual C++ Build Tools) no Windows.
    echo.
    echo Como resolver este problema para novos usuarios:
    echo.
    echo 1. Adicionar suporte ao Python 3.13 no cibuildwheel do core-sg (Feito!):
    echo    Isso criara as rodas pre-compiladas (.whl) automaticamente na proxima
    echo    publicacao, eliminando a necessidade de compiladores na maquina do usuario.
    echo.
    echo 2. Instalar o Microsoft C++ Build Tools (Se desejar compilar localmente):
    echo    Baixe em: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo    E selecione "Desenvolvimento para desktop com C++".
    echo.
    echo 3. Executar o teste em um ambiente Python 3.10, 3.11 ou 3.12:
    echo    Estas versoes ja possuem wheels pre-compiladas no PyPI/TestPyPI e nao
    echo    exigirao nenhum compilador C++ local.
    echo ======================================================================
    echo.
) else (
    echo.
    echo ======================================================================
    echo [SUCESSO] Instalação concluída com sucesso!
    echo ======================================================================
    echo [+] Executando script de testes de agrupamento...
    echo.
    "%VENV_DIR%\Scripts\python.exe" test_mustache_core.py
)

pause
