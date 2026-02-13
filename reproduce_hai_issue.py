import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.getcwd())
from app.core.batch import run_batch_clustering, analyze_batch_results
from app.core.hai import compute_hai_matrix

def create_synthetic_dataset(n_samples=50):
    # Create 3 clusters
    c1 = np.random.normal(0, 1, size=(n_samples // 3, 2))
    c2 = np.random.normal(5, 1, size=(n_samples // 3, 2))
    c3 = np.random.normal(10, 1, size=(n_samples // 3, 2))
    data = np.vstack([c1, c2, c3])
    df = pd.DataFrame(data, columns=['x', 'y'])
    return df

def test_reproduction():
    print("=== Testing HAI Reproduction ===")
    
    # 1. Use larger synthetic dataset
    np.random.seed(42)
    df = create_synthetic_dataset(60)
    print(f"Dataset shape: {df.shape}")
    
    # 2. Run Batch Clustering (mpts 2 to 10)
    # With 60 points, mpts 2 vs 10 should produce different hierarchies.
    print("\n--- Running Batch HDBSCAN (mpts 2 to 10) ---")
    min_mpts = 2
    max_mpts = 10
    step = 1
    
    batch_results = run_batch_clustering(df, min_mpts, max_mpts, step)
    print(f"Batch execution complete. Calculated {len(batch_results)} hierarchies.")
    
    # 3. Analyze HAI
    print("\n--- Analyzing HAI Matrix ---")
    analysis = analyze_batch_results(batch_results)
    
    if 'error' in analysis:
        print(f"Analysis Failed: {analysis['error']}")
        return
        
    hai_matrix = np.array(analysis['hai_matrix'])
    print(f"HAI Matrix shape: {hai_matrix.shape}")
    print("HAI Matrix values:")
    print(hai_matrix)
    
    # Check if all values are identical
    unique_vals = np.unique(hai_matrix)
    print(f"Unique HAI values: {unique_vals}")
    
    if len(unique_vals) == 1:
        print("ISSUE CONFIRMED: All HAI values are identical.")
    else:
        print("NO ISSUE: SAI values vary.")

if __name__ == "__main__":
    test_reproduction()
