"""Shared, deliberately bounded end-to-end metric and input contract."""
import numpy as np

# Minkowski is explicitly p=2 in this public API; arbitrary p is not exposed.
# Cosine is a dissimilarity, supported through HDBSCAN's generic path. Angular,
# Pearson and precomputed matrices have no end-to-end contract in the CSV UI.
SUPPORTED_METRICS = {
    "core-sg": ("euclidean", "manhattan", "chebyshev", "minkowski", "cosine"),
    "hdbscan": ("euclidean", "manhattan", "chebyshev", "minkowski", "cosine"),
}


def validate_metric(algorithm, metric):
    if algorithm not in SUPPORTED_METRICS:
        raise ValueError("Algorithm must be 'core-sg' or 'hdbscan'.")
    if metric not in SUPPORTED_METRICS[algorithm]:
        choices = ", ".join(SUPPORTED_METRICS[algorithm])
        raise ValueError(f"Distance metric '{metric}' is not supported for {algorithm}. Choose: {choices}.")


def numeric_data(df, metric="euclidean"):
    data = df.select_dtypes(include=[np.number]).to_numpy(dtype=np.float64)
    if data.ndim != 2 or data.shape[1] == 0 or len(data) < 3:
        raise ValueError("Provide at least three samples and one numeric feature.")
    if not np.isfinite(data).all():
        raise ValueError("Numeric features contain missing or infinite values. Clean the dataset first.")
    if metric == "cosine" and np.any(np.linalg.norm(data, axis=1) == 0):
        raise ValueError("Cosine distance is undefined for zero vectors. Remove or transform zero-valued rows.")
    return data


def validate_range(min_mpts, max_mpts, step, n_samples):
    if min_mpts < 2 or max_mpts < min_mpts or max_mpts >= n_samples or step < 1:
        raise ValueError(f"Require 2 <= minimum mpts <= maximum mpts < {n_samples} samples, and step size >= 1.")
