@echo off
REM build_coresg_cython.bat
REM Compila as extensoes Cython do core-sg usando MSVC.
REM Estrategia: copiar os .pyx para uma pasta temp fora do diretorio core-sg
REM para evitar que setuptools leia o pyproject.toml original (que tem license
REM em formato incompativel com setuptools >= 77).

SET CORE_SG_DIR=C:\Users\guest\Documents\GitHub\core-sg
SET PYTHON_EXE=C:\Users\guest\Documents\GitHub\mustache\venv\Scripts\python.exe
SET SCRIPTS_DIR=C:\Users\guest\Documents\GitHub\mustache\scripts
SET BUILD_TMP=%TEMP%\core_sg_build
SET VCVARS64=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat

echo === Core-SG Cython Build (Windows/MSVC) ===
echo.

REM Ativar ambiente MSVC
call "%VCVARS64%"
if %errorlevel% neq 0 (
    echo ERRO: Falha ao configurar ambiente MSVC
    exit /b 1
)
echo [1/5] Ambiente MSVC configurado.

REM Criar diretorio temporario de build isolado
if exist "%BUILD_TMP%" rmdir /s /q "%BUILD_TMP%"
mkdir "%BUILD_TMP%\core_sg"
echo [2/5] Diretorio temporario criado: %BUILD_TMP%

REM Copiar apenas os .pyx e o .c pre-gerado (se existir)
copy /Y "%CORE_SG_DIR%\core_sg\_mst_kruskal.pyx" "%BUILD_TMP%\core_sg\_mst_kruskal.pyx" > nul
copy /Y "%CORE_SG_DIR%\core_sg\_reweight.pyx"    "%BUILD_TMP%\core_sg\_reweight.pyx"    > nul

REM Copiar o setup script para o dir temporario
copy /Y "%SCRIPTS_DIR%\setup_cython_coresg.py" "%BUILD_TMP%\setup_cython.py" > nul
echo [3/5] Arquivos copiados para diretorio temporario.

REM Entrar no diretorio temporario (sem pyproject.toml do core-sg)
cd /d "%BUILD_TMP%"

REM Compilar
echo [4/5] Compilando extensoes Cython (isso pode levar alguns minutos)...
"%PYTHON_EXE%" setup_cython.py build_ext --inplace 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Build Cython falhou. Veja os erros acima.
    exit /b 1
)

echo [5/5] Build concluido. Copiando .pyd para core-sg...

REM Copiar os .pyd gerados de volta para o diretorio core_sg real
for %%f in ("%BUILD_TMP%\core_sg\*.pyd") do (
    copy /Y "%%f" "%CORE_SG_DIR%\core_sg\" > nul
    echo   Copiado: %%~nxf -> %CORE_SG_DIR%\core_sg\
)

echo.
echo === Modulos .pyd em %CORE_SG_DIR%\core_sg\ ===
dir /b "%CORE_SG_DIR%\core_sg\*.pyd" 2>nul
if %errorlevel% neq 0 echo Nenhum .pyd encontrado!

echo.
echo === Testando importacao do backend Cython ===
"%PYTHON_EXE%" "%SCRIPTS_DIR%\test_cython_backend.py"

echo.
echo === PROCESSO CONCLUIDO ===
