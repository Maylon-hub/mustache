import pandas as pd
import numpy as np
import importlib.metadata
import sys

print("==================================================")
print("Testing MustaCHE (Multiple Cluster Hierarchies Explorer) package")
print("==================================================")

# 1. Package Name and version check
try:
    pkg_version = importlib.metadata.version('mustache-core')
    print(f"mustache-core package version installed: {pkg_version}")
except importlib.metadata.PackageNotFoundError:
    print("mustache-core is not registered in pip metadata (possibly installed in development/non-standard mode).")

# 2. Try importing the mustache module
try:
    import mustache
    print("Successfully imported the 'mustache' module.")
except ImportError as e:
    print(f"FAILED to import 'mustache' module: {e}")
    sys.exit(1)

# 3. Check for core-sg backend
has_coresg = False
try:
    import core_sg
    print("core-sg backend is available.")
    has_coresg = True
except ImportError:
    print("core-sg backend is NOT available (requires C++ compilers or pre-built wheels).")

# 4. Run standard clustering (scikit-learn HDBSCAN backend)
print("\n--- Running Clustering Test (Standard HDBSCAN) ---")
try:
    from mustache.core.clustering import run_clustering
    # Create dummy numeric data (two blobs)
    np.random.seed(42)
    blob1 = np.random.normal(loc=0.0, scale=0.5, size=(10, 2))
    blob2 = np.random.normal(loc=5.0, scale=0.5, size=(10, 2))
    dummy_data = np.vstack([blob1, blob2])
    df = pd.DataFrame(dummy_data, columns=['x', 'y'])
    
    results_std = run_clustering(df, min_cluster_size=3, min_samples=3, algorithm='standard')
    print("Standard clustering execution: SUCCESS!")
    print(f"Found {results_std['n_clusters']} clusters and {results_std['noise_points']} noise points.")
except Exception as e:
    print(f"Standard clustering execution: FAILED: {e}")

# 5. Run core-sg clustering if available
if has_coresg:
    print("\n--- Running Clustering Test (Core-SG) ---")
    try:
        results_core = run_clustering(df, min_cluster_size=3, min_samples=3, algorithm='core-sg')
        print("Core-SG clustering execution: SUCCESS!")
        print(f"Found {results_core['n_clusters']} clusters and {results_core['noise_points']} noise points.")
    except Exception as e:
        print(f"Core-SG clustering execution: FAILED: {e}")
else:
    print("\nSkipping Core-SG clustering test since core-sg is not installed.")

print("\n==================================================")
print("Test completed.")
print("==================================================")
