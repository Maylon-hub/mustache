import os

report_path = r"C:\Users\guest\Documents\IC mustache\Documentação Mustache\Relatórios IDE\relatorio_cicd_cibuildwheel_multiplatforma_e_refatoracao_v0.3.0.md"

content = """# Relatório Técnico — Pipeline CI/CD Multi-plataforma (Cibuildwheel), Resolução de Impasses de Empacotamento e Refatoração do MustaCHE v0.3.0

**Projeto**: MustaCHE v2 / Core-SG (IC PIBIC-Af UFSCar)  
**Data**: 24/09/2026  
**Autor**: Maylon Martins de Melo  
**Versões Documentadas**: `mustache-core` v0.3.0 | `core-sg-mustache` v0.4.2  
**Repositórios**:
- MustaCHE: [Maylon-hub/mustache](https://github.com/Maylon-hub/mustache) (Branch: `mustache-core-sg`)
- Core-SG: [Maylon-hub/core-sg](https://github.com/Maylon-hub/core-sg) (Branch: `develop` / Tag: `v0.4.2`)

---

## 1. Contexto e Motivação

Nas etapas anteriores do projeto MustaCHE, publicamos com sucesso a extensão Cython do `core-sg-mustache` no TestPyPI. No entanto, o binário compilado (`.whl`) estava restrito ao **Python 3.11 no Windows 64-bit** (`cp311-win_amd64`).

### O Problema Encontrado
Ao tentar instalar o pacote em máquinas com **Python 3.12** (como notebooks Windows 11 com processadores modernos ou servidores Linux/macOS), o `pip` realizava *backtracking* por não encontrar uma wheel compatível e instalava uma versão em Python puro ou tentava compilar o sdist sem compilador C++, emitindo o aviso:
```text
RuntimeWarning: Cython backend for kruskal_mst is not available; using the Python fallback implementation.
```

### O Objetivo
Automação completa do processo de compilação via **GitHub Actions + `cibuildwheel`**, gerando e publicando wheels binárias nativas para **Windows, Linux e macOS** em múltiplos Python (`3.10`, `3.11`, `3.12` e `3.13`), eliminando a necessidade de ferramentas de compilação C++ na máquina do usuário final.

---

## 2. Configuração do Pipeline CI/CD (`cibuildwheel`)

Criamos a especificação de empacotamento multi-plataforma no repositório `core-sg`:

### 2.1 `pyproject.toml` (`core-sg-mustache` v0.4.2)
```toml
[build-system]
requires = ["cython>=3.0", "numpy>=1.24,<3", "setuptools>=77", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "core-sg-mustache"
version = "0.4.2"
description = "Core-SG graph construction and MST extraction utilities for HDBSCAN-style clustering."
requires-python = ">=3.10"

[tool.cibuildwheel]
build = "cp310-* cp311-* cp312-* cp313-*"
skip = ["*-musllinux_*", "*-manylinux_i686", "pp*"]
test-command = "python -c \"from sklearn.datasets import make_blobs; from core_sg import CoreSG; X, _ = make_blobs(n_samples=120, n_features=3, centers=3, random_state=42); core = CoreSG(metric='euclidean', p=2); core.fit(X, k_max=5); mst = core.extract_mst_from_core_sg(k=3); assert mst is not None\""

[tool.cibuildwheel.macos]
archs = ["x86_64", "arm64"]
test-skip = "*_x86_64"

[tool.cibuildwheel.windows]
archs = ["AMD64"]

[tool.cibuildwheel.linux]
manylinux-x86_64-image = "manylinux_2_28"
```

### 2.2 GitHub Actions (`.github/workflows/wheels.yml`)
Criado o workflow automatizado disparado em tags de release (`v*`) e execução manual (`workflow_dispatch`), compondo 3 jobs paralelos de compilação em runners nativos (`windows-latest`, `ubuntu-latest`, `macos-latest`) e um job final de publicação no TestPyPI via token de API.

---

## 3. Diagnóstico e Resolução de Problemas Encontrados nos Runs do CI/CD

Durante os testes de execução no GitHub Actions (`v0.4.0` e `v0.4.1`), identificamos e corrigimos 3 gargalos de empacotamento:

### 3.1 Divergência de Versão no Job `Release`
- **Sintoma**: O job `Release` falhava com o log: `pyproject.toml version mismatch: expected 0.4.1, found 0.4.0`.
- **Causa**: A tag git `v0.4.1` foi disparada antes de atualizar a string de versão no `pyproject.toml`.
- **Solução**: Atualização síncrona da versão para `0.4.2` no `pyproject.toml` e publicação da tag `v0.4.2`.

### 3.2 Erro de Redirecionamento no Windows (`test-requires`)
- **Sintoma**: O runner do Windows falhava na instalação dos requisitos de teste.
- **Causa**: A string `numpy>=1.24,<3` passada no `test-requires` era repassada diretamente ao `cmd.exe` do Windows, que interpretava `<3` como um comando de redirecionamento de entrada.
- **Solução**: Remoção do `test-requires` redundante. Como o arquivo `.whl` já declara suas dependências de runtime (`dependencies`), o `pip` instala tudo automaticamente ao testar a wheel.

### 3.3 Falha de Compilação do SciPy no Linux (`manylinux2014`)
- **Sintoma**: O runner Linux falhava com `ERROR: Dependency "OpenBLAS" not found` ao tentar compilar o SciPy a partir do código-fonte.
- **Causa**: O resolvedor do `pip` selecionava versões recentes de dependências (pandas 3.0 / scikit-learn 1.9) que não possuem wheels pré-compiladas para a `glibc` antiga da imagem `manylinux2014`.
- **Solução**: Atualização da imagem Linux no cibuildwheel para `manylinux_2_28`, garantindo compatibilidade nativa com as wheels modernas do ecossistema SciPy/PyPI.

### 3.4 Isolação de Arquitetura no macOS ARM
- **Sintoma**: Erro na execução do `test-command` para a wheel `x86_64` em runners Apple Silicon (ARM arm64).
- **Solução**: Inclusão de `test-skip = "*_x86_64"` na seção macOS, garantindo que ambas as wheels (`x86_64` e `arm64`) sejam compiladas, testando a arquitetura nativa.

---

## 4. Refatorações de Qualidade e Limpeza no Repositório MustaCHE

Além do pipeline de CI/CD, realizamos uma revisão no repositório `mustache` para garantir reprodutibilidade, segurança e tamanho otimizado:

### 4.1 Desversionamento de Ambientes Virtuais (`.venv` e `.venv_test_mustache`)
- **Problema**: O diretório `.venv` e `.venv_test_mustache` estavam sendo rastreados pelo Git, inflando o repositório em mais de **132 MB** com executáveis específicos do Windows.
- **Ação**: Executado `git rm -r --cached .venv .venv_test_mustache` e atualizado o `.gitignore` para bloquear `.venv/`, `.venv*/`, `venv/` e `*.venv`.

### 4.2 Alinhamento de Dependências (`pyproject.toml` e `requirements.txt`)
- **Ação**: Adicionadas versões mínimas no `pyproject.toml` (`Flask>=3.0.0`, `core-sg-mustache>=0.4.2`, `numpy>=1.24,<3`, `pandas>=2.0`, `scikit-learn>=1.3`, `scipy>=1.10`, `plotly>=5.0`).
- **`requirements.txt`**: Atualizado para apontar para `-e .` (instalação editável) e pacotes dev (`pytest>=8.0`, `pytest-flask>=1.3`).

### 4.3 Configuração Segura de `SECRET_KEY`
- **Arquivo**: `mustache/__init__.py`
- **Ação**: Alterado de `app.config['SECRET_KEY'] = 'dev'` para `os.environ.get('SECRET_KEY', 'dev-secret-key-mustache-change-in-prod')`.

### 4.4 Documentação da Sessão em Memória (`SESSION_DATA`)
- **Arquivo**: `mustache/routes.py`
- **Ação**: Adicionado comentário explicativo esclarecendo que a estrutura `SESSION_DATA` em memória foi desenhada para a interface gráfica interativa local (servidor *single-worker*) e que produções *multi-worker* (ex: Gunicorn) devem utilizar um cache persistente (Redis / disco).

### 4.5 Alinhamento da Documentação no `README.md`
- **Ação**: Atualizada a seção de pré-requisitos para declarar suporte a **Python >= 3.10** com wheels pré-compiladas multi-plataforma ativas.

---

## 5. Resultados da Suíte de Testes Automatizada

Executamos a suíte completa de testes unitários e de integração no ambiente virtual `venv`:

```powershell
python -m pytest --tb=short
```

### Resultado:
```text
============================= 55 passed in 50.03s =============================
```

- **55 de 55 testes aprovados** (rotas da API Flask, agrupamentos HDBSCAN, algoritmo Core-SG, cortes dinâmicos de dendrograma, matriz de similaridade HAI e medóides).

---

## 6. Resumo das Atualizações no Git

### Commits Realizados:

1. **Repositório `core-sg`** (Branch `develop`, Tag `v0.4.2`):
   - `feat: configure cibuildwheel multi-platform CI/CD v0.4.0`
   - `fix(ci): fix cibuildwheel test-requires, remove cp314 and skip x86_64 test on macos`
   - `fix(ci): bump version to 0.4.2, use manylinux_2_28, and remove test-requires`

2. **Repositório `mustache`** (Branch `mustache-core-sg`):
   - `chore: update mustache-core to v0.3.0 and core-sg-mustache dependency to >=0.4.0`
   - `chore: update core-sg-mustache dependency to >=0.4.2`
   - `fix(repo): remove tracked venvs, align dependencies, secure SECRET_KEY, and update docs`

---

## 7. Conclusão

Com a conclusão destas etapas, o MustaCHE v2 e o seu backend `core-sg-mustache` alcançaram maturidade de nível de produção:
1. Qualquer usuário em **Windows (64-bit), Linux ou macOS** rodando **Python 3.10 a 3.13** pode instalar o pacote via `pip install mustache-core` com o backend Cython compilado ativo nativamente.
2. O repositório local do MustaCHE está limpo, sem artefatos binários rastreados, com dependências reprodutíveis e 100% de aprovação nos testes.
"""

with open(report_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Report successfully saved to {report_path}")
