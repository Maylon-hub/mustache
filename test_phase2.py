import sys
import os
import pandas as pd
import numpy as np

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.core.batch import run_batch_clustering, analyze_batch_results

def test_phase2_logic():
    print("=== Testing Phase 2 Backend Logic ===")
    
    # 1. Load Data
    dataset_path = 'datasets/simple_2d.csv'
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        return
        
    print(f"Loading {dataset_path}...")
    df = pd.read_csv(dataset_path, header=None)
    print(f"Data shape: {df.shape}")
    
    # 2. Run Batch Clustering
    print("\n--- Running Batch HDBSCAN (mpts 2 to 5) ---")
    min_mpts = 2
    max_mpts = 5
    step = 1

    
    batch_results = run_batch_clustering(df, min_mpts, max_mpts, step)
    print(f"Batch execution complete. Calculated {len(batch_results)} hierarchies.")
    
    # Check one result
    mpts_5 = batch_results.get('5')
    if mpts_5:
        print(f"Result for mpts=5: {mpts_5['n_clusters']} clusters found.")
        print(f"Linkage Matrix shape: {len(mpts_5['linkage_z'])} merges.")
    else:
        print("Error: mpts=5 result missing!")
        
    # 3. Validation of HAI & Meta-Clustering
    print("\n--- Running Meta-Analysis (HAI + Meta-Clustering) ---")
    analysis = analyze_batch_results(batch_results)
    
    if 'error' in analysis:
        print(f"Analysis Failed: {analysis['error']}")
        return
        
    hai_matrix = np.array(analysis['hai_matrix'])
    print(f"HAI Matrix shape: {hai_matrix.shape}")
    print(f"HAI Matrix sample (top-left 3x3):\n{hai_matrix[:3, :3]}")
    
    meta_labels = analysis['meta_labels']
    print(f"Meta-Cluster Labels: {meta_labels}")
    print(f"Unique Meta-Clusters: {np.unique(meta_labels)}")
    
    medoids = analysis['medoids']
    print(f"Medoids (Meta-Cluster -> Representative mpts): {medoids}")
    
    print("\n=== Test Complete: SUCCESS ===")

if __name__ == "__main__":
    test_phase2_logic()
