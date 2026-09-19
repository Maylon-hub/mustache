"""
test_clustering.py — Unit tests for the HDBSCAN and Core-SG clustering engines.

Tests validate:
  - Output label array has the correct shape (N,)
  - Linkage matrix Z has shape (N-1, 4) and monotonically non-decreasing distances
  - Number of clusters is within a reasonable range
  - ARI/AMI metrics are computed when true labels are provided
  - 'algorithm' field matches the requested algorithm
"""
import pytest
import numpy as np
import pandas as pd
from mustache.core.clustering import run_clustering


def _df_from_array(X: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(X, columns=[f"f{i}" for i in range(X.shape[1])])


class TestHDBSCANClustering:
    def test_labels_shape(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=5, algorithm='hdbscan')
        labels = np.array(result['labels'])
        assert labels.shape == (X.shape[0],), "Labels must have one entry per sample"

    def test_linkage_shape(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=5, algorithm='hdbscan')
        Z = np.array(result['linkage_z'])
        N = X.shape[0]
        assert Z.shape == (N - 1, 4), f"Z must have shape ({N - 1}, 4), got {Z.shape}"

    def test_linkage_monotone(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=5, algorithm='hdbscan')
        Z = np.array(result['linkage_z'])
        distances = Z[:, 2]
        assert np.all(np.diff(distances) >= -1e-10), "Linkage distances must be monotonically non-decreasing"

    def test_cluster_count(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=5, algorithm='hdbscan')
        # blobs_100 has 4 centers; expect at least 1 cluster
        assert result['n_clusters'] >= 1

    def test_algorithm_field(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=5, algorithm='hdbscan')
        assert result['algorithm'] == 'hdbscan'

    def test_ari_ami_with_true_labels(self, blobs_100):
        X, y = blobs_100
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=5, algorithm='hdbscan', true_labels=y)
        assert 'ARI' in result['metrics'], "ARI must be computed when true_labels are provided"
        assert 'AMI' in result['metrics'], "AMI must be computed when true_labels are provided"
        assert -1.0 <= result['metrics']['ARI'] <= 1.0
        assert -1.0 <= result['metrics']['AMI'] <= 1.0

    def test_probabilities_shape(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=5, algorithm='hdbscan')
        probs = np.array(result['probabilities'])
        assert probs.shape == (X.shape[0],)
        assert np.all((probs >= 0) & (probs <= 1)), "Probabilities must be in [0, 1]"

    def test_noise_count_non_negative(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=5, algorithm='hdbscan')
        assert result['noise_points'] >= 0


class TestHDBSCANWithMoons:
    """Tests on non-convex moon dataset to ensure algorithm handles arbitrary shapes."""

    def test_labels_shape(self, moons_150):
        X, _ = moons_150
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=10, algorithm='hdbscan')
        assert len(result['labels']) == X.shape[0]

    def test_finds_clusters(self, moons_150):
        X, _ = moons_150
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=10, algorithm='hdbscan')
        assert result['n_clusters'] >= 1


class TestResultStructure:
    """Tests that verify the return dict has all required keys."""

    REQUIRED_KEYS = {
        'labels', 'probabilities', 'n_clusters', 'noise_points',
        'dendrogram_json', 'reachability_json', 'map_json',
        'metrics', 'linkage_z', 'clustering_time', 'algorithm'
    }

    def test_all_keys_present(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=5, algorithm='hdbscan')
        for key in self.REQUIRED_KEYS:
            assert key in result, f"Missing key in result: '{key}'"

    def test_json_fields_are_strings(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        result = run_clustering(df, min_cluster_size=5, algorithm='hdbscan')
        for json_key in ('dendrogram_json', 'reachability_json', 'map_json'):
            assert isinstance(result[json_key], str), f"'{json_key}' must be a JSON string"
