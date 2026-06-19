# MustaCHE (Multiple Cluster Hierarchies Explorer)

**MustaCHE** is an interactive, web-based visualization tool designed for exploring hierarchical density-based clustering. It allows users to analyze multiple clustering hierarchies generated under a wide range of density parameters ($m_{pts}$) simultaneously, offering key insights into cluster stability and dataset structure. 

In this version (**MustaCHE v2**), the application has been completely re-engineered from its legacy Java and Python 2.7 codebase into a native, high-performance Python 3.11 stack. It is now fully integrated with the state-of-the-art **Core-SG (Core Structure Graph)** engine for fast MST (Minimum Spanning Tree) computations, and is designed to run natively as a packaged Python application.

---

## 🌟 Key Features

- **Core-SG & HDBSCAN Clustering**: Integrated with the advanced `core-sg` engine for extremely fast calculations of multiple MSTs, scaling seamlessly to larger datasets.
- **Ultra-Fast Reachability Plots**: Employs an optimized OPTICS bypass caching mechanism, accelerating the batch reachability calculation by up to **91% (~11x speedup)**.
- **Interactive Visualizations (Plotly.js)**:
  - **Dendrogram of Meta-Clusters**: Visualizes how hierarchies group together and lets you select dynamic cutting thresholds.
  - **HAI Similarity Matrix**: Visualizes structural agreement between clustering partitions across parameter variations.
  - **Interactive Reachability Plot**: Identifies valley structures indicating density-based clusters.
  - **2D Projection Scatter Map**: Powered by t-SNE for dimensional projection.
- **Ground Truth Validation**: Upload known labels for automatic Adjusted Rand Index (ARI) and Adjusted Mutual Info (AMI) calculation.
- **Python Packaging & CLI**: Fully packaged library that can be launched directly using the `mustache` command line interface.

---

## 🚀 Running Locally (For Developers)

To run the application locally on your machine from the source code, follow these steps:

### Prerequisites
- **Python >= 3.10** installed.
- Git (for cloning the repositories).

### Installation Steps

1. **Clone the repositories**:
   Ensure you have both the `mustache` repository and its companion dependency `core-sg` cloned in the same directory:
   ```bash
   git clone https://github.com/Maylon-hub/core-sg.git
   git clone https://github.com/Maylon-hub/mustache.git
   ```

2. **Set up a Virtual Environment**:
   Navigate to the `mustache` directory, create and activate a virtual environment:
   ```bash
   cd mustache
   python -m venv venv
   
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Core-SG in Editable Mode**:
   Install the adjacent `core-sg` dependency in your active virtual environment:
   ```bash
   pip install -e ../core-sg
   ```

4. **Install MustaCHE in Editable Mode**:
   Install `mustache-core` and its required packages:
   ```bash
   pip install -e .
   ```

5. **Start the Application**:
   You can launch the server using the command-line utility:
   ```bash
   mustache --port 5000
   ```
   *Alternatively*, you can run the entry script directly:
   ```bash
   python mustache/cli.py
   ```

6. **Access the Interface**:
   Open your web browser and navigate to **`http://127.0.0.1:5000`**.

---

## 📦 Installation via PyPI (Once Published)

Once published on PyPI, users will be able to install and run the tool globally with a single command without dealing with cloning repositories manually.

### Installation
```bash
pip install mustache-core
```

### Running the App
After installation, the CLI tool will be registered on your system path. Simply run:
```bash
mustache
```
You can customize the host, port, and run mode using command line flags:
```bash
mustache --host 0.0.0.0 --port 8080 --debug
```

---

## 📖 Usage Guide

### 1. Upload Dataset
- Under the **Dataset (CSV)** input, choose a numerical dataset file (no headers, values separated by commas).
- Example formatting:
  ```csv
  0.23,1.45,-0.67
  0.11,2.02,-0.12
  ...
  ```

### 2. (Optional) Upload Ground Truth Labels
- Upload a single-column CSV with integer labels representing the ground truth.
- This will enable automatic calculation and display of clustering validation metrics (ARI, AMI).

### 3. Adjust Parameters & Run
- **Min Cluster Size**: Minimum size to form a density cluster.
- **Min Samples**: Controls the tolerance for noise points.
- **Distance Metric**: Euclidean or Manhattan.
- **Algorithm**: Select `core-sg` for accelerated MST processing or `standard` for classical Scikit-Learn HDBSCAN.
- Click **"Run Clustering"** to execute the pipeline and render interactive charts.

### 4. Batch Parameter Exploration
- Use the **Batch mode** to specify a range of values for $m_{pts}$ (e.g., Min: 5, Max: 30, Step: 2).
- MustaCHE will calculate clustering hierarchies for all parameters, compute the pairwise agreement matrix (HAI), construct the meta-clustering dendrogram, and cache the reachability plot to show how hierarchies evolve.

---

## 📁 Project Directory Structure

```
mustache/
├── datasets/             # Sample datasets for demonstration
├── mustache/             # Core Python package modules
│   ├── core/             # Mathematical algorithms (clustering, HAI, batch logic)
│   ├── static/           # UI CSS, dynamic Javascript, and logos
│   ├── templates/        # Flask HTML layouts
│   ├── cli.py            # CLI launcher setup
│   └── routes.py         # Flask API controllers and routing
├── pyproject.toml        # Build metadata configuration
├── requirements.txt      # Dev environment dependency lock
└── README.md             # Project documentation
```

---

## 📄 License & Credits

- **Original concept and code**: Araujo Neto, Antonio Cavalcante, Mario A. Nascimento, Joerg Sander, and Ricardo J. G. B. Campello (2018).
- **Reengineered Version**: Maylon Martins de Melo (2025-2026).
- **License**: Licensed under the [BSD 3-Clause License](LICENSE).

---

## 🎓 Citation

If you use MustaCHE in your research or applications, please cite the original publication:

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
