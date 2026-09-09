"""
test_batch.py — Tests for the batch clustering pipeline and meta-analysis.

Tests validate:
  - run_batch_clustering returns a dict keyed by mpts values
  - Each result entry has the expected keys and correct label shape
  - analyze_batch_results returns valid HAI matrix, meta_linkage and medoids
"""
import pytest
import numpy as np
import pandas as pd
from mustache.core.batch import run_batch_clustering, analyze_batch_results


def _df_from_array(X: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(X, columns=[f"f{i}" for i in range(X.shape[1])])


class TestRunBatchClustering:
    """Tests on the batch run function itself."""

    def test_returns_dict(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        results = run_batch_clustering(df, min_mpts=5, max_mpts=10, step=5, algorithm='hdbscan')
        assert isinstance(results, dict), "run_batch_clustering must return a dict"

    def test_keys_match_mpts_range(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        results = run_batch_clustering(df, min_mpts=5, max_mpts=15, step=5, algorithm='hdbscan')
        expected_keys = {str(k) for k in range(5, 16, 5)}
        assert expected_keys.issubset(results.keys()), \
            f"Expected keys {expected_keys} not found in {set(results.keys())}"

    def test_each_result_has_labels(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        results = run_batch_clustering(df, min_mpts=5, max_mpts=10, step=5, algorithm='hdbscan')
        for mpts_key, result in results.items():
            labels = np.array(result['labels'])
            assert labels.shape == (X.shape[0],), \
                f"Labels for mpts={mpts_key} must have shape ({X.shape[0]},), got {labels.shape}"

    def test_each_result_has_linkage(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        results = run_batch_clustering(df, min_mpts=5, max_mpts=10, step=5, algorithm='hdbscan')
        N = X.shape[0]
        for mpts_key, result in results.items():
            Z = np.array(result['linkage_z'])
            assert Z.shape == (N - 1, 4), \
                f"Linkage for mpts={mpts_key} must have shape ({N-1}, 4), got {Z.shape}"

    def test_algorithm_field_matches(self, blobs_100):
        X, _ = blobs_100
        df = _df_from_array(X)
        results = run_batch_clustering(df, min_mpts=5, max_mpts=10, step=5, algorithm='hdbscan')
        for mpts_key, result in results.items():
            assert result['algorithm'] == 'hdbscan', \
                f"Algorithm field mismatch for mpts={mpts_key}"


class TestAnalyzeBatchResults:
    """Tests on the meta-analysis pipeline (HAI + meta-clustering)."""

    def _run_batch(self, X, step=5):
        df = _df_from_array(X)
        return run_batch_clustering(df, min_mpts=5, max_mpts=15, step=step, algorithm='hdbscan')

    def test_returns_dict(self, blobs_100):
        X, _ = blobs_100
        batch_results = self._run_batch(X)
        analysis = analyze_batch_results(batch_results)
        assert isinstance(analysis, dict)

    def test_hai_matrix_is_square(self, blobs_100):
        X, _ = blobs_100
        batch_results = self._run_batch(X)
        analysis = analyze_batch_results(batch_results)
        hai = np.array(analysis['hai_matrix'])
        assert hai.ndim == 2 and hai.shape[0] == hai.shape[1], \
            f"HAI matrix must be square, got shape {hai.shape}"

    def test_hai_matrix_symmetry(self, blobs_100):
        X, _ = blobs_100
        batch_results = self._run_batch(X)
        analysis = analyze_batch_results(batch_results)
        hai = np.array(analysis['hai_matrix'])
        np.testing.assert_allclose(hai, hai.T, atol=1e-10,
            err_msg="HAI matrix must be symmetric: H[i,j] == H[j,i]")

    def test_hai_diagonal_is_one(self, blobs_100):
        X, _ = blobs_100
        batch_results = self._run_batch(X)
        analysis = analyze_batch_results(batch_results)
        hai = np.array(analysis['hai_matrix'])
        np.testing.assert_allclose(np.diag(hai), 1.0, atol=1e-10,
            err_msg="HAI diagonal must be 1.0 (perfect self-similarity)")

    def test_hai_values_in_range(self, blobs_100):
        X, _ = blobs_100
        batch_results = self._run_batch(X)
        analysis = analyze_batch_results(batch_results)
        hai = np.array(analysis['hai_matrix'])
        assert np.all((hai >= 0) & (hai <= 1.0 + 1e-10)), \
            "HAI values must be in [0, 1]"

    def test_meta_linkage_exists(self, blobs_100):
        X, _ = blobs_100
        batch_results = self._run_batch(X)
        analysis = analyze_batch_results(batch_results)
        assert 'meta_linkage' in analysis, "analyze_batch_results must return 'meta_linkage'"

    def test_meta_linkage_shape(self, blobs_100):
        X, _ = blobs_100
        batch_results = self._run_batch(X)
        n_mpts = len(batch_results)
        analysis = analyze_batch_results(batch_results)
        Z = np.array(analysis['meta_linkage'])
        assert Z.shape == (n_mpts - 1, 4), \
            f"Meta linkage must have shape ({n_mpts - 1}, 4), got {Z.shape}"

    def test_medoids_keys_are_integers(self, blobs_100):
        X, _ = blobs_100
        batch_results = self._run_batch(X)
        analysis = analyze_batch_results(batch_results)
        medoids = analysis.get('medoids', {})
        for k in medoids.keys():
            assert isinstance(k, (int, np.integer)), f"Medoid key must be int, got {type(k)}"

    def test_ordered_mpts_matches_sorted_keys(self, blobs_100):
        X, _ = blobs_100
        batch_results = self._run_batch(X)
        analysis = analyze_batch_results(batch_results)
        ordered_mpts = analysis.get('ordered_mpts', [])
        expected_sorted = sorted([int(k) for k in batch_results.keys()])
        assert list(ordered_mpts) == expected_sorted, \
            "ordered_mpts must match the sorted batch keys"
