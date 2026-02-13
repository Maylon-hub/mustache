from sklearn.cluster import HDBSCAN


import pandas as pd
import numpy as np
from sklearn.metrics import adjusted_rand_score, adjusted_mutual_info_score
from sklearn.neighbors import NearestNeighbors
from scipy.spatial.distance import pdist, squareform


def compute_mutual_reachability(data, min_samples, metric='euclidean'):
    """
    Computes the Mutual Reachability Distance matrix for HDBSCAN.
    d_mreach(a, b) = max(core_k(a), core_k(b), d(a, b))
    """
    n_samples = data.shape[0]
    k = min(min_samples, n_samples)
    
    # Compute Core Distances (distance to k-th nearest neighbor)
    nbrs = NearestNeighbors(n_neighbors=k, metric=metric).fit(data)
    core_distances, _ = nbrs.kneighbors(data)
    core_dist = core_distances[:, -1]
    
    # Compute basic Distance Matrix
    if metric == 'euclidean':
        raw_dist = squareform(pdist(data))
    else:
        raw_dist = squareform(pdist(data, metric=metric))
        
    # Vectorized Mutual Reachability
    # MR[i,j] = max(core[i], core[j], dist[i,j])
    
    # Expand core distances to matrix for broadcasting
    # core_mat[i, j] = core_dist[i]
    core_mat = np.tile(core_dist, (n_samples, 1))
    
    # Symmetric max of cores: max(core[i], core[j])
    # max_core[i, j] = max(core[i], core[j])
    max_core = np.maximum(core_mat, core_mat.T)
    
    # Final MR
    mreach_mat = np.maximum(max_core, raw_dist)
    
    # Ensure diagonal is exactly zero (fix for floating point errors)
    np.fill_diagonal(mreach_mat, 0)
    
    return mreach_mat





def run_clustering(df, min_cluster_size=5, min_samples=None, metric='euclidean', true_labels=None):

    """
    Runs HDBSCAN clustering on the provided DataFrame using scikit-learn.
    Returns a dictionary with results.
    """
    # Convert DataFrame to numpy array
    data = df.select_dtypes(include=[np.number]).to_numpy()
    
    if data.size == 0 or data.shape[1] == 0:
        raise ValueError("No numerical data found for clustering. Please ensure the CSV contains numeric columns.")
    
    clusterer = HDBSCAN(
        min_cluster_size=int(min_cluster_size),
        min_samples=int(min_samples) if min_samples else None,
        metric=metric,
        store_centers='medoid'
    )


    
    labels = clusterer.fit_predict(data)

    
    # Generate Linkage Matrix for Dendrogram (using scipy as proxy for visualization)
    from scipy.cluster.hierarchy import linkage, dendrogram
    import plotly.figure_factory as ff
    
    # Use 'single' linkage to mimic HDBSCAN's MST-based approach
    # FIX: Use Mutual Reachability Distance instead of Euclidean Distance
    # This ensures the hierarchy varies with min_samples (mpts)
    
    # MR Distance Matrix
    m_samples_val = int(min_samples) if min_samples else int(min_cluster_size)
    mreach_matrix = compute_mutual_reachability(data, m_samples_val, metric)
    
    # Condense for linkage (scipy expects condensed distance array)
    condensed_mreach = squareform(mreach_matrix, checks=False)

    
    Z = linkage(condensed_mreach, method='single')


    
    # Create Dendrogram Figure
    fig_dendro = ff.create_dendrogram(data, linkagefun=lambda x: Z)
    fig_dendro.update_layout(
        template='plotly_white',
        title='Hierarchical Clustering Dendrogram',
        xaxis_title='Sample Index',
        yaxis_title='Distance',
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # Generate Reachability Plot
    # HDBSCAN doesn't produce a reachability plot directly like OPTICS, 
    # but we can approximate a similar view using the single linkage tree (MST).
    # The 'Z' linkage matrix contains (cluster_1, cluster_2, distance, sample_count).
    # For a reachability plot, we typically want the distance to the nearest neighbor 
    # in the spanning tree, ordered by the traversal.
    
    # Simplified approach: Use the linkage distances directly for now, 
    # ordered by the dendrogram leaves.
    dendro_leaves = fig_dendro['layout']['xaxis']['ticktext']
    # Map leaf indices to original data indices
    ordered_indices = [int(i) for i in dendro_leaves]
    
    # We need a reachability distance for each point. 
    # In single linkage, this is roughly the height at which the point merges.
    # This is a simplification; true reachability requires OPTICS or extracting from MST.
    # For HDBSCAN, the 'condensed_tree_' or 'single_linkage_tree_' is the source.
    
    # Let's use the single linkage tree from HDBSCAN if available, or our scipy Z.
    # Scipy Z: Z[i, 2] is the distance.
    
    # Constructing a basic reachability-like plot from Z:
    # This is complex to do perfectly without OPTICS, but we can plot the 
    # merge distances of the ordered points.
    
    import plotly.graph_objects as go
    
    # Placeholder for true reachability: Plot distances of ordered points
    # This is NOT a true reachability plot but gives a similar visual of density structure
    # for verification purposes.
    
    fig_reach = go.Figure()
    fig_reach.add_trace(go.Bar(
        x=list(range(len(ordered_indices))),
        y=[0] * len(ordered_indices), # Placeholder, need to calculate actual reachability
        marker_color='#097B43'
    ))
    
    # Better approach: Use HDBSCAN's single_linkage_tree_ if we switch back to hdbscan library,
    # but with sklearn's HDBSCAN, we might not have it exposed easily in the same way 
    # without 'gen_min_span_tree=True' which isn't in sklearn's version yet (it uses a different backend).
    
    # Alternative: Use OPTICS from sklearn for the reachability plot specifically, 
    # as it's the standard for that visualization.
    from sklearn.cluster import OPTICS
    optics = OPTICS(min_samples=int(min_samples) if min_samples else 5, metric=metric)
    optics.fit(data)

    
    reachability = optics.reachability_[optics.ordering_]
    labels_optics = optics.labels_[optics.ordering_]
    
    # Use HDBSCAN labels for coloring instead of OPTICS labels for consistency
    ordered_hdbscan_labels = labels[optics.ordering_]
    
    fig_reach = go.Figure()
    fig_reach.add_trace(go.Bar(
        x=list(range(len(reachability))),
        y=reachability,
        marker=dict(
            color=ordered_hdbscan_labels,  # Color by HDBSCAN clusters
            colorscale='Viridis', 
            line=dict(width=0),
            showscale=True,
            colorbar=dict(title="Cluster")
        ),
        name='Reachability Distance',
        hovertemplate='<b>Point %{x}</b><br>Distance: %{y:.3f}<br>Cluster: %{marker.color}<extra></extra>'
    ))
    fig_reach.update_layout(
        template='plotly_white',
        title='Reachability Plot',
        xaxis_title='Sample Index (Ordered)',
        yaxis_title='Reachability Distance',
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )

    # Generate 2D Projection (t-SNE)
    from sklearn.manifold import TSNE
    
    # Use t-SNE to project data to 2D
    # Perplexity should be less than number of samples. Default is 30.
    n_samples = data.shape[0]
    perplexity = min(30, n_samples - 1) if n_samples > 1 else 1
    
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42)
    projection = tsne.fit_transform(data)

    
    fig_map = go.Figure()
    fig_map.add_trace(go.Scatter(
        x=projection[:, 0],
        y=projection[:, 1],
        mode='markers',
        marker=dict(
            size=8,
            color=labels, # Color by cluster label
            colorscale='Viridis',
            showscale=True,
            line=dict(width=1, color='DarkSlateGrey')
        ),
        text=[f"Cluster: {l}" for l in labels],
        hoverinfo='text'
    ))
    
    fig_map.update_layout(
        template='plotly_white',
        title='2D Projection (t-SNE)',
        xaxis_title='Dimension 1',
        yaxis_title='Dimension 2',
        margin=dict(l=20, r=20, t=40, b=20)
    )

    metrics = {}
    if true_labels is not None:
        # Filter out noise points (-1) from evaluation if desired, 
        # but standard ARI/AMI handles them as just another label.
        # However, it's often better to check alignment.
        
        # Ensure lengths match
        if len(true_labels) == len(labels):
            metrics['ARI'] = adjusted_rand_score(true_labels, labels)
            metrics['AMI'] = adjusted_mutual_info_score(true_labels, labels)
        else:
            metrics['error'] = "Label file length does not match data length."

    return {
        'labels': labels.tolist(),
        'probabilities': clusterer.probabilities_.tolist(),
        'n_clusters': int(labels.max() + 1),
        'noise_points': int((labels == -1).sum()),
        'dendrogram_json': fig_dendro.to_json(),
        'reachability_json': fig_reach.to_json(),
        'map_json': fig_map.to_json(),
        'metrics': metrics,
        'linkage_z': Z.tolist()
    }

