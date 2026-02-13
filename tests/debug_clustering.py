import pandas as pd
from app.core.clustering import run_hdbscan
import os

# Create a minimal test script to debug the 500 error
try:
    print("Loading synthetic_large.csv...")
    df = pd.read_csv('datasets/synthetic_large.csv')
    print(f"Data shape: {df.shape}")
    
    params = {
        'min_cluster_size': 10,
        'min_samples': 2,
        'metric': 'euclidean',
        'cluster_selection_method': 'eom'
    }
    
    print(f"Running HDBSCAN with params: {params}...")
    results = run_hdbscan(df, params)
    
    print("SUCCESS!")
    print(f"Clusters: {results['n_clusters']}")
    print(f"Noise: {results['noise_points']}")

except Exception as e:
    print(f"Error caught: {e}")
    import traceback
    traceback.print_exc()
