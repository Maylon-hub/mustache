import numpy as np
import pandas as pd
from .clustering import run_clustering

def run_batch_clustering(df, min_mpts, max_mpts, step, metric='euclidean'):
    """
    Runs HDBSCAN for a range of mpts values.
    Returns a dictionary where keys are mpts values and values are clustering results.
    """
    results = {}
    
    # Ensure numerical data
    data = df.select_dtypes(include=[np.number])
    
    # Loop through mpts range
    # In HDBSCAN, min_cluster_size is typically the main parameter.
    # We will vary min_cluster_size and keep min_samples = min_cluster_size (standard behavior)
    # unless specified otherwise.
    
    for mpts in range(min_mpts, max_mpts + 1, step):
        # We use mpts for both min_cluster_size and min_samples mimicking legacy behavior
        # where 'mpts' controlled the scale.
        
        # Run clustering for this specific mpts
        # We reuse the existing run_clustering function but need to handle the return
        # slightly differently to be more compact if needed, but for now full storage.
        
        # Run clustering for this specific mpts
        try:
            cluster_result = run_clustering(df, min_cluster_size=mpts, min_samples=mpts, metric=metric)
            results[str(mpts)] = cluster_result
        except Exception as e:
            print(f"Skipping mpts={mpts}: {str(e)}")
            continue

        
    return results

from .hai import compute_hai_matrix, run_meta_clustering, compute_medoids

def analyze_batch_results(batch_results):
    """
    Performs meta-analysis on batch results:
    1. Computes HAI Matrix
    2. Runs Meta-Clustering
    3. Identifies Medoids
    """
    # Extract Linkage Z matrices (convert back to numpy)
    # batch_results is a dict {mpts: result_dict}
    # Sort keys to ensure consistent matrix order
    sorted_keys = sorted(batch_results.keys(), key=lambda x: int(x))
    
    linkage_list = []
    n_samples = 0
    
    for key in sorted_keys:
        result = batch_results[key]
        if 'linkage_z' in result:
            Z = np.array(result['linkage_z'])
            linkage_list.append(Z)
            # Infer n_samples from linkage size (N-1 merges) => N = len(Z) + 1
            if n_samples == 0:
                n_samples = len(Z) + 1
        else:
            # Handle error/missing data?
            print(f"Warning: No linkage_z for mpts={key}")
            pass
            
    if not linkage_list:
        return {'error': 'No valid linkage matrices found'}
        
    # Compute HAI Matrix
    hai_matrix = compute_hai_matrix(linkage_list, n_samples)
    
    # Meta-Clustering
    meta_labels, meta_linkage = run_meta_clustering(hai_matrix)
    
    # Generate Meta-Dendrogram (Plotly)
    import plotly.figure_factory as ff
    # We need to map leaf indices to our sorted mpts keys for the labels
    dendro_labels = [str(k) for k in sorted_keys]
    
    # ff.create_dendrogram expects data (X) to compute linkage, OR a custom linkage matrix.
    # However, ff.create_dendrogram with linkagefun is tricky if we already have Z.
    # It calculates Z internally usually.
    # Workaround: Use scipy.cluster.hierarchy.dendrogram to get coordinates or build manually?
    # Actually, ff.create_dendrogram HAS a linkagefun argument, but it expects a function that *returns* Z.
    # So we can pass lambda x: meta_linkage.
    # BUT, meta_linkage from HDBSCAN might have slightly different format or scikit-learn vs scipy differences.
    # HDBSCAN's single_linkage_tree_ is a standard linkage matrix (4 columns).
    
    try:
        # Note: ff.create_dendrogram computes dist matrix if X is passed. 
        # If we want to use OUR Z, we must trick it.
        # Function to return our Z
        get_z = lambda x: np.array(meta_linkage)
        
        # We pass dummy data of correct shape (N_samples, something) just to satisfy shape checks if any
        dummy_X = np.zeros((len(sorted_keys), 1))
        
        fig_meta_dendro = ff.create_dendrogram(dummy_X, linkagefun=get_z, labels=dendro_labels)
        fig_meta_dendro.update_layout(
            template='plotly_white',
            title='Meta-Clustering Dendrogram (Hierarchies)',
            xaxis_title='mpts Parameter',
            yaxis_title='Distance',
            margin=dict(l=20, r=20, t=40, b=50)
        )
        meta_dendro_json = fig_meta_dendro.to_json()
    except Exception as e:
        print(f"Error generating meta-dendrogram: {e}")
        meta_dendro_json = None
    
    # Medoids
    medoids_map = compute_medoids(hai_matrix, meta_labels)
    # medoids_map maps {label: index_in_sorted_keys}
    
    # Convert indices to mpts values for the frontend
    medoids_mpts = {}
    for label, idx in medoids_map.items():
        medoids_mpts[int(label)] = int(sorted_keys[idx])
        
    return {
        'hai_matrix': hai_matrix.tolist(),
        'meta_labels': meta_labels,
        'meta_dendrogram_json': meta_dendro_json,
        'medoids': medoids_mpts,
        'ordered_mpts': [int(k) for k in sorted_keys]
    }


