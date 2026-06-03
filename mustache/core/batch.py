# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
import time
from .clustering import run_clustering
from scipy.cluster.hierarchy import linkage, dendrogram as sp_dendrogram
from scipy.spatial.distance import squareform
from sklearn.cluster import HDBSCAN

def run_batch_clustering(df, min_mpts, max_mpts, step, metric='euclidean', algorithm='core-sg'):
    """
    Runs HDBSCAN for a range of mpts values.
    Returns a dictionary where keys are mpts values and values are clustering results.
    """
    results = {}
    
    # Ensure numerical data
    data = df.select_dtypes(include=[np.number])
    data_np = data.to_numpy()
    
    # Precompute OPTICS once for the entire batch
    t_opt_start = time.time()
    from sklearn.cluster import OPTICS
    # Use min_mpts or default 5 for stable density layout
    optics_samples = max(min_mpts, 5)
    optics_model = OPTICS(min_samples=optics_samples, metric=metric)
    optics_model.fit(data_np)
    optics_time_total = time.time() - t_opt_start
    
    # Amortize timing for report clarity
    n_iters = max(1, len(range(min_mpts, max_mpts + 1, step)))
    amortized_optics_time = optics_time_total / n_iters
    precomputed_optics = (optics_model.reachability_, optics_model.ordering_, amortized_optics_time)
    
    # Loop through mpts range
    for mpts in range(min_mpts, max_mpts + 1, step):
        # We use mpts for both min_cluster_size and min_samples mimicking legacy behavior
        # where 'mpts' controlled the scale.
        
        # Run clustering for this specific mpts
        try:
            cluster_result = run_clustering(
                df, 
                min_cluster_size=mpts, 
                min_samples=mpts, 
                metric=metric, 
                algorithm=algorithm,
                precomputed_optics=precomputed_optics
            )
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
    
    total_optics_time = 0.0
    total_clustering_time = 0.0
    
    for key in sorted_keys:
        result = batch_results[key]
        total_optics_time += result.get('optics_time', 0.0)
        total_clustering_time += result.get('clustering_time', 0.0)
        
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
        
    # 1. Compute HAI Matrix (Pairwise similarity computation)
    t_hai_start = time.time()
    hai_matrix = compute_hai_matrix(linkage_list, n_samples)
    hai_time = time.time() - t_hai_start
    
    # 2. Meta-Clustering
    t_meta_start = time.time()
    meta_labels, meta_linkage = run_meta_clustering(hai_matrix)
    
    # 3. Generate Meta-Dendrogram (Plotly) using scipy dendrogram coordinates.
    import plotly.graph_objects as go
    from scipy.cluster.hierarchy import dendrogram as sp_dendrogram
    
    dendro_labels = [str(k) for k in sorted_keys]
    
    try:
        Z = np.array(meta_linkage)
        
        # Get dendrogram coordinate layout from scipy (no rendering)
        ddict = sp_dendrogram(Z, labels=dendro_labels, no_plot=True)
        
        icoord = np.array(ddict['icoord'])  # X-coords of each branch (N-1 x 4)
        dcoord = np.array(ddict['dcoord'])  # Y-coords (heights) of each branch (N-1 x 4)
        leaf_labels = ddict['ivl']           # Leaf labels in left-to-right order
        
        # Build one Scatter trace per branch (each row of icoord/dcoord is one U-shape)
        traces = []
        for xs, ys in zip(icoord.tolist(), dcoord.tolist()):
            traces.append(go.Scatter(
                x=xs,
                y=ys,
                mode='lines',
                line=dict(color='#2196F3', width=2),
                hoverinfo='skip',
                showlegend=False
            ))
        
        # X-axis tick positions: scipy places leaves at 5, 15, 25, ... (10 apart)
        n_leaves = len(leaf_labels)
        tick_vals = [10 * i + 5 for i in range(n_leaves)]
        
        layout = go.Layout(
            template='plotly_white',
            title='Meta-Clustering Dendrogram (Hierarchies)',
            xaxis=dict(
                tickvals=tick_vals,
                ticktext=leaf_labels,
                title='mpts Parameter',
                showgrid=False,
                zeroline=False
            ),
            yaxis=dict(
                title='Distance (1 - HAI)',
                showgrid=True,
                zeroline=True,
                rangemode='tozero'
            ),
            margin=dict(l=50, r=20, t=50, b=60),
            hovermode=False
        )
        
        fig_meta_dendro = go.Figure(data=traces, layout=layout)
        meta_dendro_json = fig_meta_dendro.to_json()
    except Exception as e:
        print(f"Error generating meta-dendrogram: {e}")
        import traceback; traceback.print_exc()
        meta_dendro_json = None
    dendrogram_time = time.time() - t_meta_start
    
    # 4. Medoids selection
    t_medoids_start = time.time()
    medoids_map = compute_medoids(hai_matrix, meta_labels)
    
    # Convert indices to mpts values for the frontend
    medoids_mpts = {}
    for label, idx in medoids_map.items():
        medoids_mpts[int(label)] = int(sorted_keys[idx])
    medoids_time = time.time() - t_medoids_start
    
    # Format and display execution times report in the CLI
    print("\n" + "="*50)
    print("           MUSTACHE V2 TIMING PROFILE REPORT")
    print("="*50)
    print(f"1. Core Clustering Runs Time (HDBSCAN/Core-SG): {total_clustering_time:.4f}s")
    print(f"2. Reachability Plots Runs Time (OPTICS):      {total_optics_time:.4f}s")
    print(f"3. HAI Similarity Matrix Computation Time:      {hai_time:.4f}s")
    print(f"4. Meta-Clustering & Dendrogram Build Time:    {dendrogram_time:.4f}s")
    print(f"5. Medoids Selection Computation Time:          {medoids_time:.4f}s")
    print("="*50 + "\n")
        
    return {
        'hai_matrix': hai_matrix.tolist(),
        'meta_labels': meta_labels,
        'meta_linkage': meta_linkage.tolist() if isinstance(meta_linkage, np.ndarray) else meta_linkage,
        'meta_dendrogram_json': meta_dendro_json,
        'medoids': medoids_mpts,
        'ordered_mpts': [int(k) for k in sorted_keys],
        'times': {
            'clustering_runs_time': round(total_clustering_time, 4),
            'optics_runs_time': round(total_optics_time, 4),
            'hai_time': round(hai_time, 4),
            'dendrogram_time': round(dendrogram_time, 4),
            'medoids_time': round(medoids_time, 4)
        }
    }


