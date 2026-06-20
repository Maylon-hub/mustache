# MustaCHE v2 (Multiple Cluster Hierarchies Explorer)

**MustaCHE** é uma ferramenta interativa e baseada em web para exploração e análise visual de múltiplos agrupamentos hierárquicos baseados em densidade (HDBSCAN). Ele permite analisar a estabilidade de agrupamentos sob diversas variações de parâmetros simultaneamente.

Nesta versão v2, o projeto foi reengenheirado de sua base legado (Java/Python 2.7) para um **pacote Python nativo** integrado ao motor de alto desempenho **Core-SG** para o cálculo acelerado de Árvores Geradoras Mínimas (MST).

---

## 🌟 Recursos Principais

* **Motor Principal Core-SG**: Integração com a biblioteca de aceleração de grafos e cálculo de MSTs.
* **Interface CLI Simples**: Suba o servidor local executando apenas um comando no terminal.
* **Visualizações Interativas (Plotly)**:
  * **Dendrograma de Meta-Agrupamentos**: Visualize a evolução das partições e defina limites dinâmicos de corte.
  * **Matriz de Similaridade HAI**: Analise a concordância estrutural entre diferentes valores de parâmetros.
  * **Gráfico de Acessibilidade (Reachability Plot)**: Detecte estruturas de vales que revelam grupos densos.
  * **Projeção 2D (t-SNE)**: Visualize a distribuição espacial dos pontos e coloração por grupo.
* **Validação Científica**: Suporte para upload de rótulos reais (*ground truth*) e cálculo automático de métricas (ARI e AMI).

---

## 📦 Instalação

### Pré-requisitos
* **Python >= 3.10** instalado em sua máquina.

### ⚠️ Importante sobre a Compilação do Core-SG
O **Core-SG** é o motor de agrupamento obrigatório e principal do MustaCHE. Ele possui módulos de desempenho escritos em Cython (`.pyx`) que requerem compilação.
* **Python 3.10 a 3.12**: Possuem rodas pré-compiladas (*wheels*) disponíveis no PyPI para as plataformas mais comuns, instalando instantaneamente.
* **Python 3.13 ou plataformas sem wheels pré-compiladas**: O `pip` tentará compilar o código fonte do `core-sg` localmente. Para isso, você precisará de compiladores C++ instalados no sistema operacional:
  * **Windows**: Instale o [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (selecione a opção "Desenvolvimento para desktop com C++").
  * **Linux (Ubuntu/Debian)**: Rode `sudo apt install build-essential`.
  * **macOS**: Instale o Xcode Command Line Tools executando `xcode-select --install` no terminal.

### Passo 1: Instalação via Pip
Como o pacote é publicado no **TestPyPI** para validação, utilize o comando abaixo para puxar o pacote base e suas dependências de terceiros do PyPI principal:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mustache-core
```

*(Uma vez publicado no PyPI oficial, o comando simplificado será apenas `pip install mustache-core`)*.

---

## 🚀 Como Usar

### Nome do Pacote vs. Namespace de Importação
* O pacote é instalado via terminal sob o nome **`mustache-core`**.
* Para importação em scripts Python ou Notebooks, o namespace correto é **`mustache`** (não `mustache_core`):
  ```python
  import mustache
  ```

### 💻 Rodando a Interface Web (CLI)
Após a instalação, a ferramenta registra o comando global `mustache` no seu terminal. Para iniciar a interface:

```bash
mustache
```

Você também pode personalizar a porta e o endereço de IP do servidor:
```bash
mustache --host 127.0.0.1 --port 8080 --debug
```

Abra seu navegador e acesse: **`http://127.0.0.1:5000`** (ou a porta escolhida).

### 📓 Rodando em Scripts Python / Notebooks
Se quiser rodar o fluxo de agrupamento de forma programática ou testar sua instalação, crie um script como o exemplo abaixo:

```python
import pandas as pd
import numpy as np
from mustache.core.clustering import run_clustering

# 1. Gerar dados numéricos sintéticos
np.random.seed(42)
dados = np.vstack([
    np.random.normal(loc=0.0, scale=0.5, size=(15, 2)),
    np.random.normal(loc=5.0, scale=0.5, size=(15, 2))
])
df = pd.DataFrame(dados, columns=['x', 'y'])

# 2. Executar o agrupamento utilizando o motor principal Core-SG
print("Executando agrupamento com Core-SG...")
resultados = run_clustering(df, min_cluster_size=3, min_samples=3, algorithm='core-sg')

print(f"Sucesso! Grupos encontrados: {resultados['n_clusters']}")
print(f"Pontos de ruído detectados: {resultados['noise_points']}")
```

---

## 📁 Estrutura do Repositório

```
mustache/
├── datasets/             # Datasets de exemplo (.csv)
├── mustache/             # Código-fonte da aplicação
│   ├── core/             # Algoritmos principais (clustering, HAI, batch, etc.)
│   ├── static/           # Arquivos estáticos da interface web (CSS, JS, imagens)
│   ├── templates/        # Templates Flask (HTML)
│   ├── cli.py            # Script do ponto de entrada CLI
│   └── routes.py         # Endpoints da API Flask e rotas do Dashboard
├── pyproject.toml        # Metadados de empacotamento (setuptools)
├── requirements.txt      # Dependências de desenvolvimento locais
└── README.md             # Este arquivo de documentação
```

---

## 🎓 Citação

Se você utilizar o MustaCHE em pesquisas acadêmicas, cite a publicação original dos autores:

```bibtex
@article{neto2018mustache,
  title={MustaCHE: A Multiple Clustering Hierarchies Explorer},
  author={Neto, Antonio Cavalcante Araujo and Nascimento, Mario A and Sander, Joerg and Campello, Ricardo JGB},
  journal={Proceedings of the VLDB Endowment},
  volume={11},
  number={12},
  pages={2058--2061},
  year={2018},
  publisher={VLDB Endowment}
}
```

---
**Desenvolvido originalmente por**: Neto et al. (2018)  
**Reengenharia e Integração com Core-SG por**: Maylon Martins de Melo (Iniciação Científica - UFSCar)
