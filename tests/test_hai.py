"""
test_hai.py — Mathematical unit tests for the HAI (Hierarchy Agreement Index) module.

Tests validate the mathematical properties documented in the MustaCHE paper:
  - HAI score must be in [0, 1]
  - HAI(H, H) = 1.0 (perfect self-similarity)
  - HAI matrix is strictly symmetric: H[i,j] == H[j,i]
  - Distance matrix diagonal must be 1/n (single-point cluster normalized size)
  - Medoid identification returns valid indices within cluster membership
"""
import pytest
import numpy as np
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import pdist

from mustache.core.hai import (
    build_distance_matrix,
    compute_hai_score,
    compute_hai_matrix,
    run_meta_clustering,
    compute_medoids,
)


def _make_linkage(X: np.ndarray) -> np.ndarray:
    """Creates a single-linkage matrix from raw data using Euclidean distance."""
    condensed = pdist(X, metric='euclidean')
    return linkage(condensed, method='single')


class TestBuildDistanceMatrix:
    def test_output_shape(self, blobs_100):
        X, _ = blobs_100
        Z = _make_linkage(X)
        D = build_distance_matrix(Z, X.shape[0])
        assert D.shape == (X.shape[0], X.shape[0])

    def test_diagonal_value(self, blobs_100):
        X, _ = blobs_100
        N = X.shape[0]
        Z = _make_linkage(X)
        D = build_distance_matrix(Z, N)
        expected_diag = 1.0 / N
        np.testing.assert_allclose(np.diag(D), expected_diag, atol=1e-10,
            err_msg=f"Diagonal must be 1/N = {expected_diag:.6f}")

    def test_symmetry(self, blobs_100):
        X, _ = blobs_100
        Z = _make_linkage(X)
        D = build_distance_matrix(Z, X.shape[0])
        np.testing.assert_allclose(D, D.T, atol=1e-10,
            err_msg="Distance matrix must be symmetric")

    def test_values_in_range(self, blobs_100):
        X, _ = blobs_100
        Z = _make_linkage(X)
        D = build_distance_matrix(Z, X.shape[0])
        assert np.all(D >= 0), "All distance matrix values must be >= 0"
        assert np.all(D <= 1.0 + 1e-10), "All distance matrix values must be <= 1"


class TestComputeHAIScore:
    def test_self_similarity_is_one(self, blobs_100):
        X, _ = blobs_100
        Z = _make_linkage(X)
        D = build_distance_matrix(Z, X.shape[0])
        score = compute_hai_score(D, D)
        assert abs(score - 1.0) < 1e-10, f"HAI(H, H) must equal 1.0, got {score}"

    def test_symmetry(self, blobs_100, blobs_200):
        X1, _ = blobs_100
        X2, _ = blobs_200
        # Use same number of samples for both
        N = min(X1.shape[0], X2.shape[0])
        X1, X2 = X1[:N], X2[:N]
        Z1 = _make_linkage(X1)
        Z2 = _make_linkage(X2)
        D1 = build_distance_matrix(Z1, N)
        D2 = build_distance_matrix(Z2, N)
        score_12 = compute_hai_score(D1, D2)
        score_21 = compute_hai_score(D2, D1)
        assert abs(score_12 - score_21) < 1e-10, \
            f"HAI must be symmetric: HAI(H1,H2)={score_12} != HAI(H2,H1)={score_21}"

    def test_score_in_range(self, blobs_100, blobs_200):
        X1, _ = blobs_100
        X2, _ = blobs_200
        N = min(X1.shape[0], X2.shape[0])
        X1, X2 = X1[:N], X2[:N]
        Z1 = _make_linkage(X1)
        Z2 = _make_linkage(X2)
        D1 = build_distance_matrix(Z1, N)
        D2 = build_distance_matrix(Z2, N)
        score = compute_hai_score(D1, D2)
        assert 0.0 - 1e-10 <= score <= 1.0 + 1e-10, f"HAI score must be in [0,1], got {score}"


class TestComputeHAIMatrix:
    def test_matrix_is_square(self, blobs_100):
        X, _ = blobs_100
        Z = _make_linkage(X)
        K = 4  # number of fake hierarchies
        linkage_list = [Z for _ in range(K)]
        H = compute_hai_matrix(linkage_list, X.shape[0])
        assert H.shape == (K, K)

    def test_matrix_diagonal_is_one(self, blobs_100):
        X, _ = blobs_100
        Z = _make_linkage(X)
        K = 4
        linkage_list = [Z for _ in range(K)]
        H = compute_hai_matrix(linkage_list, X.shape[0])
        np.testing.assert_allclose(np.diag(H), 1.0, atol=1e-10)

    def test_matrix_is_symmetric(self, blobs_100):
        X, _ = blobs_100
        Z = _make_linkage(X)
        K = 4
        linkage_list = [Z for _ in range(K)]
        H = compute_hai_matrix(linkage_list, X.shape[0])
        np.testing.assert_allclose(H, H.T, atol=1e-10)

    def test_matrix_values_in_range(self, blobs_100):
        X, _ = blobs_100
        Z = _make_linkage(X)
        K = 4
        linkage_list = [Z for _ in range(K)]
        H = compute_hai_matrix(linkage_list, X.shape[0])
        assert np.all((H >= 0 - 1e-10) & (H <= 1 + 1e-10))


class TestComputeMedoids:
    def test_medoid_per_cluster(self):
        """Each non-noise label must have exactly one medoid."""
        # Create a simple 4x4 HAI matrix (4 mpts, 2 meta-clusters)
        hai = np.array([
            [1.0, 0.9, 0.1, 0.1],
            [0.9, 1.0, 0.1, 0.1],
            [0.1, 0.1, 1.0, 0.9],
            [0.1, 0.1, 0.9, 1.0],
        ])
        labels = np.array([0, 0, 1, 1])
        medoids = compute_medoids(hai, labels)
        assert set(medoids.keys()) == {0, 1}, f"Expected medoid keys {{0,1}}, got {set(medoids.keys())}"

    def test_medoid_index_within_cluster(self):
        """Medoid index must correspond to a point in the cluster."""
        hai = np.array([
            [1.0, 0.9, 0.1, 0.1],
            [0.9, 1.0, 0.1, 0.1],
            [0.1, 0.1, 1.0, 0.9],
            [0.1, 0.1, 0.9, 1.0],
        ])
        labels = np.array([0, 0, 1, 1])
        medoids = compute_medoids(hai, labels)
        # Cluster 0 contains indices {0,1}, cluster 1 contains {2,3}
        assert medoids[0] in {0, 1}, f"Medoid of cluster 0 must be in {{0,1}}, got {medoids[0]}"
        assert medoids[1] in {2, 3}, f"Medoid of cluster 1 must be in {{2,3}}, got {medoids[1]}"

    def test_noise_label_excluded(self):
        """Noise points (label=-1) must not appear in medoids dict."""
        hai = np.eye(4)
        labels = np.array([-1, 0, 0, 1])
        medoids = compute_medoids(hai, labels)
        assert -1 not in medoids, "Noise label (-1) must not appear in medoids"
