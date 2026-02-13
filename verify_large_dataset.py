import pandas as pd
import numpy as np
from sklearn.datasets import make_blobs
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())
from app.core.batch import run_batch_clustering, analyze_batch_results

def verify_large_dataset():
    print("=== Generating Large Synthetic Dataset ===")
    
    # 1. Create Data (500 samples, 4 centers)
    X, y = make_blobs(n_samples=500, centers=4, n_features=2, random_state=42, cluster_std=1.2)
    
    # Create DataFrame
    df = pd.DataFrame(X, columns=['x', 'y'])
    
    # 2. Save to datasets/
    base_dir = os.path.dirname(os.path.abspath(__file__)) # /app
    datasets_dir = os.path.join(base_dir, 'datasets')
    os.makedirs(datasets_dir, exist_ok=True)
    
    df_path = os.path.join(datasets_dir, 'synthetic_large.csv')
    labels_path = os.path.join(datasets_dir, 'synthetic_large_labels.csv')
    
    df.to_csv(df_path, index=False)
    # Save labels with header 'label'
    pd.DataFrame(y, columns=['label']).to_csv(labels_path, index=False)
    
    print(f"Dataset saved to: {df_path}")
    print(f"Labels saved to: {labels_path}")
    
    # 3. Test Parameters
    min_mpts = 5
    max_mpts = 50
    step = 5
    
    print(f"\n=== Running Batch Clustering ===")
    print(f"Points: 500")
    print(f"mpts range: {min_mpts} -> {max_mpts} (step {step})")
    
    # 4. Run Batch
    batch_results = run_batch_clustering(df, min_mpts, max_mpts, step)
    
    runs = len(batch_results)
    expected_runs = len(range(min_mpts, max_mpts + 1, step))
    print(f"\nBatch completed. Got {runs} results (Expected {expected_runs}).")
    
    if runs == 0:
        print("FAIL: No batch results.")
        return
        
    # 5. Analyze HAI
    print("\n=== Analyzing HAI Matrix ===")
    analysis = analyze_batch_results(batch_results)
    
    if 'error' in analysis:
        print(f"FAIL Analysis: {analysis['error']}")
        return
        
    hai_matrix = np.array(analysis['hai_matrix'])
    
    print(f"HAI Matrix shape: {hai_matrix.shape}")
    print(f"Values Range: {hai_matrix.min():.4f} - {hai_matrix.max():.4f}")
    print(f"Mean HAI: {hai_matrix.mean():.4f}")
    
    unique_vals = np.unique(hai_matrix)
    if len(unique_vals) > 1:
        print("SUCCESS: HAI Matrix has varying values.")
    else:
        print("FAIL: HAI Matrix is constant (one color issu??).")
        
    # Also print medoids to check
    print("\nCorrect Medoids found:", analysis['medoids'])

if __name__ == "__main__":
    verify_large_dataset()
