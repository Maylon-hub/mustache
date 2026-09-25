# Guia de Documentação — MustaCHE v2

**Pacote**: `mustache-core` v0.2.0**Backend**: `core-sg-mustache` v0.3.0 (Cython nativo)**Estilo deste guia**: [Read the Docs](https://www.sphinx-doc.org/) / [MkDocs](https://www.mkdocs.org/)

> Este documento serve como referência para usuários finais, orientadores e colaboradores que desejam **instalar, usar a API, interpretar saídas e operar a Web UI** do MustaCHE.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Instalação](#2-instalação)
3. [API Reference — `run_clustering`](#3-api-reference--run_clustering)
4. [Interpretando os Resultados](#4-interpretando-os-resultados)
5. [Web UI — Interface Interativa](#5-web-ui--interface-interativa)
6. [CLI — Linha de Comando](#6-cli--linha-de-comando)
7. [Exemplos Completos](#7-exemplos-completos)
8. [Perguntas Frequentes](#8-perguntas-frequentes)

---

## 1. Visão Geral

O **MustaCHE** (*Multiple Cluster Hierarchies Explorer*) é uma ferramenta interativa, baseada na web, para explorar clustering hierárquico baseado em densidade. Ele permite analisar **múltiplas hierarquias de clustering** geradas sob uma ampla faixa de parâmetros de densidade (`mpts`) simultaneamente, oferecendo insights sobre:

- **Estabilidade de clusters** — quais clusters persistem em diferentes escalas;
- **Estrutura do dataset** — como os dados se organizam hierarquicamente;
- **Comparação entre métodos** — HDBSCAN, Core-SG, e variações.

### 1.1 Arquitetura

```text
┌─────────────────────────────────────────────────────────┐
│              Web UI (Flask + Plotly + D3.js)            │
├─────────────────────────────────────────────────────────┤
│            Motor Analítico (mustache.core)              │
│            - run_clustering()                           │
│            - stability_analysis()                       │
│            - hierarchy_extraction()                     │
├─────────────────────────────────────────────────────────┤
│               Backend Cython (core_sg)                  │
│            - _mst_kruskal.pyd (MST em C otimizado)      │
│            - _reweight.pyd (reponderação de arestas)    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Instalação

### 2.1 Pré-requisitos

- Python 3.11.0 (64-bit)
- Windows 10/11 (para as wheels pré-compiladas atuais)
- Conexão com Internet

### 2.2 Instalação via pip

```powershell
# Criar ambiente virtual
python -m venv venv_mustache
.\venv_mustache\Scripts\activate

# Atualizar pip
pip install --upgrade pip

# Instalar o MustaCHE (puxa core-sg-mustache automaticamente)
pip install --index-url https://test.pypi.org/simple \
            --extra-index-url https://pypi.org/simple \
            mustache-core==0.2.0
```

### 2.3 Verificação

```python
import mustache
print(mustache.__version__)  # Esperado: 0.2.0

from mustache.core import run_clustering
print("Backend Cython ativo")  # Sem erros = sucesso
```

---

## 3. API Reference — `run_clustering`

### 3.1 Assinatura

```python
from mustache.core import run_clustering

result = run_clustering(
    X,
    method='hdbscan',
    min_cluster_size=5,
    min_samples=None,
    match_reference_implementation=True,
    core_dist_n_jobs=1,
    random_state=None
)
```

### 3.2 Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
| :--------------------------------- | :------------------ | :----------------- | :------------------------------------------------------------------------------------------------------------- |
| `X` | `np.ndarray` | *(obrigatório)* | Matriz de dados de forma`(n_samples, n_features)` |
| `method` | `str` | `'hdbscan'` | Método de clustering:`'hdbscan'` ou `'core_sg'` |
| `min_cluster_size` | `int` | `5` | Tamanho mínimo de um cluster |
| `min_samples` | `int` ou `None` | `None` | Número mínimo de amostras em uma vizinhança (se`None`, usa `min_cluster_size`) |
| `match_reference_implementation` | `bool` | `True` | Se`True`, usa o algoritmo de referência do HDBSCAN para reprodutibilidade |
| `core_dist_n_jobs` | `int` | `1` | Número de jobs para computação de distância.`1` = single-thread (reprodutível); `-1` = todos os cores |
| `random_state` | `int` ou `None` | `None` | Seed para reprodutibilidade |

### 3.3 Retorno

A função retorna um dicionário com as seguintes chaves:

| Chave | Tipo | Descrição |
| :---------------------- | :--------------------- | :----------------------------------------------------------- |
| `labels` | `np.ndarray` (int) | Rótulos de cluster para cada amostra (`-1` indica ruído) |
| `probabilities` | `np.ndarray` (float) | Probabilidade de cada amostra pertencer ao seu cluster |
| `cluster_persistence` | `np.ndarray` (float) | Estabilidade/persistência de cada cluster encontrado |
| `cluster_sizes` | `dict` | Mapeamento`label` $\rightarrow$ tamanho |
| `n_clusters` | `int` | Número de clusters encontrados (excluindo ruído) |
| `hierarchy` | `list` (dict) | Estrutura hierárquica completa (dendrograma) |
| `mst_edges` | `np.ndarray` | Arestas da Minimum Spanning Tree (se disponível) |

### 3.4 Exemplo mínimo

```python
import numpy as np
from mustache.core import run_clustering

# Gerar dados sintéticos (3 blobs)
rng = np.random.RandomState(42)
X = np.vstack([
    rng.randn(100, 2) + [2, 2],
    rng.randn(100, 2) + [-2, -2],
    rng.randn(100, 2) + [2, -2]
])

# Executar clustering
result = run_clustering(X, method='hdbscan', min_cluster_size=10)

print(f"Clusters encontrados: {result['n_clusters']}")
print(f"Amostras rotuladas: {len(result['labels'])}")
print(f"Rótulos únicos: {np.unique(result['labels'])}")
```

---

## 4. Interpretando os Resultados

### 4.1 Rótulos (`labels`)

- Cada valor inteiro $\ge 0$ representa um cluster;
- `-1` indica que a amostra foi classificada como ruído (não pertence a nenhum cluster denso);
- A quantidade de rótulos únicos (excluindo `-1`) é o número de clusters.

### 4.2 Probabilidades (`probabilities`)

- Valores entre $0$ e $1$;
- Quanto mais próximo de 1, mais fortemente a amostra pertence ao seu cluster;
- Útil para identificar amostras ambíguas (fronteira entre clusters).

### 4.3 Persistência (`cluster_persistence`)

- Mede quanto um cluster persiste ao longo de diferentes escalas de densidade;
- Valores altos indicam clusters robustos e bem separados;
- Valores baixos indicam clusters instáveis ou transitórios.

$$
\text{persistência}(C) = \int_{\lambda_{\min}}^{\lambda_{\max}} \frac{|C \cap \text{cluster}_{\lambda}|}{|C|} \, d\lambda
$$

### 4.4 Hierarquia (`hierarchy`)

- Lista de dicionários representando cada nível de corte da árvore hierárquica;
- Cada nível contém: `lambda_value`, `clusters`, `parent`, `stability`;
- Permite visualizar o dendrograma completo na Web UI.

### 4.5 Exportando para CSV

```python
import pandas as pd

df = pd.DataFrame({
    'label': result['labels'],
    'probability': result['probabilities']
})
df.to_csv('output/cluster_labels.csv', index=False)
```

---

## 5. Web UI — Interface Interativa

### 5.1 Iniciando o servidor

```powershell
mustache
# ou, alternativamente:
python -m mustache.cli
```

O servidor será iniciado em: `http://localhost:5000`

### 5.2 Funcionalidades da Web UI

| Aba | Funcionalidade |
| :--------------------- | :--------------------------------------------------- |
| **Upload** | Carregar CSV com dados tabulares |
| **Parâmetros** | Configurar`mpts`, `min_cluster_size`, método |
| **Hierarquias** | Visualizar dendrogramas interativos (Plotly + D3.js) |
| **Estabilidade** | Heatmap de estabilidade de clusters vs.`mpts` |
| **Comparação** | Comparar múltiplas hierarquias lado a lado |
| **Exportar** | Baixar CSVs, JSONs e PNGs dos gráficos |

### 5.3 Fluxo de uso típico

1. Upload do CSV (ex: `dataset_iris.csv`)
2. Selecionar faixa de `mpts`: `[5, 50]`, passo `5`
3. Executar clustering
4. Explorar hierarquias na aba "Hierarquias"
5. Analisar estabilidade na aba "Estabilidade"
6. Exportar resultados

---

## 6. CLI — Linha de Comando

### 6.1 Comando principal

```powershell
mustache --help
```

### 6.2 Subcomandos

```powershell
# Executar clustering em um CSV
mustache cluster dados.csv --method hdbscan --min-cluster-size 10

# Gerar relatório de estabilidade
mustache stability dados.csv --mpts-range 5 50 5

# Iniciar a Web UI
mustache serve --port 5000
```

---

## 7. Exemplos Completos

### 7.1 Clustering em dataset real (Iris)

```python
import numpy as np
import pandas as pd
from mustache.core import run_clustering
from sklearn.datasets import load_iris

# Carregar dataset
iris = load_iris()
X = iris.data

# Executar clustering
result = run_clustering(X, method='hdbscan', min_cluster_size=5)

# Exibir resultados
print(f"Clusters: {result['n_clusters']}")
print(f"Silhouette score: {result.get('silhouette_score', 'N/A')}")

# Exportar
df = pd.DataFrame(X, columns=iris.feature_names)
df['cluster'] = result['labels']
df['probability'] = result['probabilities']
df.to_csv('iris_clusters.csv', index=False)
```

### 7.2 Análise de estabilidade em múltiplos `mpts`

```python
import numpy as np
from mustache.core import run_clustering

# Dados sintéticos com estrutura multi-escala
rng = np.random.RandomState(42)
X = np.vstack([
    rng.randn(150, 2) * 0.5 + [0, 0],
    rng.randn(150, 2) * 0.5 + [5, 5],
    rng.randn(150, 2) * 2.0 + [2.5, 0]
])

# Executar para diferentes valores de mpts
mpts_values = [5, 10, 15, 20, 30, 50]
stability_results = []

for mpts in mpts_values:
    result = run_clustering(X, method='hdbscan',
                            min_cluster_size=mpts,
                            core_dist_n_jobs=1)
    stability_results.append({
        'mpts': mpts,
        'n_clusters': result['n_clusters'],
        'mean_persistence': np.mean(result['cluster_persistence'])
            if len(result['cluster_persistence']) > 0 else 0.0
    })

# Exibir tabela
for r in stability_results:
    print(f"mpts={r['mpts']:>3} | clusters={r['n_clusters']} | "
          f"persistência média={r['mean_persistence']:.3f}")
```

### 7.3 Visualização da hierarquia

```python
import plotly.graph_objects as go
from mustache.core import run_clustering
import numpy as np

# Gerar dados e executar clustering
X = np.random.RandomState(42).randn(300, 2)
result = run_clustering(X, method='hdbscan', min_cluster_size=10)

# Extrair hierarquia
hierarchy = result['hierarchy']

# Plotar dendrograma simplificado
lambdas = [h['lambda_value'] for h in hierarchy]
n_clusters = [len(h['clusters']) for h in hierarchy]

fig = go.Figure(data=go.Scatter(x=lambdas, y=n_clusters, mode='lines+markers'))
fig.update_layout(
    title='Dendrograma: Clusters vs. Lambda',
    xaxis_title='Lambda (1/distância)',
    yaxis_title='Número de clusters'
)
fig.write_html('dendrograma.html')
fig.show()
```

---

## 8. Perguntas Frequentes

- **Por que preciso do Python 3.11 especificamente?**As wheels pré-compiladas publicadas no TestPyPI foram geradas para `cp311-win_amd64`. Outras versões do Python exigiriam recompilação (trabalho futuro via `cibuildwheel`).
- **O que significa `match_reference_implementation=True`?**Garante que o algoritmo siga a implementação de referência do HDBSCAN original (Campello et al., 2013), assegurando reprodutibilidade entre diferentes máquinas e versões.
- **Por que `core_dist_n_jobs=1` é recomendado?**Execuções paralelas podem introduzir não-determinismo na ordem de processamento de pontos equidistantes. Para reprodutibilidade científica, use 1.
- **Como exportar a hierarquia para outro formato?**
  A chave `hierarchy` do resultado é uma lista de dicionários Python, facilmente serializável em JSON:

```python
import json
with open('hierarquia.json', 'w') as f:
    json.dump(result['hierarchy'], f, indent=2)
```

- **Posso usar GPU para acelerar?**Atualmente, o backend Cython é CPU-only. Suporte a GPU está no roadmap futuro.
- **Como citar o MustaCHE?**

```bibtex
@software{mustache2026,
  title   = {MustaCHE: Multiple Cluster Hierarchies Explorer},
  author  = {[autores]},
  year    = {2026},
  url     = {https://test.pypi.org/project/mustache-core/},
  version = {0.2.0}
}
```

---

## Referências

- Campello, R. J. G. B., et al. "Density-Based Clustering Based on Hierarchical Density Estimates." PAKDD 2013.
- Documentação oficial do HDBSCAN: [https://hdbscan.readthedocs.io/](https://hdbscan.readthedocs.io/)
- Core-SG (base do backend): [https://github.com/gabrieljorliano/core-sg](https://github.com/gabrieljorliano/core-sg)
- MustaCHE no TestPyPI: [https://test.pypi.org/project/mustache-core/0.2.0/](https://test.pypi.org/project/mustache-core/0.2.0/)
