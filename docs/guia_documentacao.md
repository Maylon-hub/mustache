# Guia de Documentação — MustaCHE v2

**Código-fonte atual**: `mustache-core` v0.3.0rc2<br>
**Backend mínimo**: `core-sg-mustache` v0.4.5rc2<br>
**Estilo deste guia**: [Read the Docs](https://www.sphinx-doc.org/) / [MkDocs](https://www.mkdocs.org/)

> Este documento serve como referência para usuários finais, orientadores e colaboradores que desejam **instalar, usar a API, interpretar saídas e operar a Web UI** do MustaCHE.

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
│            - run_batch_clustering()                     │
│            - analyze_batch_results()                    │
├─────────────────────────────────────────────────────────┤
│               Backend Cython (core_sg)                  │
│            - _mst_kruskal.pyd (MST em C otimizado)      │
│            - _reweight.pyd (reponderação de arestas)    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Instalação

### 2.1 Pré-requisitos

- Python >= 3.10
- Windows, Linux ou macOS com uma wheel compatível do backend
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
            --pre mustache-core==0.3.0rc2
```

### 2.3 Verificação

```python
import mustache
print(mustache.__version__)  # Esperado: 0.3.0rc2

from mustache.core import run_clustering
print("Backend Cython ativo")  # Sem erros = sucesso
```

Para validar o uso em Jupyter, abra e execute todas as células de
[`examples/mustache_quickstart.ipynb`](https://github.com/Maylon-hub/mustache/blob/mustache-core-sg/examples/mustache_quickstart.ipynb). O notebook cria
um conjunto sintético, executa uma varredura CORE-SG para `mpts = 4, 6, 8` e verifica a forma
dos resultados.

---

## 3. API Reference — `run_clustering`

### 3.1 Assinatura

```python
from mustache.core import run_clustering

result = run_clustering(
    dataframe,
    min_cluster_size=5,
    min_samples=None,
    metric='euclidean',
    algorithm='core-sg'
)
```

### 3.2 Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
| :--------------------------------- | :------------------ | :----------------- | :------------------------------------------------------------------------------------------------------------- |
| `dataframe` | `pandas.DataFrame` | *(obrigatório)* | Dados tabulares; apenas colunas numéricas são agrupadas |
| `algorithm` | `str` | `'core-sg'` | Método de clustering: `'core-sg'` ou `'hdbscan'` |
| `min_cluster_size` | `int` | `5` | Tamanho mínimo de um cluster |
| `min_samples` | `int` ou `None` | `None` | Número mínimo de amostras em uma vizinhança (se`None`, usa `min_cluster_size`) |
| `metric` | `str` | `'euclidean'` | Métrica aceita pelo backend selecionado |
| `true_labels` | array ou `None` | `None` | Rótulos de referência opcionais para ARI e AMI |

### 3.3 Retorno

A função retorna um dicionário com as seguintes chaves:

| Chave | Tipo | Descrição |
| :---------------------- | :--------------------- | :----------------------------------------------------------- |
| `labels` | `list[int]` | Rótulos de cluster para cada amostra (`-1` indica ruído) |
| `probabilities` | `list[float]` | Probabilidade de cada amostra pertencer ao seu cluster |
| `n_clusters` | `int` | Número de clusters encontrados (excluindo ruído) |
| `noise_points` | `int` | Quantidade de amostras classificadas como ruído |
| `linkage_z` | `list` | Matriz de linkage da hierarquia |
| `metrics` | `dict` | ARI e AMI quando `true_labels` é fornecido |
| `dendrogram_json`, `reachability_json`, `map_json` | `str` ou `None` | Figuras Plotly serializadas |
| `clustering_time`, `optics_time` | `float` | Tempos observados, em segundos |

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
result = run_clustering(pd.DataFrame(X), algorithm='hdbscan', min_cluster_size=10)

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

### 4.3 Hierarquia (`linkage_z`)

- Matriz SciPy de forma `(n_samples - 1, 4)` representando as fusões da árvore;
- Cada linha contém os dois filhos, a distância da fusão e o tamanho do novo cluster;
- É a representação usada pelo HAI e pelo dendrograma.

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
| **Selecionar ramos** | Clicar numa subárvore para selecionar todos os valores de `mpts` abaixo dela |
| **Exportar** | Baixar CSV com rótulos e probabilidades das hierarquias selecionadas |

### 5.3 Fluxo de uso típico

1. Upload do CSV (ex: `dataset_iris.csv`)
2. Selecionar faixa de `mpts`: `[5, 50]`, passo `5`
3. Executar clustering
4. Explorar hierarquias na aba "Hierarquias"
5. Analisar estabilidade na aba "Estabilidade"
6. Clicar em ramos do meta-dendrograma para selecionar as hierarquias relevantes
7. Salvar a análise ou exportar as partições selecionadas em CSV

---

## 6. CLI — Linha de Comando

### 6.1 Comando principal

```powershell
mustache --help
```

### 6.2 Opções disponíveis

O comando atual inicia a Web UI; ele não possui subcomandos de clustering.

```powershell
mustache --host 127.0.0.1 --port 5000
mustache --help
```

Para processamento sem servidor, importe `run_clustering` ou `run_batch_clustering` em um script ou notebook.

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
result = run_clustering(pd.DataFrame(X), algorithm='hdbscan', min_cluster_size=5)

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
    result = run_clustering(pd.DataFrame(X), algorithm='hdbscan',
                            min_cluster_size=mpts,
                            min_samples=mpts)
    stability_results.append({
        'mpts': mpts,
        'n_clusters': result['n_clusters'],
        'noise_points': result['noise_points']
    })

# Exibir tabela
for r in stability_results:
    print(f"mpts={r['mpts']:>3} | clusters={r['n_clusters']} | "
          f"ruído={r['noise_points']}")
```

### 7.3 Visualização da hierarquia

```python
import plotly.graph_objects as go
from mustache.core import run_clustering
import numpy as np

# Gerar dados e executar clustering
X = np.random.RandomState(42).randn(300, 2)
result = run_clustering(pd.DataFrame(X), algorithm='hdbscan', min_cluster_size=10)

# Extrair hierarquia
hierarchy = np.asarray(result['linkage_z'])

# Plotar dendrograma simplificado
from scipy.cluster.hierarchy import dendrogram
dendrogram(hierarchy)
```

---

## 8. Perguntas Frequentes

- **Qual versão do Python devo usar?** O projeto declara Python >= 3.10. Para a validação final, use uma versão que possua wheel publicada tanto para `mustache-core` quanto para `core-sg-mustache`.
- **O que significa `match_reference_implementation=True`?**Garante que o algoritmo siga a implementação de referência do HDBSCAN original (Campello et al., 2013), assegurando reprodutibilidade entre diferentes máquinas e versões.
- **Por que `core_dist_n_jobs=1` é recomendado?**Execuções paralelas podem introduzir não-determinismo na ordem de processamento de pontos equidistantes. Para reprodutibilidade científica, use 1.
- **Como exportar a hierarquia para outro formato?**
  A chave `linkage_z` é uma lista Python serializável em JSON:

```python
import json
with open('hierarquia.json', 'w') as f:
    json.dump(result['linkage_z'], f, indent=2)
```

- **Posso usar GPU para acelerar?**Atualmente, o backend Cython é CPU-only. Suporte a GPU está no roadmap futuro.
- **Como citar o MustaCHE?**

```bibtex
@software{mustache2026,
  title   = {MustaCHE: Multiple Cluster Hierarchies Explorer},
  author  = {[autores]},
  year    = {2026},
  url     = {https://test.pypi.org/project/mustache-core/},
  version = {0.3.0rc2}
}
```

---

## Referências

- Campello, R. J. G. B., et al. "Density-Based Clustering Based on Hierarchical Density Estimates." PAKDD 2013.
- Documentação oficial do HDBSCAN: [https://hdbscan.readthedocs.io/](https://hdbscan.readthedocs.io/)
- Core-SG (base do backend): [https://github.com/gabrieljorliano/core-sg](https://github.com/gabrieljorliano/core-sg)
- MustaCHE no TestPyPI: [https://test.pypi.org/project/mustache-core/0.3.0rc2/](https://test.pypi.org/project/mustache-core/0.3.0rc2/)
