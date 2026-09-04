# MustaCHE (Multiple Cluster Hierarchies Explorer)

**MustaCHE** is an interactive web-based visual analytics tool for exploring hierarchical density-based clustering. It enables users to analyze multiple clustering hierarchies generated across a wide range of density parameters ($m_{pts}$) simultaneously, offering deep insights into cluster stability, hierarchy relationships, and data partitioning.

In **MustaCHE v2**, the application has been completely re-engineered into a **100% native Python package** (`mustache-core`), removing all legacy Java and Docker dependencies. It integrates the state-of-the-art **Core-SG (Core Structure Graph)** engine for ultra-fast Minimum Spanning Tree (MST) computation and includes a built-in Command Line Interface (CLI).

---

## 🌟 Key Features

- **100% Native Python**: No Docker or Java required. Install and run directly via Python/pip.
- **Core-SG & HDBSCAN Integration**: Accelerated density-based clustering powered by `core-sg` for scalable multiple MST extractions.
- **Optimized Reachability Plots**: Built-in OPTICS caching mechanism speeding up reachability rendering by up to **~11x (91% faster)** during batch processing.
- **Interactive Visualizations (Plotly.js)**:
  - **Meta-Clustering Dendrogram**: Hierarchically cluster different parameter configurations with dynamic cut thresholding.
  - **HAI Similarity Matrix**: Visualizes structural agreement between clustering partitions across parameter ranges.
  - **Reachability Plot**: Highlights density valleys corresponding to physical clusters.
  - **2D Projection Scatter Map**: Spatial projection powered by t-SNE.
- **CLI & Web Dashboard**: Run with a single command (`mustache`) or import functions directly into Python scripts and Jupyter Notebooks.
- **Ground Truth Validation**: Support for external label files to calculate Adjusted Rand Index (ARI) and Adjusted Mutual Information (AMI).

---

## 🚀 Quick Start (Running via Python Package)

### 1. Installation via pip

Once published or installed from PyPI:

```bash
pip install mustache-core
```

*(If installing from TestPyPI)*:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mustache-core
```

### 2. Launch the Application

Run the built-in CLI command in your terminal:

```bash
mustache
```

Custom host and port options:
```bash
mustache --host 127.0.0.1 --port 5000 --debug
```

Once started, open your web browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🛠️ Local Development Setup (From Source Code)

If you are developing locally or contributing to the codebase, follow these steps to run MustaCHE directly from source without Docker.

### Prerequisites
- **Python >= 3.10** (Python 3.11 or 3.12 recommended)
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
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Dependencies and the Package in Editable Mode**:
   ```bash
   pip install --upgrade pip
   pip install -e .
   ```

   *(Optional)* If you are also working on a local version of `core-sg`:
   ```bash
   pip install -e ../core-sg
   ```

4. **Start the Application**:
   You can run the server via the CLI command:
   ```bash
   mustache
   ```

   Or run it directly as a Python module:
   ```bash
   python -m mustache.cli
   ```

   Or execute the script directly:
   ```bash
   python mustache/cli.py
   ```

5. **Open the Dashboard**:
   Open your browser at **`http://127.0.0.1:5000`**.

---

## 🐍 Using MustaCHE as a Python Library

You can also import MustaCHE algorithms directly into your Python scripts or Jupyter Notebooks:

```python
import pandas as pd
from mustache.core.clustering import run_clustering
from mustache.core.batch import run_batch_clustering

# Load numerical dataset (without headers)
df = pd.read_csv("datasets/sample_data.csv", header=None)

# 1. Run single clustering analysis
result = run_clustering(
    df, 
    min_cluster_size=5, 
    min_samples=5, 
    metric="euclidean", 
    algorithm="core-sg"  # or 'standard'
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
print(f"Processed {len(batch_results['results'])} hierarchies.")
```

---

## 📖 Usage Guide

### 1. Upload Dataset
- Under the **Dataset (CSV)** section, upload a CSV file containing numerical feature values (comma-separated, without header row).
- Example format:
  ```csv
  1.2,3.4,5.6
  2.1,4.3,6.5
  0.8,3.1,4.9
  ```

### 2. (Optional) Ground Truth Labels
- Upload a single-column CSV containing integer cluster labels to calculate ARI and AMI validation metrics.

### 3. Configure Clustering Parameters
- **Min Cluster Size**: Smallest grouping considered a valid cluster.
- **Min Samples**: Density threshold / neighborhood size.
- **Distance Metric**: `Euclidean` or `Manhattan`.
- **Algorithm**: `core-sg` (recommended for faster MST computation) or `standard` (scikit-learn HDBSCAN).

### 4. Batch Analysis
- In the **Batch Analysis** section, define a range of $m_{pts}$ values (`Min`, `Max`, `Step`).
- MustaCHE runs the hierarchy sweep, calculates the HAI similarity matrix, builds the meta-clustering dendrogram, and caches the reachability plots.

### 5. Export Results
- Click **"Export JSON"** to download metrics, cluster labels, and chart data.

---

## 📁 Project Structure

```
mustache/
├── datasets/                 # Sample datasets for testing (CSV format)
├── mustache/                 # Main Python package
│   ├── __init__.py           # Flask application factory
│   ├── cli.py                # Command Line Interface (CLI) entrypoint
│   ├── routes.py             # Flask HTTP routes and API endpoints
│   ├── core/                 # Core clustering algorithms and logic
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
- **Modernization & Core-SG Integration**:
  Maylon Martins de Melo (2025-2026), Federal University of São Carlos (UFSCar).
- **License**: [BSD 3-Clause License](LICENSE).

---

## 🎓 Citation

If you use MustaCHE in your research, please cite the original publication:

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
