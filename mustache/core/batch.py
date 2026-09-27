# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
import time
from .clustering import run_clustering
from .validation import numeric_data, validate_metric, validate_range

def run_batch_clustering(df, min_mpts, max_mpts, step, metric='euclidean', algorithm='core-sg'):
    """
    Build each requested hierarchy, reusing CORE-SG support once per batch.
    Returns a dictionary where keys are mpts values and values are clustering results.
    """
    results = {}
    
    # Ensure numerical data
    validate_metric(algorithm, metric)
    data_np = numeric_data(df, metric)
    validate_range(min_mpts, max_mpts, step, len(data_np))
    
    n_iters = max(1, len(range(min_mpts, max_mpts + 1, step)))

    # For Core-SG: Build the support graph ONCE up to k_max = max_mpts (ICDE 2022)
    # Then extract each hierarchy for k <= k_max from that same support.
    core_model = None
    amortized_core_fit_time = 0.0
    if algorithm == 'core-sg':
        from core_sg import CoreSG
        t_core_start = time.perf_counter()
        core_model = CoreSG(metric=metric, p=2, no_noise=False)
        core_model.fit(data_np, k_max=int(max_mpts))
        amortized_core_fit_time = (time.perf_counter() - t_core_start) / n_iters

    # Loop through mpts range
    for mpts in range(min_mpts, max_mpts + 1, step):
        # Modern batch policy ties minimum cluster size to the density mpts.
        # The legacy form exposed these independently; see the scientific guide.
        
        # Run clustering for this specific mpts
        try:
            cluster_result = run_clustering(
                df, 
                min_cluster_size=mpts, 
                min_samples=mpts, 
                metric=metric, 
                algorithm=algorithm,
                core_model=core_model,
                precomputed_projection=None,
                extra_clustering_time=amortized_core_fit_time,
                compact=True,
            )
            results[str(mpts)] = cluster_result
        except Exception as e:
            raise RuntimeError(f"Batch failed at mpts={mpts}: {e}") from e

        
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
    if not sorted_keys:
        raise ValueError('No hierarchies are available for HAI analysis.')
    
    linkage_list = []
    n_samples = 0
    
    total_optics_time = 0.0
    total_clustering_time = 0.0
    total_reachability_time = 0.0
    
    for key in sorted_keys:
        result = batch_results[key]
        total_optics_time += result.get('optics_time', 0.0)
        total_clustering_time += result.get('clustering_time', 0.0)
        total_reachability_time += result.get('reachability_time', 0.0)
        
        if 'linkage_z' in result:
            Z = np.array(result['linkage_z'])
            linkage_list.append(Z)
            # Infer n_samples from linkage size (N-1 merges) => N = len(Z) + 1
            if n_samples == 0:
                n_samples = len(Z) + 1
            elif len(Z) + 1 != n_samples:
                raise ValueError('All HAI hierarchies must refer to the same samples.')
        else:
            raise ValueError(f'Missing hierarchy for mpts={key}; matrix ordering cannot be preserved.')
            
    if not linkage_list:
        return {'error': 'No valid linkage matrices found'}
        
    # 1. Compute HAI Matrix (Pairwise similarity computation)
    t_hai_start = time.time()
    hai_matrix, hai_metadata = compute_hai_matrix(
        linkage_list, n_samples, return_metadata=True
    )
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

        if len(dendro_labels) == 1:
            fig_meta_dendro = go.Figure(data=[go.Scatter(
                x=[5], y=[0], mode='markers+text', text=dendro_labels,
                textposition='bottom center', marker=dict(size=8, color='#2196F3'),
                hovertemplate='mpts %{text}<extra></extra>'
            )])
            fig_meta_dendro.update_layout(
                template='plotly_white', title='Meta-Hierarchy Dendrogram (single hierarchy)',
                xaxis=dict(visible=False), yaxis=dict(title='Distance (1 - HAI)', range=[0, 1]),
                margin=dict(l=50, r=20, t=50, b=60), hovermode=False
            )
            meta_dendro_json = fig_meta_dendro.to_json()
        else:
            # Get dendrogram coordinate layout from scipy (no rendering)
            ddict = sp_dendrogram(Z, labels=dendro_labels, no_plot=True)
        
            icoord = np.array(ddict['icoord'])
            dcoord = np.array(ddict['dcoord'])
            leaf_labels = ddict['ivl']
        
            # X-axis tick positions: scipy places leaves at 5, 15, 25, ... (10 apart)
            n_leaves = len(leaf_labels)
            tick_vals = [10 * i + 5 for i in range(n_leaves)]
            # U-shape endpoints are subtree centres, NOT outer leaf bounds.
            # Recover true membership from linkage children to avoid excluding
            # outer leaves when clicking an internal branch.
            positions = {int(leaf): tick_vals[i] for i, leaf in enumerate(ddict['leaves'])}
            members = {i: [int(sorted_keys[i])] for i in range(n_leaves)}
            branch_members = {}
            for i, row in enumerate(Z):
                left, right = int(row[0]), int(row[1])
                xs_pair = tuple(sorted((positions[left], positions[right])))
                members[n_leaves + i] = members[left] + members[right]
                positions[n_leaves + i] = sum(xs_pair) / 2
                branch_members[(xs_pair[0], xs_pair[1], float(row[2]))] = members[n_leaves + i]

            # Build one Scatter trace per branch (each row of icoord/dcoord is one U-shape)
            traces = []
            for branch_index, (xs, ys) in enumerate(zip(icoord.tolist(), dcoord.tolist())):
                branch_mpts = sorted(branch_members[(min(xs), max(xs), max(ys))])
                # Insert a point at the centre of the horizontal segment. Plotly
                # click events are point-based, so this makes the visible branch
                # reliably clickable without changing its geometry.
                clickable_xs = [xs[0], xs[1], (xs[1] + xs[2]) / 2, xs[2], xs[3]]
                clickable_ys = [ys[0], ys[1], ys[1], ys[2], ys[3]]
                traces.append(go.Scatter(
                    x=clickable_xs, y=clickable_ys, mode='lines+markers',
                    line=dict(color='#2196F3', width=5),
                    marker=dict(size=18, opacity=0),
                    hovertemplate=(
                        'Branch: mpts ' + ', '.join(map(str, branch_mpts)) +
                        '<br>Merge distance: %{y:.6f}<extra></extra>'
                    ),
                    meta={
                        'branch_id': branch_index,
                        'mpts_values': branch_mpts,
                        'merge_height': max(ys),
                    },
                    showlegend=False
                ))
        
            layout = go.Layout(
                template='plotly_white', title='Meta-Hierarchy Dendrogram',
                xaxis=dict(tickvals=tick_vals, ticktext=leaf_labels, title='mpts Parameter', showgrid=False, zeroline=False),
                yaxis=dict(title='Distance (1 - HAI)', showgrid=True, zeroline=True, rangemode='tozero'),
                margin=dict(l=50, r=20, t=50, b=60), hovermode=False
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
    outlier_mpts = [
        int(sorted_keys[index])
        for index, label in enumerate(meta_labels)
        if int(label) == -1
    ]
    
    # Identify algorithm used in batch
    algo_used = "HDBSCAN/Core-SG"
    for res in batch_results.values():
        if isinstance(res, dict) and 'algorithm' in res:
            algo_used = "Core-SG" if res['algorithm'] == 'core-sg' else "HDBSCAN"
            break

    # Format and display execution times report in the CLI
    print("\n" + "="*50)
    print("           MUSTACHE V2 TIMING PROFILE REPORT")
    print("="*50)
    print(f"1. Core Clustering Runs Time ({algo_used}): {total_clustering_time:.4f}s")
    print(f"2. Hierarchy Reachability Build Time:         {total_reachability_time:.4f}s")
    print(f"3. HAI Similarity Matrix Computation Time:      {hai_time:.4f}s")
    print(f"4. Meta-Clustering & Dendrogram Build Time:    {dendrogram_time:.4f}s")
    print(f"5. Medoids Selection Computation Time:          {medoids_time:.4f}s")
    print("="*50 + "\n")
        
    return {
        'hai_matrix': hai_matrix.tolist(),
        'hai_computation': hai_metadata,
        'meta_labels': meta_labels,
        'meta_linkage': meta_linkage.tolist() if isinstance(meta_linkage, np.ndarray) else meta_linkage,
        'meta_dendrogram_json': meta_dendro_json,
        'medoids': medoids_mpts,
        'outliers': outlier_mpts,
        'ordered_mpts': [int(k) for k in sorted_keys],
        'times': {
            'clustering_runs_time': round(total_clustering_time, 4),
            'optics_runs_time': round(total_optics_time, 4),
            'reachability_time': round(total_reachability_time, 4),
            'hai_time': round(hai_time, 4),
            'dendrogram_time': round(dendrogram_time, 4),
            'medoids_time': round(medoids_time, 4)
        }
    }


