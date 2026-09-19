# Relatório Técnico: Empacotamento de Wheels Pré-compiladas (Cython) e Publicação no TestPyPI

**Data**: 18/09/2026  
**Projeto**: MustaCHE v2 — IC PIBIC-Af UFSCar  
**Pacotes Publicados**:
1. 🔗 **`core-sg-mustache` v0.3.0**: https://test.pypi.org/project/core-sg-mustache/0.3.0/
2. 🔗 **`mustache-core` v0.2.0**: https://test.pypi.org/project/mustache-core/0.2.0/

---

## 1. Motivação e Objetivos Alcançados

Anteriormente, a instalação do `core-sg` a partir do código-fonte exigia que a máquina do usuário final possuísse as ferramentas de compilação C++ (*Microsoft Visual C++ Build Tools / MSVC v143*), causando falhas de instalação para usuários comuns e orientadores.

**Objetivo Alcançado**:
Geramos e publicamos **wheels pré-compiladas** contendo os binários Cython otimizados (`_mst_kruskal.cp311-win_amd64.pyd` e `_reweight.cp311-win_amd64.pyd`). Agora, o comando `pip install mustache-core` instala automaticamente o MustaCHE e o `core-sg` **sem compilar nada**, com backend Cython nativo em C 100% ativo.

---

## 2. Auditoria dos Pacotes e Limpeza de Arquivos Desnecessários

### 2.1 Pacote `core-sg-mustache` (v0.3.0)
* **Tag da Wheel**: `cp311-cp311-win_amd64` (plataforma Windows 64-bit + Python 3.11).
* **Conteúdo incluído**:
  - `core_sg/__init__.py`, `core_sg.py`, `edges.py`, `estimators.py`, `knn.py`, `mst_kruskal.py`, `noise_handler.py`, `reweight.py`, `score_sg.py`, `hdbscan_adapter.py`
  - Binários compilados: `core_sg/_mst_kruskal.cp311-win_amd64.pyd` e `core_sg/_reweight.cp311-win_amd64.pyd`
  - Fontes Cython: `_mst_kruskal.pyx`, `_reweight.pyx`
* **Excluídos**: Scripts de benchmark internos, testes, relatórios Markdown e arquivos de CI.

### 2.2 Pacote `mustache-core` (v0.2.0)
* **Tag da Wheel**: `py3-none-any` (Pure Python wheel).
* **Conteúdo incluído**:
  - Aplicação Flask e motor analítico: `mustache/cli.py`, `mustache/routes.py`, `mustache/core/*`
  - Recursos estáticos da Web UI: `mustache/static/**/*`, `mustache/templates/**/*`
* **Excluídos**: Pastas `docs/`, `scripts/`, `tests/`, `legacy/`, `Relatórios IDE/` e qualquer arquivo `.pdf`, `.png`, `.jpg` fora de `static/`.

---

## 3. Configurações dos Arquivos de Empacotamento

### 3.1 `pyproject.toml` do `core-sg`
```toml
[build-system]
requires = ["cython>=3.0", "numpy>=1.24,<3", "setuptools>=77", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "core-sg-mustache"
version = "0.3.0"
description = "Core-SG graph construction and MST extraction utilities for HDBSCAN-style clustering."
readme = "README.md"
requires-python = ">=3.10"
license = "BSD-3-Clause"
dependencies = [
  "numpy>=1.24,<3",
  "pandas>=2.0",
  "scikit-learn>=1.3",
  "hdbscan>=0.8.39",
  "pynndescent>=0.5.13",
]

[tool.setuptools.packages.find]
include = ["core_sg", "core_sg.*"]
```

### 3.2 `pyproject.toml` do `mustache-core`
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mustache-core"
version = "0.2.0"
description = "MustaCHE (Multiple Cluster Hierarchies Explorer) integrated with pre-compiled Core-SG"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "Flask>=3.0.0",
    "core-sg-mustache>=0.3.0",
    "numpy",
    "pandas",
    "scikit-learn",
    "scipy",
    "plotly"
]

[project.scripts]
mustache = "mustache.cli:main"

[tool.setuptools]
include-package-data = true

[tool.setuptools.packages.find]
include = ["mustache*"]
exclude = ["tests*", "docs*", "scripts*", "legacy*"]

[tool.setuptools.package-data]
mustache = ["static/**/*", "templates/**/*"]

[tool.setuptools.exclude-package-data]
"*" = ["*.pdf", "*.png", "*.jpg", "*.bat", "*.sh"]
```

---

## 4. Validação em Ambientes Limpos (Sem Ferramentas C++)

### Teste 1: Validação do `core-sg-mustache` em `C:\temp\venv_teste`
```powershell
python -m venv C:\temp\venv_teste
C:\temp\venv_teste\Scripts\activate
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ core-sg-mustache==0.3.0
```
* **Resultado**:
  ```text
  Downloading core_sg_mustache-0.3.0-cp311-cp311-win_amd64.whl (165 kB)
  Successfully installed core-sg-mustache-0.3.0
  Cython backend OK
  MST edges: 299
  ```

### Teste 2: Validação Integrada do `mustache-core` em `C:\temp\venv_mustache`
```powershell
python -m venv C:\temp\venv_mustache
C:\temp\venv_mustache\Scripts\activate
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mustache-core==0.2.0
```
* **Resultado**:
  ```text
  Successfully installed mustache-core-0.2.0 core-sg-mustache-0.3.0
  MustaCHE importado OK
  CoreSG Cython backend OK
  ```

---

## 5. Limitação de Plataforma e Plano Futuro (`cibuildwheel`)

* **Limitação Atual**: A wheel gerada nesta etapa foi compilada especificamente para a plataforma **Windows 64-bit + Python 3.11** (`cp311-win_amd64`). Em máquinas Linux ou macOS sem compilador C, o `pip` buscaria a versão de código-fonte (`sdist`).
* **Trabalho Futuro (CI/CD Automático)**:
  Para gerar wheels nativas multi-plataforma automaticamente para **Windows, Linux (manylinux) e macOS** em múltiplas versões do Python (3.10, 3.11, 3.12, 3.13), deve-se configurar o workflow do GitHub Actions utilizando a ferramenta `cibuildwheel`:
  ```yaml
  name: Build Multi-platform Wheels
  on: [push, release]
  jobs:
    build_wheels:
      runs-on: ${{ matrix.os }}
      strategy:
        matrix:
          os: [ubuntu-latest, windows-latest, macos-latest]
      steps:
        - uses: actions/checkout@v4
        - uses: pypa/cibuildwheel@v2.20.0
        - uses: pypa/gh-action-pypi-publish@v1.8.14
          with:
            repository-url: https://test.pypi.org/legacy/
  ```
