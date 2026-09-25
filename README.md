# MustaCHE (Multiple Cluster Hierarchies Explorer)

![TestPyPI Version](https://img.shields.io/badge/TestPyPI-mustache--core%20v0.3.0rc1-blue)
![Backend Version](https://img.shields.io/badge/backend-core--sg--mustache%20v0.4.5rc1-green)
![Python Version](https://img.shields.io/badge/python-3.11-blue)
![Platform](https://img.shields.io/badge/platform-win__amd64-lightgrey)

**MustaCHE** is an interactive web-based visual analytics tool for exploring hierarchical density-based clustering. It enables users to analyze multiple clustering hierarchies generated across a wide range of density parameters ($m_{pts}$) simultaneously, offering deep insights into cluster stability, hierarchy relationships, and data partitioning.

In **MustaCHE v2**, the application has been completely re-engineered into a **100% native Python package** (`mustache-core`), removing all legacy Java and Docker dependencies. It integrates the state-of-the-art **Core-SG (Core Structure Graph)** engine with Cython acceleration (`core-sg-mustache`) for ultra-fast Minimum Spanning Tree (MST) computation and includes a built-in Command Line Interface (CLI).

---

## 🌟 Key Features

- **100% Native Python**: No Docker or Java required. Install and run directly via Python/pip.
- **Core-SG & HDBSCAN Integration**: Accelerated density-based clustering powered by `core-sg-mustache` for scalable multiple MST extractions.
- **Pre-compiled Wheels**: Windows 64-bit pre-compiled binaries available on TestPyPI—no C++ compiler or Visual Studio required for installation.
- **Optimized Reachability Plots**: Built-in OPTICS caching mechanism speeding up reachability rendering during batch processing.
- **Interactive Visualizations (Plotly.js & D3.js)**:
  - **Meta-Clustering Dendrogram**: Hierarchically cluster different parameter configurations with dynamic cut thresholding.
  - **HAI Similarity Matrix**: Visualizes structural agreement between clustering partitions across parameter ranges.
  - **Reachability Plot**: Highlights density valleys corresponding to physical clusters.
  - **2D Projection Scatter Map**: Spatial projection powered by t-SNE (single-analysis API responses).
  - **Manual Branch Selection**: Click a meta-dendrogram branch to select every `mpts` hierarchy below it, then save the selection with the project or export those partitions to CSV.
- **CLI & Web Dashboard**: Run with a single command (`mustache`) or import functions directly into Python scripts and Jupyter Notebooks.
- **Ground Truth Validation**: Support for external label files to calculate Adjusted Rand Index (ARI) and Adjusted Mutual Information (AMI).

---

## 🚀 Quick Start (Running via Python Package)

### Prerequisites

- **Python >= 3.10** (tested on Python 3.10, 3.11, 3.12, 3.13).
- Pre-built binary wheels (`.whl`) with native Cython acceleration (`core-sg-mustache>=0.4.5rc1`) available for Windows 64-bit, Linux, and macOS—no C++ compiler or Visual Studio required for end users.

### 1. Create and Activate a Virtual Environment

It is strongly recommended to install the package in an isolated virtual environment:

```bash
# Create virtual environment (.venv)
python -m venv .venv
```

Activate the environment based on your operating system and shell:

- **Windows (PowerShell)**:

  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

  > [!TIP]
  > **PowerShell Script Execution Error (`PSSecurityException`)?**  
  > If Windows blocks the script execution, run this command **once** in PowerShell to allow virtual environment scripts for your current user:
>
  > ```powershell
  > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  > ```
>
  > Press `Y` (or `S`) when prompted, then re-run `.\.venv\Scripts\Activate.ps1`.
- **Windows (Command Prompt / CMD)**:

  ```cmd
  .\.venv\Scripts\activate.bat
  ```

- **Windows (Git Bash)**:

  ```bash
  source .venv/Scripts/activate
  ```

- **Linux / macOS (Bash / Zsh)**:

  ```bash
  source .venv/bin/activate
  ```

### 2. Upgrade pip

Ensure `pip` is updated to avoid build or dependency resolution issues:

```bash
python -m pip install --upgrade pip
```

### 3. Install mustache-core

A single `pip install` command installs MustaCHE along with all required dependencies—including the **`core-sg-mustache`** backend engine, Flask, NumPy, Pandas, Scikit-Learn, Scipy, HDBSCAN, and Plotly. **End users do not need to install `core-sg-mustache` separately.**

- **From TestPyPI (release candidate v0.3.0rc1)**:

  ```bash
  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ --pre mustache-core==0.3.0rc1
  ```

- **From PyPI (Official release)**:
  *Coming soon*

> [!TIP]
> **Automatic Dependency Resolution**: Because `core-sg-mustache` is declared in `mustache-core`'s package specifications (`pyproject.toml`), `pip` automatically discovers and installs `core-sg-mustache` without any separate commands.

> [!NOTE]
> The package is named **`mustache-core`** for installation via `pip`, but inside Python scripts and notebooks you import it as:
>
> ```python
> import mustache
> ```

### 4. Launch the Application

Run the built-in CLI command in your terminal:

```bash
mustache
```

Custom host and port options:

```bash
mustache --host 127.0.0.1 --port 5000 --debug
```

*(Alternative command if the global script is not directly resolved in your shell)*:

```bash
python -m mustache.cli
```

Once started, open your web browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🛠️ Local Development Setup (From Source Code)

If you are developing locally or contributing to the codebase, follow these steps to run MustaCHE directly from source without Docker.

### Prerequisites

- **Python 3.11.0 (64-bit)**
- **Git**

### Step-by-Step Guide

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/maylon-hub/mustache.git
   cd mustache
   ```

2. **Create and Activate a Virtual Environment**:
   - **Windows (PowerShell)**:

     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

     *(If script execution is blocked, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once)*
   - **Windows (Command Prompt / CMD)**:

     ```cmd
     .\.venv\Scripts\activate.bat
     ```

   - **Windows (Git Bash)**:

     ```bash
     source .venv/Scripts/activate
     ```

   - **Linux / macOS**:

     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Dependencies and the Package in Editable Mode**:

   ```bash
   python -m pip install --upgrade pip
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ -e .
   ```

   > [!NOTE]
   > - If developing both packages simultaneously from source, build and install your local clone of `core-sg-mustache` first:
>
   >   ```bash
   >   pip install -e ../core-sg
   >   pip install -e .
   >   ```

4. **Start the Application**:
   You can run the server via the CLI command:

   ```bash
   mustache
   ```

   Or run it directly as a Python module:

   ```bash
   python -m mustache.cli
   ```

5. **Open the Dashboard**:
   Open your browser at **`http://127.0.0.1:5000`**.

---

## 🐍 Using MustaCHE as a Python Library

You can import MustaCHE algorithms directly into your Python scripts or Jupyter Notebooks:

An executable example is available at [`examples/mustache_quickstart.ipynb`](examples/mustache_quickstart.ipynb).

```python
import pandas as pd
from mustache.core import run_clustering
from mustache.core.batch import run_batch_clustering

# Load numerical dataset
df = pd.read_csv("datasets/sample_data.csv", header=None)

# 1. Run single clustering analysis
result = run_clustering(
    df, 
    min_cluster_size=5, 
    min_samples=5, 
    metric="euclidean", 
    algorithm="core-sg"  # Options: 'core-sg' or 'hdbscan'
)
print(f"Number of clusters found: {result['n_clusters']}")

# 2. Run batch parameter exploration (mpts sweep)
batch_results = run_batch_clustering(
    df, 
    min_mpts=5, 
    max_mpts=25, 
    step=2, 
    metric="euclidean", 
    algorithm="core-sg"
)
print(f"Processed {len(batch_results)} hierarchies.")
```

---

## 📖 Usage Guide

### 1. Upload Dataset

- Under the **Dataset (CSV)** section, upload a CSV file containing numerical feature values (comma-separated).

### 2. (Optional) Ground Truth Labels

- Upload a single-column CSV containing integer cluster labels to calculate ARI and AMI validation metrics.

### 3. Configure Clustering Parameters

- **Min Cluster Size**: Smallest grouping considered a valid cluster.
- **Min Samples**: Density threshold / neighborhood size.
- **Distance Metric**: `Euclidean` or `Manhattan`.
- **Algorithm**: `core-sg` (recommended for fast Cython MST computation) or `hdbscan` (standalone reference HDBSCAN).

### 4. Batch Analysis

- In the **Batch Analysis** section, define a range of $m_{pts}$ values (`Min`, `Max`, `Step`).
- MustaCHE runs the hierarchy sweep, calculates the HAI similarity matrix, builds the meta-clustering dendrogram, and prepares the reachability plots.
- HAI is exact up to 2,000 samples. Above that threshold, MustaCHE uses a deterministic sample of point pairs and reports the method, seed, pair count, confidence, and conservative error bound in `analysis['hai_computation']`.

### 5. Select, Save, and Export Branches

- Activate the wand tool and click a blue branch in the meta-dendrogram. Every leaf (`mpts`) below that branch is selected and the branch turns green.
- Click the same branch again to remove those hierarchies, or use **Clear selection**.
- **Save Analysis** preserves the selected `mpts` values in the saved project.
- **Export CSV** exports the selected hierarchies. With no manual selection, it exports the active medoids.

### 6. Export Results

- Click **Export CSV** to download the input data together with cluster labels and membership probabilities for the selected hierarchies.

---

## 📁 Project Structure

```
mustache/
├── datasets/                 # Sample datasets for testing (CSV format)
├── docs/                     # Detailed documentation & reproducibility guides
│   ├── guia_documentacao.md  # API reference & user guide
│   └── reproducao.md         # Reproducibility manual
├── mustache/                 # Main Python package
│   ├── __init__.py           # Flask application factory
│   ├── cli.py                # Command Line Interface (CLI) entrypoint
│   ├── routes.py             # Flask HTTP routes and API endpoints
│   ├── core/                 # Core clustering algorithms and logic
│   │   ├── __init__.py       # Core module exports
│   │   ├── clustering.py     # HDBSCAN & Core-SG clustering runner
│   │   ├── batch.py          # Batch parameter exploration & caching
│   │   └── hai.py            # Hierarchy Agreement Index calculation
│   ├── static/               # CSS, Plotly JS, and image assets
│   └── templates/            # HTML templates (dashboard, settings, etc.)
├── MANIFEST.in               # Manifest rules for non-code packaging
├── pyproject.toml            # PEP 517/518 build and metadata configuration
├── requirements.txt          # Development dependencies
└── README.md                 # Project documentation
```

---

## 📄 License & Credits

- **Original MustaCHE Concept & Authors**:
  Antonio Cavalcante Araujo Neto, Mario A. Nascimento, Joerg Sander, and Ricardo J. G. B. Campello (2018).
- **Modernization, Core-SG Integration & Cython Backend**:
  Maylon Martins de Melo (2025-2026), Federal University of São Carlos (UFSCar).
