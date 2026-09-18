# Manual de Reprodutibilidade — MustaCHE v2

**Projeto**: MustaCHE — Multiple Cluster Hierarchies Explorer  
**Versão documentada**: `mustache-core` v0.2.0 + `core-sg-mustache` v0.3.0  
**Data de validação**: 18/09/2026  
**Plataforma validada**: Windows 10/11 64-bit · Python 3.11.0  
**DOI do software**: *[a ser registrado no Zenodo]*  
**Repositório**: *[URL do GitHub]*

> Este documento segue as diretrizes de reprodutibilidade da **ACM Artifacts Review** e da **IEEE RepliQa**, permitindo que qualquer leitor do relatório técnico ou artigo reproduza integralmente os experimentos descritos.

---

## 1. Escopo da Reprodutibilidade

Este manual garante a reprodução de:

1. ✅ Instalação do ambiente em máquina **sem compilador C++** (via wheels pré-compiladas no TestPyPI);
2. ✅ Execução do motor de clustering `core-sg` com backend Cython nativo;
3. ✅ Execução da suíte de benchmarks do MustaCHE;
4. ✅ Geração dos CSVs, hierarquias e gráficos apresentados no relatório;
5. ✅ Validação da suíte de testes (55/55 aprovados).

---

## 2. Ambiente de Hardware e Software

### 2.1 Requisitos mínimos de hardware

| Componente | Mínimo | Recomendado |
| :--- | :--- | :--- |
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16 GB |
| **Disco** | 2 GB livres | 10 GB livres |
| **GPU** | Não requerida | Não requerida |

### 2.2 Requisitos de software

| Componente | Versão |
| :--- | :--- |
| **Sistema operacional** | Windows 10/11 64-bit |
| **Python** | 3.11.0 (obrigatório para a wheel `cp311-win_amd64`) |
| **pip** | $\ge 23.0$ |
| **Conexão com Internet** | Sim (para baixar pacotes do TestPyPI) |

> ⚠️ **Importante**: Não é necessário instalar Visual Studio Build Tools, MSVC, nem qualquer compilador C++. As wheels publicadas no TestPyPI já contêm os binários Cython pré-compilados (`.pyd`).

---

## 3. Instalação Reprodutível

### 3.1 Criar ambiente virtual isolado

```powershell
python -m venv venv_reproducao
.\venv_reproducao\Scripts\activate
```

### 3.2 Atualizar ferramentas de empacotamento

```powershell
pip install --upgrade pip setuptools wheel
```

### 3.3 Instalar o MustaCHE e suas dependências

```powershell
pip install --index-url https://test.pypi.org/simple \
            --extra-index-url https://pypi.org/simple \
            mustache-core==0.2.0
```

Este comando instala automaticamente:

| Pacote | Versão | Conteúdo |
| :--- | :--- | :--- |
| `mustache-core` | 0.2.0 | Motor analítico, CLI, Web UI |
| `core-sg-mustache` | 0.3.0 | Backend Cython compilado (`_mst_kruskal.pyd`, `_reweight.pyd`) |
| `numpy`, `pandas`, `scikit-learn`, `scipy`, `plotly`, `Flask`, `hdbscan`, `pynndescent` | *(automático)* | Dependências transitivas |

### 3.4 Fixar versões (lock de reprodutibilidade)

Para garantir que versões idênticas sejam usadas em execuções futuras:

```powershell
pip freeze > requirements.lock.txt
```

---

## 4. Validação da Instalação

### 4.1 Teste de importação

```powershell
python -c "import mustache; print('MustaCHE:', mustache.__version__)"
python -c "from mustache.core import run_clustering; print('Backend Cython OK')"
```

**Saída esperada**:
```text
MustaCHE: 0.2.0
Backend Cython OK
```

### 4.2 Teste funcional mínimo

```powershell
python -c "
from mustache.core import run_clustering
import numpy as np

X = np.random.RandomState(42).rand(300, 5)
result = run_clustering(X, method='hdbscan',
                        match_reference_implementation=True,
                        core_dist_n_jobs=1)
print('Labels únicos:', len(np.unique(result['labels'])))
"
```

**Saída esperada**:
```text
Labels únicos: <número inteiro ≥ 1>
```

### 4.3 Suíte de testes automatizada

```powershell
pip install pytest
pytest --tb=short
```

**Saída esperada**:
```text
55 passed in X.XXs
```

---

## 5. Execução dos Experimentos do Relatório

### 5.1 Obter os scripts do experimento

Os scripts usados para gerar os resultados do relatório estão versionados no repositório:

```powershell
git clone <URL_DO_REPOSITORIO>
cd MustaCHE/scripts/benchmarks
```

### 5.2 Seeds e parâmetros fixos

Para garantir reprodutibilidade total, os scripts utilizam:

| Parâmetro | Valor fixo | Justificativa |
| :--- | :--- | :--- |
| `random_state` | `42` | Seed determinística para geração de dados sintéticos |
| `core_dist_n_jobs` | `1` | Execução single-threaded para evitar não-determinismo de paralelismo |
| `match_reference_implementation` | `True` | Garante compatibilidade com o HDBSCAN de referência |
| `min_cluster_size` | conforme dataset | Especificado em cada script |
| `min_samples` | conforme dataset | Especificado em cada script |

### 5.3 Execução sequencial

```powershell
python run_benchmark_synthetic.py      # Seção 4.1 do relatório
python run_benchmark_real_datasets.py  # Seção 4.2 do relatório
python run_stability_analysis.py       # Seção 4.3 do relatório
python generate_figures.py             # Gráficos do relatório
```

### 5.4 Artefatos gerados

Após a execução, a pasta `output/` conterá:

```text
output/
├── csv/
│   ├── cluster_labels_*.csv
│   ├── stability_scores_*.csv
│   └── benchmark_summary.csv
├── hierarchies/
│   └── *.json   (árvores de dendrograma)
└── figures/
    ├── stability_comparison.png
    ├── hierarchy_visualization.png
    └── benchmark_heatmap.png
```

---

## 6. Verificação dos Resultados

### 6.1 Critérios de aceitação

| Verificação | Critério |
| :--- | :--- |
| **Idempotência** | Duas execuções consecutivas geram CSVs byte-idênticos |
| **Integridade** | Todos os 55 testes pytest passam |
| **Consistência** | Número de clusters e scores de estabilidade coincidem com os do relatório |

### 6.2 Comparação com resultados publicados

Os valores de referência estão em `output/expected_checksums.sha256`. Para validar:

```powershell
cd output
Get-FileHash -Algorithm SHA256 csv/*.csv | Compare-Object -ReferenceObject (Get-Content expected_checksums.sha256)
```

Se não houver divergência, os resultados são bit-a-bit idênticos aos publicados.

---

## 7. Limitações e Escopo de Plataforma

| Plataforma | Status | Observação |
| :--- | :--- | :--- |
| **Windows 64-bit + Python 3.11** | ✅ Validado | Wheel `cp311-win_amd64` disponível no TestPyPI |
| **Linux (manylinux)** | ⏳ Futuro | Requer CI/CD com `cibuildwheel` |
| **macOS (Intel/ARM)** | ⏳ Futuro | Requer CI/CD com `cibuildwheel` |
| **Python 3.10, 3.12, 3.13** | ⏳ Futuro | Requer rebuild das wheels |

Para plataformas não suportadas, o `pip` tentará compilar o `sdist`, o que exigirá um compilador C++ (MSVC no Windows, GCC no Linux, Clang no macOS).

---

## 8. Solução de Problemas

| Sintoma | Causa provável | Solução |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'mustache'` | Pacote não instalado | Reexecutar `pip install mustache-core==0.2.0` |
| `ImportError: DLL load failed` | Python diferente de 3.11 | Usar Python 3.11.0 exatamente |
| `ERROR: Could not find a version that satisfies the requirement` | `pip` sem acesso ao TestPyPI | Verificar `--index-url` e `--extra-index-url` |
| Resultados não-idênticos entre execuções | Paralelismo não controlado | Fixar `core_dist_n_jobs=1` e `random_state=42` |
| `error: Microsoft Visual C++ 14.0 is required` | `pip` tentando compilar `sdist` | Confirmar Python 3.11 64-bit e wheel correta |

---

## 9. Contato e Suporte

- **Autor**: Maylon [sobrenome] — [email UFSCar]
- **Orientador(a)**: [nome] — [email]
- **Instituição**: Universidade Federal de São Carlos (UFSCar)
- **Programa**: IC PIBIC-Af — 2025/2026

Dúvidas sobre reprodutibilidade devem ser registradas como *issues* no repositório do projeto.
