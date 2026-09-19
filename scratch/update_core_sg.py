import sys
from pathlib import Path
import numpy as np

filePath = r"C:\Users\guest\Documents\GitHub\core-sg\core_sg\core_sg.py"
with open(filePath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update build_core_sg_from_data
target_old = """    # ---- pairwise distances dentro da função ----
    if metric == "minkowski":
        D = pairwise_distances(X, metric=metric, p=p)
    elif metric == "arccos":
        D = pairwise_distances(X, metric="cosine")
    else:
        D = pairwise_distances(X, metric=metric)

    D = np.ascontiguousarray(D, dtype=pairwise_dtype)
    np.fill_diagonal(D, 0.0)

    if _round_distances:
        D = D.round(4)

    # ------------------------------------------------------------------
    # Separação correta dos papéis:
    # - min_samples_k: parâmetro do HDBSCAN
    # - graph_knn_k: número de vizinhos no kNN graph do Core-SG
    # - core_k: core-distance compatível com HDBSCAN
    # ------------------------------------------------------------------
    min_samples_k = k_max
    graph_knn_k = min_samples_k

    # kNN graph do Core-SG usa k original
    idxs_graph, dists_graph = knn_from_precomputed(
        D,
        k=graph_knn_k,
        include_self=False,
    )

    metric_edges, knng_to_insert = build_knng_vectors(
        idxs_graph,
        dists_graph,
        knng_size=n,
        k_max=graph_knn_k,
    )

    # min_samples conta o próprio ponto, então com diagonal 0
    # o índice correto é min_samples_k - 1
    # core_k = np.partition(D, kth=min_samples_k - 1, axis=1)[:, min_samples_k - 1]
    # core_k = np.ascontiguousarray(core_k, dtype=np.float64)

    core_k_list = np.partition(D, kth=min_samples_k - 1, axis=1)[:, :min_samples_k]
    core_k_list = np.sort(core_k_list, axis=1)

    # MST da mutual reachability com k_max
    hdb_obj, mst_orig = reference_mst_original_distance(D, k_max=k_max)"""

target_new = """    min_samples_k = k_max
    graph_knn_k = min_samples_k

    if metric == "euclidean" and n <= 10000 and X.ndim == 2 and X.shape[1] <= 15:
        from scipy.spatial import cKDTree
        tree = cKDTree(X)
        dists_all, idxs_all = tree.query(X, k=k_max + 1)
        idxs_graph = idxs_all[:, 1:].astype(np.int64)
        dists_graph = dists_all[:, 1:].astype(np.float64)
        core_k_list = dists_graph[:, :k_max]

        metric_edges, knng_to_insert = build_knng_vectors(
            idxs_graph,
            dists_graph,
            knng_size=n,
            k_max=graph_knn_k,
        )

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=k_max,
            min_samples=k_max,
            metric="euclidean",
            core_dist_n_jobs=1,
        )
        clusterer.fit(X)
        hdb_obj = clusterer
        mst_orig = np.asarray(clusterer._min_spanning_tree, dtype=np.float64)
        D = np.zeros((n, n), dtype=np.float64)
    else:
        if metric == "minkowski":
            D = pairwise_distances(X, metric=metric, p=p)
        elif metric == "arccos":
            D = pairwise_distances(X, metric="cosine")
        else:
            D = pairwise_distances(X, metric=metric)

        D = np.ascontiguousarray(D, dtype=pairwise_dtype)
        np.fill_diagonal(D, 0.0)

        if _round_distances:
            D = D.round(4)

        idxs_graph, dists_graph = knn_from_precomputed(
            D,
            k=graph_knn_k,
            include_self=False,
        )

        metric_edges, knng_to_insert = build_knng_vectors(
            idxs_graph,
            dists_graph,
            knng_size=n,
            k_max=graph_knn_k,
        )

        core_k_list = np.partition(D, kth=min_samples_k - 1, axis=1)[:, :min_samples_k]
        core_k_list = np.sort(core_k_list, axis=1)

        hdb_obj, mst_orig = reference_mst_original_distance(D, k_max=k_max)"""

# 2. Update mst_from_core_sg
mst_old = """    t0 = time()
    core_k = core_k_list[:, k - 1]
    core_k = np.ascontiguousarray(core_k, dtype=np.float64)
    weighted = reweight_core_sg_mutual_reachability(
        core_sg=core_sg,
        core_k=core_k,
        metric_edges=metric_edges,
        n_nodes=n_nodes,
    )"""

mst_new = """    n_mst_edges = n_nodes - 1
    n_knng_total = core_sg.shape[0] - n_mst_edges
    k_max_total = n_knng_total // n_nodes

    if k < k_max_total and n_knng_total == n_nodes * k_max_total:
        knng_part = core_sg[:n_knng_total].reshape(n_nodes, k_max_total, 3)[:, :k, :].reshape(-1, 3)
        mst_part = core_sg[n_knng_total:]
        active_core_sg = np.vstack([knng_part, mst_part])
    else:
        active_core_sg = core_sg

    t0 = time()
    core_k = core_k_list[:, k - 1]
    core_k = np.ascontiguousarray(core_k, dtype=np.float64)
    weighted = reweight_core_sg_mutual_reachability(
        core_sg=active_core_sg,
        core_k=core_k,
        metric_edges=metric_edges,
        n_nodes=n_nodes,
    )"""

assert target_old in content, "target_old not found"
assert mst_old in content, "mst_old not found"

content = content.replace(target_old, target_new).replace(mst_old, mst_new)

with open(filePath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated core_sg.py!")