import numpy as np
from sklearn.cluster import HDBSCAN
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import is_valid_linkage, linkage


def _sizes_at_density_levels(Z, n_samples):
    """Resolve arbitrary binary ordering of simultaneous (equal-height) merges.

    A density level produces one cluster even when SciPy serializes its merge
    as several binary nodes. All tied descendants inherit that cluster's size.
    This preserves HAI under alternative MST tie-breaking of the same levels.
    """
    Z = np.asarray(Z, dtype=float)
    sizes = np.ones(2 * n_samples - 1)
    for i, row in enumerate(Z):
        expected = sizes[int(row[0])] + sizes[int(row[1])]
        if row[3] != expected:
            raise ValueError('Linkage cluster cardinalities do not match their children.')
        sizes[n_samples + i] = expected
    for i in range(len(Z) - 1, -1, -1):
        for child in Z[i, :2].astype(int):
            if child >= n_samples and Z[child - n_samples, 2] == Z[i, 2]:
                sizes[child] = sizes[n_samples + i]
    return sizes

def build_distance_matrix(Z, n_samples):
    """
    Constructs the hierarchy distance matrix from the linkage matrix Z.
    D[i, j] = Size of the smallest cluster containing both i and j, normalized by n_samples.
    Z structure: [idx1, idx2, distance, sample_count]
    """
    D = np.zeros((n_samples, n_samples))
    level_sizes = _sizes_at_density_levels(Z, n_samples)
    
    # We need to track the members of each cluster.
    # Initial clusters are just the points themselves: 0..(n-1)
    cluster_members = {i: [i] for i in range(n_samples)}
    
    # Iterate through Z
    for i, row in enumerate(Z):
        # Index of the new cluster being formed
        new_cluster_idx = n_samples + i
        
        child1_idx = int(row[0])
        child2_idx = int(row[1])
        # row[3] is number of samples in the new cluster (size)
        cluster_size = level_sizes[new_cluster_idx]
        
        normalized_size = cluster_size / n_samples
        
        members1 = cluster_members[child1_idx]
        members2 = cluster_members[child2_idx]
        
        # Fill D for all pairs between members1 and members2
        m1 = np.array(members1)
        m2 = np.array(members2)
        
        D[np.ix_(m1, m2)] = normalized_size
        D[np.ix_(m2, m1)] = normalized_size
        
        # Merge members for the new cluster
        cluster_members[new_cluster_idx] = members1 + members2
        
        # Cleanup old keys to free memory
        del cluster_members[child1_idx]
        del cluster_members[child2_idx]
        
    # Set diagonal to 1/n (size of single point cluster)
    np.fill_diagonal(D, 1.0 / n_samples)
        
    return D

def compute_hai_score(D1, D2):
    """
    Computes HAI between two distance matrices.
    HAI = 1 - (total_diff / n^2)
    """
    n = D1.shape[0]
    diff = np.abs(D1 - D2)
    total_diff = np.sum(diff)
    return 1.0 - (total_diff / (n * n))


def _build_lca_index(Z, n_samples):
    """Build a binary-lifting index for LCA queries on a SciPy linkage tree."""
    node_count = 2 * n_samples - 1
    parent = np.full(node_count, -1, dtype=np.int64)
    children = np.full((node_count, 2), -1, dtype=np.int64)
    sizes = _sizes_at_density_levels(Z, n_samples)

    for merge_index, row in enumerate(np.asarray(Z)):
        node = n_samples + merge_index
        left, right = int(row[0]), int(row[1])
        children[node] = (left, right)
        parent[left] = node
        parent[right] = node

    root = node_count - 1
    parent[root] = root
    depth = np.zeros(node_count, dtype=np.int64)
    stack = [root]
    while stack:
        node = stack.pop()
        left, right = children[node]
        if left >= 0:
            depth[left] = depth[node] + 1
            depth[right] = depth[node] + 1
            stack.extend((left, right))

    levels = max(1, int(np.ceil(np.log2(max(2, node_count)))) + 1)
    ancestors = np.empty((levels, node_count), dtype=np.int64)
    ancestors[0] = parent
    for level in range(1, levels):
        ancestors[level] = ancestors[level - 1][ancestors[level - 1]]
    return ancestors, depth, sizes


def _sampled_hierarchy_values(Z, n_samples, left_points, right_points):
    """Return normalized LCA cluster sizes for a shared sample of point pairs."""
    ancestors, depth, sizes = _build_lca_index(Z, n_samples)
    left = np.asarray(left_points, dtype=np.int64).copy()
    right = np.asarray(right_points, dtype=np.int64).copy()

    swap = depth[left] < depth[right]
    left[swap], right[swap] = right[swap].copy(), left[swap].copy()
    depth_delta = depth[left] - depth[right]
    for level in range(ancestors.shape[0]):
        mask = ((depth_delta >> level) & 1).astype(bool)
        left[mask] = ancestors[level, left[mask]]

    different = left != right
    for level in range(ancestors.shape[0] - 1, -1, -1):
        move = different & (ancestors[level, left] != ancestors[level, right])
        left[move] = ancestors[level, left[move]]
        right[move] = ancestors[level, right[move]]

    lca = left.copy()
    lca[different] = ancestors[0, left[different]]
    return sizes[lca] / float(n_samples)


def compute_hai_matrix(
    linkage_list,
    n_samples,
    *,
    max_exact_samples=2000,
    sample_pairs=50000,
    random_state=42,
    return_metadata=False,
):
    """
    HAI = 1 - 2/n² * sum(i<j) |d_H1(i,j) - d_H2(i,j)|.

    d_H is the normalized size of the lowest common ancestor cluster. This is
    the formula in legacy/resources/hai.pyx, not TED or a label validation score.
    Inputs describe full single-linkage trees over the SAME indexed samples;
    agreement on a legacy compact/pruned tree can differ (see user guide).
    """
    n_hierarchies = len(linkage_list)
    if n_samples < 1 or not n_hierarchies:
        raise ValueError('HAI requires at least one hierarchy and one sample.')
    if sample_pairs < 1 or max_exact_samples < 1:
        raise ValueError('HAI pair budget and exact threshold must be positive.')
    for Z in linkage_list:
        array = np.asarray(Z, dtype=float)
        if array.size and (not np.isfinite(array).all() or np.any(array[:, :2] != np.floor(array[:, :2]))):
            raise ValueError('HAI linkage must have finite values and integer node indices.')
        if n_samples > 1:
            is_valid_linkage(array, throw=True)
        if len(Z) != n_samples - 1:
            raise ValueError('HAI linkage sizes must match n_samples.')
        _sizes_at_density_levels(Z, n_samples)
    hai_matrix = np.zeros((n_hierarchies, n_hierarchies))
    
    use_approximation = n_samples > max_exact_samples

    if use_approximation:
        pair_count = max(1, int(sample_pairs))
        rng = np.random.default_rng(random_state)
        left_points = rng.integers(0, n_samples, size=pair_count, dtype=np.int64)
        right_points = rng.integers(0, n_samples - 1, size=pair_count, dtype=np.int64)
        right_points += right_points >= left_points
        hierarchy_values = [
            _sampled_hierarchy_values(Z, n_samples, left_points, right_points)
            for Z in linkage_list
        ]
        normalization = (n_samples - 1) / n_samples
        # Hoeffding bound for a bounded [0, 1] mean, confidence 95%.
        error_bound = normalization * np.sqrt(np.log(40.0) / (2.0 * pair_count))
        method = 'sampled-pairs'
    else:
        triangle = np.triu_indices(n_samples, k=1)
        hierarchy_values = [
            build_distance_matrix(Z, n_samples)[triangle]
            for Z in linkage_list
        ]
        normalization = 2.0 / (n_samples * n_samples)
        pair_count = n_samples * (n_samples - 1) // 2
        error_bound = 0.0
        method = 'exact-condensed'
    
    for i in range(n_hierarchies):
        for j in range(i, n_hierarchies):
            if i == j:
                score = 1.0
            else:
                if use_approximation:
                    score = 1.0 - normalization * float(
                        np.mean(np.abs(hierarchy_values[i] - hierarchy_values[j]))
                    )
                else:
                    score = 1.0 - normalization * float(
                        np.sum(np.abs(hierarchy_values[i] - hierarchy_values[j]), dtype=np.float64)
                    )
            
            hai_matrix[i, j] = np.clip(score, 0.0, 1.0)
            hai_matrix[j, i] = hai_matrix[i, j]
            
    metadata = {
        'method': method,
        'approximate': use_approximation,
        'n_samples': int(n_samples),
        'pair_count': int(pair_count),
        'random_state': int(random_state) if use_approximation else None,
        'confidence': 0.95 if use_approximation else 1.0,
        'absolute_error_bound': float(error_bound),
        'error_bound_scope': 'per hierarchy comparison; not simultaneous over the matrix',
        'sampling': 'uniform ordered distinct pairs with replacement; shared across hierarchies' if use_approximation else None,
        'bit_generator': 'PCG64' if use_approximation else None,
        'normalization': '2/n^2 sum over unordered pairs',
        'hierarchy_representation': 'full-single-linkage',
        'tie_policy': 'simultaneous equal-height merges form one density-level cluster',
        'max_exact_samples': int(max_exact_samples),
    }
    return (hai_matrix, metadata) if return_metadata else hai_matrix

def run_meta_clustering(hai_matrix):
    """
    Runs HDBSCAN on the HAI matrix (converted to distance).
    Returns labels and a linkage matrix (manually computed via scipy).
    """
    hai_matrix = np.asarray(hai_matrix, dtype=float)
    if hai_matrix.ndim != 2 or hai_matrix.shape[0] != hai_matrix.shape[1] or not len(hai_matrix):
        raise ValueError('HAI must be a non-empty square matrix.')
    if not np.isfinite(hai_matrix).all() or not np.allclose(hai_matrix, hai_matrix.T) or not np.allclose(np.diag(hai_matrix), 1) or np.any((hai_matrix < 0) | (hai_matrix > 1)):
        raise ValueError('HAI must be finite, symmetric, in [0, 1], with unit diagonal.')
    if len(hai_matrix) == 1:
        return [0], []

    distance_matrix = 1.0 - hai_matrix
    distance_matrix[distance_matrix < 0] = 0
    np.fill_diagonal(distance_matrix, 0)
    
    # Run HDBSCAN for labels (using sklearn version)
    # Legacy run_hdbscan_hai uses mpts=1: no additional density smoothing
    # of 1-HAI. sklearn counts self, so min_samples=1 induces single linkage.
    clusterer = HDBSCAN(metric='precomputed', min_samples=1, min_cluster_size=2, allow_single_cluster=True, copy=True)
    clusterer.fit(distance_matrix)
    labels = clusterer.labels_
    
    # Generate Linkage Matrix for Dendrogram using scipy (Hybrid Approach)
    # This replaces the missing single_linkage_tree_ attribute in sklearn 1.3
    condensed_dist = squareform(distance_matrix, checks=False)

    linkage_matrix = linkage(condensed_dist, method='single')
    
    return labels.tolist(), linkage_matrix.tolist()


def compute_medoids(hai_matrix, labels):
    """
    Minimize sum(1 - HAI) within each non-noise meta-cluster.
    Ties select the first index (ordered_mpts is sorted in batch analysis).
    """
    hai_matrix = np.asarray(hai_matrix, dtype=float)
    if hai_matrix.shape != (len(labels), len(labels)):
        raise ValueError('Meta labels must align with the square HAI matrix.')
    distance_matrix = 1.0 - hai_matrix
    unique_labels = np.unique(labels)
    medoids = {}
    
    for label in unique_labels:
        if label == -1:
            continue
            
        indices = np.where(np.array(labels) == label)[0]
        if len(indices) == 0:
            continue
            
        sub_matrix = distance_matrix[np.ix_(indices, indices)]
        total_distances = np.sum(sub_matrix, axis=0)
        min_idx = np.argmin(total_distances)
        medoids[int(label)] = int(indices[min_idx])
        
    return medoids
