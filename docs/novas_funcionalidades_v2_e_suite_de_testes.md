# Relatório de Implementação: Novas Funcionalidades v2, Histórico e Suíte de Testes (Pytest)

**Projeto**: MustaCHE (Multiple Cluster Hierarchies Explorer) v2  
**Data**: 17 de Setembro de 2026  
**Autores**: Maylon Martins de Melo  
**Referência Principal**: Neto et al. (2018) — *MustaCHE: A Multiple Cluster Hierarchies Explorer*

---

## 1. Visão Geral

Este documento registra as implementações e atualizações arquiteturais realizadas no MustaCHE v2, resgatando recursos de usabilidade e visualização da versão legacy de 2017 e introduzindo uma arquitetura robusta de persistência local, cache em memória e testes automatizados.

---

## 2. Detalhamento das Melhorias e Funcionalidades

### 2.1 Especificação de Algoritmo no Timing Profile Report
- **Descrição**: O relatório de tempo de execução exibido no terminal ao finalizar uma análise em lote agora identifica dinamicamente o algoritmo executado (`HDBSCAN` ou `Core-SG`), em vez do texto genérico `(HDBSCAN/Core-SG)`.
- **Arquivos**: `mustache/core/clustering.py` e `mustache/core/batch.py`.

---

### 2.2 Fase 1: Cache Inteligente de Limiares e Debounce
- **Discretização de Alturas no Backend**: Em `mustache/routes.py`, as alturas distintas da matriz de ligação $Z$ do meta-dendrograma são indexadas via `np.searchsorted`. Cortes que ocorrem no mesmo intervalo de fusão utilizam a partição guardada em `SESSION_DATA['cut_cache']`.
- **Cache Local no Cliente**: Em `mustache/static/js/main.js`, o mapa `clientCutCache` armazena respostas do frontend por limiar, retornando a visualização dos Reachability Plots em $0\text{ms}$ (Instant Cache).
- **Debounce de 120ms**: Adicionado ao evento `plotly_relayout` do meta-dendrograma, evitando disparos excessivos de requisições HTTP durante o arrasto contínuo da linha de corte.

---

### 2.3 Fase 2: Toolbar Interativa e Extração de Ramos em CSV
- **Barra de Ferramentas no Dendrograma**: Incorporada no cabeçalho do card em `mustache/templates/index.html`:
  - 🪄 **Magic Wand (`select`)**: Ativa a seleção/desseleção visual de ramos no Plotly.
  - ➗ **Cut Line (`cut`)**: Habilita o ajuste da linha de corte.
  - ✋ **Pan**: Ferramenta de navegação.
  - 🔍 **Zoom (+, -, 100%)**: Controles dedicados de zoom.
  - 🏷️ **Badge em Tempo Real**: Exibe a quantidade de ramos selecionados (`X branches selected`).
- **Endpoint `POST /export_branches_csv`**:
  - Gera para download direto um arquivo `.csv` unificado contendo o dataset original concatenado com os rótulos de cluster (`Cluster_mpts_X`) e probabilidades de pertinência (`Prob_mpts_X`) de cada ramo selecionado (ou dos medoides ativos se nenhum ramo for marcado).

---

### 2.4 Fase 3: Home Dashboard e Histórico de Análises Salvas
- **Módulo de Armazenamento Local (`mustache/core/storage.py`)**:
  - Salva e gerencia projetos na pasta do usuário em `~/.mustache/projects/<project_id>/`.
  - Estrutura gravada: `metadata.json` (parâmetros e resumo), `results.json` (figuras Plotly, matriz HAI, linkage e medoides) e `data.csv` (dados originais).
- **Rotas de API REST (`mustache/routes.py`)**:
  - `GET /api/projects`: Lista todos os projetos ordenados por data.
  - `POST /api/projects/save`: Salva o lote recém-calculado com o nome fornecido pelo usuário.
  - `GET /api/projects/<id>/data`: Carrega o experimento diretamente na sessão.
  - `DELETE /api/projects/<id>`: Remove o experimento do disco.
  - `GET /api/projects/<id>/export_zip`: Gera empacotamento ZIP de todos os artefatos do projeto.
- **Interface Home (`mustache/templates/home.html`)**:
  - Inspirada na interface legacy (`home.png` e `home2.png`).
  - Apresenta cards informativos com badges de status, busca em tempo real por nome/algoritmo/métrica, contagem de projetos e botão flutuante (+).
  - Botão **OPEN**: Carrega o projeto salvo no dashboard instantaneamente sem necessidade de recomputar o agrupamento.
- **Integrantes de UI**:
  - Botão **"Save Analysis"** visível na sidebar fixa e no topo do card do dendrograma após o término do lote.
  - Tratamento de parâmetros de URL: `?project_id=<id>` para carregar análises e `?new=1` para resetar a sessão.

---

### 2.5 Fase 4: Suíte de Testes Automatizados com Pytest
Estrutura completa desenvolvida na pasta `tests/`:

1. `conftest.py`: Fixtures compartilhadas para geração de datasets sintéticos (`make_blobs`, `make_moons`) e cliente de testes Flask (`flask_client`).
2. `test_clustering.py` (12 testes): Valida os motores de clustering (shapes de rótulos, monotonicidade da matriz $Z$, ARI/AMI, probabilidades e contagem de clusters).
3. `test_batch.py` (14 testes): Valida o pipeline de execução em lote, faixa de $m_{pts}$, estrutura dos dicionários de saída, simetria e propriedades da matriz HAI.
4. `test_hai.py` (14 testes): Valida as propriedades matemáticas do Hierarchy Agreement Index (simetria estrita $H_{ij} = H_{ji}$, diagonal unitária $H_{ii} = 1.0$, intervalo de similaridades em $[0, 1]$ e identificação correta de medoides excluindo ruído).
5. `test_api_routes.py` (15 testes): Valida a integração das rotas HTTP do Flask (`/`, `/api/projects`, `/batch`, `/cut_dendrogram`, `/export_branches_csv`).

- **Configuração no `pyproject.toml`**:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  python_files = ["test_clustering.py", "test_batch.py", "test_hai.py", "test_api_routes.py"]
  addopts = "-v --tb=short -p no:flask"
  ```
- **Resultado da Suíte Completa**:
  ```text
  ============================= 55 passed in 39.48s =============================
  ```

---

## 3. Ambiente de Execução e Desenvolvimento

Para garantir que o comando CLI `mustache` utilize o código-fonte atualizado da pasta do repositório em vez de uma cópia congelada no `site-packages`, o pacote deve ser instalado em **modo editável**:

```powershell
# Ativar o ambiente virtual venv
.\venv\Scripts\activate

# Instalar em modo editável sem reinstalar dependências
pip install -e . --no-deps

# Iniciar a aplicação
mustache
```

A aplicação será iniciada por padrão em **`http://127.0.0.1:5000`**:
- **Dashboard Principal**: `http://127.0.0.1:5000/`
- **Painel de Histórico (Saved Projects)**: `http://127.0.0.1:5000/projects`
