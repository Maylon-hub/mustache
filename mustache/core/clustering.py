"""Clustering and visualizations derived from the very same fitted hierarchy."""
import time
import warnings

import numpy as np
from scipy.cluster.hierarchy import dendrogram, is_valid_linkage
from sklearn.metrics import adjusted_rand_score, adjusted_mutual_info_score, pairwise_distances
from sklearn.neighbors import NearestNeighbors

from .validation import numeric_data, validate_metric


def compute_mutual_reachability(data, min_samples, metric='euclidean'):
    """Reference convention: mpts includes the query point itself."""
    kwargs = {'p': 2} if metric == 'minkowski' else {}
    neighbors = NearestNeighbors(n_neighbors=int(min_samples), metric=metric, **kwargs).fit(data)
    distances, _ = neighbors.kneighbors(data)
    core = distances[:, -1]
    raw = pairwise_distances(data, metric=metric, **kwargs)
    result = np.maximum(np.maximum(core[:, None], core[None, :]), raw)
    np.fill_diagonal(result, 0)
    return result


def hierarchy_reachability(Z, labels, *, mpts, metric):
    """Density contour: adjacent leaves separate at their LCA merge height.

    The legacy hierarchy loader overwrote each ordered cluster interval with
    its density level. Here the full single-linkage tree defines those intervals.
    This is a hierarchy-derived reachability view, not an OPTICS ordering or
    reachability estimate. Each mpts gets its own ordering and distances.
    """
    Z = np.asarray(Z, dtype=float)
    is_valid_linkage(Z, throw=True)
    n = len(Z) + 1
    order = np.asarray(dendrogram(Z, no_plot=True)['leaves'], dtype=int)
    positions = np.empty(n, dtype=int)
    positions[order] = np.arange(n)
    first = np.empty(2 * n - 1, dtype=int)
    last = np.empty_like(first)
    first[:n] = last[:n] = positions
    values = np.zeros(n, dtype=float)
    # In the dendrogram traversal each subtree is contiguous. The boundary
    # between its children is exactly one adjacent pair's LCA.
    for i, row in enumerate(Z):
        a, b = int(row[0]), int(row[1])
        first[n + i] = min(first[a], first[b])
        last[n + i] = max(last[a], last[b])
        values[max(first[a], first[b])] = row[2]
    # The first ordered point has no predecessor. Preserve that missing value
    # rather than inventing a finite distance for it (legacy used a ceiling).
    y = values.tolist()
    y[0] = None
    return {
        'x': list(range(n)), 'y': y, 'ordering': order.tolist(),
        'labels': np.asarray(labels)[order].tolist(),
        'method': 'hierarchy-adjacent-cophenetic', 'mpts': int(mpts),
        'metric': metric, 'first_point_undefined': True,
    }


def run_clustering(df, min_cluster_size=5, min_samples=None, metric='euclidean', algorithm='core-sg', true_labels=None, precomputed_optics=None, core_model=None, precomputed_projection=None, extra_clustering_time=0.0, compact=False):
    """Fit one hierarchy; batch callers may reuse a fitted CORE-SG support graph.

    precomputed_optics remains accepted for API compatibility, but is deprecated:
    an OPTICS layout does not represent this fitted hierarchy.
    """
    validate_metric(algorithm, metric)
    data = numeric_data(df, metric)
    minimum_size = int(min_cluster_size)
    mpts = minimum_size if min_samples is None else int(min_samples)
    if minimum_size < 2 or minimum_size > len(data) or mpts < 2 or mpts >= len(data):
        raise ValueError('Require minimum cluster size >= 2 and 2 <= mpts < number of samples.')
    if precomputed_optics is not None:
        warnings.warn('precomputed_optics is deprecated; reachability is derived from each hierarchy.', DeprecationWarning, stacklevel=2)
    if true_labels is not None and len(true_labels) != len(data):
        raise ValueError('Label file length does not match dataset length.')

    start = time.perf_counter()
    if algorithm == 'core-sg':
        from core_sg import CoreSG
        model = core_model
        if model is None:
            model = CoreSG(metric=metric, p=2, no_noise=False)
            model.fit(data, k_max=mpts)
        elif model.metric != metric or model.n_samples_ != len(data):
            raise ValueError('Pre-fitted CORE-SG data size or distance metric does not match this analysis.')
        model.extract_hierarchy_from_core_sg(k=mpts)
        Z = model.single_linkage_tree_.to_numpy().astype(float)
        # CORE-SG's cached k_max outputs and extraction defaults use different
        # minimum cluster sizes. Relabel the SAME tree explicitly for this mpts.
        # This is the narrow tested HDBSCAN adapter boundary (not another fit).
        from hdbscan.hdbscan_ import _tree_to_labels
        labels, probabilities = _tree_to_labels(
            data, Z, min_cluster_size=minimum_size + 1,
            match_reference_implementation=True,
        )[:2]
    else:
        import hdbscan
        kwargs = {'p': 2} if metric == 'minkowski' else {}
        model = hdbscan.HDBSCAN(
            min_cluster_size=minimum_size, min_samples=mpts, metric=metric,
            algorithm='generic' if metric == 'cosine' else 'best',
            match_reference_implementation=True, core_dist_n_jobs=1,
            approx_min_span_tree=False, **kwargs,
        ).fit(data)
        labels, probabilities = model.labels_, model.probabilities_
        # Use the fitted tree, not an independently reconstructed MRD hierarchy.
        Z = model.single_linkage_tree_.to_numpy().astype(float)
    elapsed = time.perf_counter() - start + extra_clustering_time
    labels, probabilities = np.asarray(labels), np.asarray(probabilities)
    start = time.perf_counter()
    reach = hierarchy_reachability(Z, labels, mpts=mpts, metric=metric)
    reach_time = time.perf_counter() - start

    fig_dendro = fig_reach = fig_map = None
    projection_method = None
    if not compact:
        import plotly.graph_objects as go
        dd = dendrogram(Z, no_plot=True)
        fig_dendro = go.Figure([
            go.Scatter(x=x, y=y, mode='lines', showlegend=False)
            for x, y in zip(dd['icoord'], dd['dcoord'])
        ])
        fig_dendro.update_layout(template='plotly_white', title='Clustering hierarchy', xaxis_title='Sample order', yaxis_title='Mutual reachability distance')
        fig_reach = go.Figure(go.Bar(x=reach['x'], y=reach['y'], customdata=reach['ordering'], marker_color='#1F6F5F', hovertemplate='Sample %{customdata}<br>Hierarchy distance: %{y:.6f}<extra></extra>'))
        fig_reach.update_layout(template='plotly_white', title=f'Hierarchy reachability: mpts = {mpts}', xaxis_title='Sample order', yaxis_title='Hierarchy reachability distance')
        projection = precomputed_projection
        projection_method = 'provided' if projection is not None else 't-SNE (Euclidean)'
        if projection is None:
            try:
                from sklearn.manifold import TSNE
                # Visualization only: Euclidean t-SNE does not define clusters,
                # HAI, representatives, or distances in the reachability plots.
                projection = TSNE(n_components=2, perplexity=min(30, max(1, len(data) // 3)), random_state=42, method='exact' if len(data) < 50 else 'barnes_hut', init='pca' if data.shape[1] >= 2 else 'random', metric='euclidean').fit_transform(data)
            except Exception as exc:
                warnings.warn(f't-SNE projection failed: {exc}. Displaying feature coordinates.', RuntimeWarning)
                projection = data[:, :2] if data.shape[1] >= 2 else np.column_stack((data[:, 0], np.zeros(len(data))))
                projection_method = 'feature coordinates'
        fig_map = go.Figure(go.Scatter(x=projection[:, 0], y=projection[:, 1], mode='markers', marker=dict(color=labels, colorscale='Viridis'), text=[f'Cluster: {label}' for label in labels]))
        fig_map.update_layout(template='plotly_white', title=f'2D visualization — {projection_method}', xaxis_title='Dimension 1', yaxis_title='Dimension 2')
    metrics = {} if true_labels is None else {
        'ARI': adjusted_rand_score(true_labels, labels),
        'AMI': adjusted_mutual_info_score(true_labels, labels),
    }
    return {
        'labels': labels.tolist(), 'probabilities': probabilities.tolist(),
        'n_clusters': len(set(labels.tolist()) - {-1}), 'noise_points': int((labels == -1).sum()),
        'dendrogram_json': fig_dendro.to_json() if fig_dendro else None,
        'reachability_json': fig_reach.to_json() if fig_reach else None,
        'reachability_data': reach, 'map_json': fig_map.to_json() if fig_map else None,
        'projection_method': projection_method, 'metrics': metrics, 'linkage_z': Z.tolist(),
        'optics_time': 0.0, 'reachability_time': reach_time,
        'clustering_time': elapsed, 'algorithm': algorithm, 'metric': metric,
        'mpts': mpts, 'min_cluster_size': minimum_size, 'n_samples': len(data),
        'hierarchy_representation': 'full-single-linkage',
    }
