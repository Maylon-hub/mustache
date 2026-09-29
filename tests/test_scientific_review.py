"""Regression oracles independent of the optimized pipeline's implementation."""
import io
import json

import hdbscan
import numpy as np
import pandas as pd
import pytest
from scipy.cluster.hierarchy import cophenet, linkage
from sklearn.metrics import adjusted_rand_score, pairwise_distances

from mustache.core.batch import run_batch_clustering, analyze_batch_results
from mustache.core.clustering import run_clustering, hierarchy_reachability
from mustache.core.hai import compute_hai_matrix, compute_medoids
from mustache.core import storage
from mustache.core.validation import SUPPORTED_METRICS


Z1 = np.array([[0, 1, 1, 2], [2, 3, 2, 3]], dtype=float)
Z2 = np.array([[1, 2, 1, 2], [0, 3, 2, 3]], dtype=float)


def test_hai_known_original_pair_sum():
    # Legacy HAI: two unordered pairs differ by 1/3. 1 - 2*(2/3)/9.
    hai, metadata = compute_hai_matrix([Z1, Z2], 3, return_metadata=True)
    np.testing.assert_allclose(hai, [[1, 23/27], [23/27, 1]], atol=1e-14, rtol=0)
    assert metadata['normalization'] == '2/n^2 sum over unordered pairs'


def test_hai_ignores_height_scale_but_preserves_topology():
    scaled = Z1.copy(); scaled[:, 2] *= 73
    assert compute_hai_matrix([Z1, scaled], 3)[0, 1] == 1


def test_hai_simultaneous_merges_are_invariant_to_binary_tie_order():
    balanced = np.array([[0, 1, 1, 2], [2, 3, 1, 2], [4, 5, 1, 4]], float)
    chained = np.array([[0, 1, 1, 2], [2, 4, 1, 3], [3, 5, 1, 4]], float)
    assert compute_hai_matrix([balanced, chained], 4)[0, 1] == 1
    sampled = compute_hai_matrix([balanced, chained], 4, max_exact_samples=2)
    assert sampled[0, 1] == 1


def test_hai_rejects_invalid_cardinality():
    bad = Z1.copy(); bad[0, 3] = 1
    with pytest.raises(ValueError, match='cardinalities'):
        compute_hai_matrix([bad], 3)


@pytest.mark.parametrize('invalid', [float('nan'), float('inf')])
def test_hai_rejects_nonfinite_hierarchies(invalid):
    bad = Z1.copy(); bad[0, 2] = invalid
    with pytest.raises(ValueError, match='finite'):
        compute_hai_matrix([bad], 3)


def test_hai_rejects_fractional_sample_indices():
    bad = Z1.copy(); bad[0, 0] = .5
    with pytest.raises(ValueError, match='integer'):
        compute_hai_matrix([bad], 3)


def test_sampled_hai_preserves_normalization_and_metadata():
    hai, meta = compute_hai_matrix([Z1, Z2], 3, max_exact_samples=2, sample_pairs=100000, random_state=31, return_metadata=True)
    assert hai[0, 1] == pytest.approx(23/27, abs=0.004)
    np.testing.assert_equal(hai, hai.T)
    np.testing.assert_equal(np.diag(hai), 1)
    assert np.all((hai >= 0) & (hai <= 1))
    assert meta['sampling'].startswith('uniform ordered distinct pairs with replacement')
    assert meta['bit_generator'] == 'PCG64' and meta['random_state'] == 31
    assert 'not simultaneous' in meta['error_bound_scope']


def test_medoid_minimizes_within_cluster_distance_and_ties():
    hai = np.array([[1, .7, .6, .1], [.7, 1, .9, .1], [.6, .9, 1, .1], [.1, .1, .1, 1]])
    assert compute_medoids(hai, [4, 4, 4, -1]) == {4: 1}
    assert compute_medoids(np.ones((3, 3)), [0, 0, 0]) == {0: 0}


def test_reachability_is_adjacent_cophenetic_of_this_tree():
    Z = np.array([[0, 1, 2, 2], [2, 3, 3, 2], [4, 5, 9, 4]], float)
    reach = hierarchy_reachability(Z, [0, 0, 1, 1], mpts=2, metric='manhattan')
    assert reach['ordering'] == [0, 1, 2, 3]
    assert reach['y'] == [None, 2, 9, 3]
    assert reach['labels'] == [0, 0, 1, 1]
    assert reach['mpts'] == 2 and reach['metric'] == 'manhattan'


@pytest.fixture
def small_df():
    return pd.DataFrame(np.random.default_rng(37).normal(size=(30, 3)) + 2)


@pytest.mark.parametrize('algorithm', ['hdbscan', 'core-sg'])
@pytest.mark.parametrize('metric', SUPPORTED_METRICS['hdbscan'])
def test_supported_metric_full_pipeline(algorithm, metric, small_df):
    batch = run_batch_clustering(small_df, 2, 4, 2, algorithm=algorithm, metric=metric)
    analysis = analyze_batch_results(batch)
    assert analysis['ordered_mpts'] == [2, 4]
    assert np.asarray(analysis['hai_matrix']).shape == (2, 2)
    for mpts, result in batch.items():
        assert result['metric'] == metric
        assert result['reachability_data']['metric'] == metric
        assert result['reachability_data']['mpts'] == int(mpts)
        assert sorted(result['reachability_data']['ordering']) == list(range(len(small_df)))


@pytest.mark.parametrize('metric', SUPPORTED_METRICS['hdbscan'])
def test_core_public_unrounded_matches_reference_mst_and_labels(metric, small_df):
    batch = run_batch_clustering(small_df, 2, 6, 2, algorithm='core-sg', metric=metric)
    for key, result in batch.items():
        ref = hdbscan.HDBSCAN(min_cluster_size=int(key), min_samples=int(key), metric=metric,
            algorithm='generic' if metric == 'cosine' else 'best',
            match_reference_implementation=True, approx_min_span_tree=False,
            core_dist_n_jobs=1, **({'p': 2} if metric == 'minkowski' else {})).fit(small_df.to_numpy())
        # MSTs can have tied edges and different binary serialization. Compare
        # the induced ultrametric, not an arbitrary row/edge ordering.
        np.testing.assert_allclose(cophenet(np.array(result['linkage_z'])), cophenet(ref.single_linkage_tree_.to_numpy()), atol=1e-8)
        assert adjusted_rand_score(result['labels'], ref.labels_) == 1


def test_batch_fits_core_once_and_extracts_every_requested_mpts(monkeypatch, small_df):
    import core_sg
    original = core_sg.CoreSG
    instances, fits, extracts = [], [], []
    class TrackedCore(original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs); instances.append(self)
        def fit(self, data, k_max):
            fits.append((id(self), k_max)); return super().fit(data, k_max)
        def extract_hierarchy_from_core_sg(self, k, **kwargs):
            extracts.append((id(self), k)); return super().extract_hierarchy_from_core_sg(k, **kwargs)
    monkeypatch.setattr(core_sg, 'CoreSG', TrackedCore)
    run_batch_clustering(small_df, 2, 6, 2)
    assert len(instances) == 1 and fits == [(id(instances[0]), 6)]
    assert extracts == [(id(instances[0]), k) for k in [2, 4, 6]]


def test_core_fast_distances_are_real(small_df):
    from core_sg import CoreSG
    model = CoreSG(no_noise=False).fit(small_df.to_numpy(), k_max=6)
    np.testing.assert_allclose(model.distance_matrix_, pairwise_distances(small_df), atol=1e-12)
    edges = model.metric_edges_
    expected = np.linalg.norm(small_df.to_numpy()[edges[:, 0].astype(int)] - small_df.to_numpy()[edges[:, 1].astype(int)], axis=1)
    np.testing.assert_allclose(edges[:, 2], expected, atol=1e-12)


def test_missing_linkage_cannot_shift_mpts_matrix_order():
    with pytest.raises(ValueError, match='Missing hierarchy'):
        analyze_batch_results({'2': {'linkage_z': Z1.tolist()}, '4': {}})


def test_root_branch_contains_all_hierarchies():
    analysis = analyze_batch_results({'2': {'linkage_z': Z1.tolist()}, '4': {'linkage_z': Z2.tolist()}, '6': {'linkage_z': Z1.tolist()}})
    figure = json.loads(analysis['meta_dendrogram_json'])
    # The final Plotly trace is an interaction layer, not a hierarchy branch.
    branches = [trace for trace in figure['data'] if trace.get('meta', {}).get('mpts_values')]
    root = max(branches, key=lambda trace: len(trace['meta']['mpts_values']))
    assert root['meta']['mpts_values'] == [2, 4, 6]
    for group, mpts in analysis['medoids'].items():
        index = analysis['ordered_mpts'].index(mpts)
        assert analysis['meta_labels'][index] == group


def batch_post(client, metric='manhattan', **extra):
    return client.post('/batch', data={'sample_dataset': 'iris', 'algorithm': 'hdbscan', 'metric': metric, 'min_mpts': '2', 'max_mpts': '6', 'step': '2', **extra})


@pytest.mark.parametrize('metric', ['angular', 'pearson', 'precomputed', 'not-a-metric'])
def test_invalid_metric_rejected_before_clustering(flask_client, metric):
    response = batch_post(flask_client, metric)
    assert response.status_code == 400
    assert 'Distance metric' in response.get_json()['error']


@pytest.mark.parametrize('algorithm', ['core-sg', 'hdbscan'])
def test_saved_project_restores_parameters_partition_and_plots(flask_client, algorithm):
    response = batch_post(flask_client, algorithm=algorithm)
    assert response.status_code == 200
    batch = response.get_json()
    assert batch['params']['metric'] == 'manhattan'
    assert batch['params']['algorithm'] == algorithm
    cut = flask_client.post('/cut_dendrogram', json={'y_threshold': 0}).get_json()
    saved = flask_client.post('/api/projects/save', json={'name': 'Review run', 'selected_mpts': [2, 6]}).get_json()['project']
    assert saved['mpts_max'] == 6 and saved['distance'] == 'MANHATTAN'
    assert saved['dataset_name'] == 'Iris' and saved['points'] == 150
    assert saved['timestamp'] > 0 and saved['execution_time'] >= 0
    assert len(saved['dataset_sha256']) == 64
    assert 'mustache/core/hai.py' in saved['runtime_provenance']['source_sha256']
    restored = flask_client.get(f"/api/projects/{saved['id']}/data").get_json()
    assert restored['params'] == batch['params']
    for field in ('meta_labels', 'medoids'):
        assert restored['analysis'][field] == cut[field]
    assert restored['analysis']['cut_threshold'] == 0
    assert restored['analysis']['selection_mode'] == 'threshold'
    assert restored['analysis']['selected_mpts'] == [2, 6]
    assert restored['analysis']['hai_matrix'] == batch['analysis']['hai_matrix']
    assert restored['analysis']['meta_dendrogram_json']
    assert all(result['reachability_data'] for result in restored['results'].values())
    auto = flask_client.post('/cut_dendrogram', json={'mode': 'automatic'}).get_json()
    assert auto['meta_labels'] == batch['analysis']['meta_labels']
    assert auto['medoids'] == batch['analysis']['medoids']


def test_batch_endpoint_defaults_to_core_sg(flask_client):
    response = flask_client.post('/batch', data={
        'sample_dataset': 'iris', 'min_mpts': 2, 'max_mpts': 6,
        'step': 2, 'metric': 'manhattan',
    })
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['params']['algorithm'] == 'core-sg'
    assert payload['analysis']['ordered_mpts'] == [2, 4, 6]
    assert all(result['algorithm'] == 'core-sg' and result['metric'] == 'manhattan'
               for result in payload['results'].values())


def test_cached_cut_updates_saved_partition(flask_client):
    batch_post(flask_client)
    first = flask_client.post('/cut_dendrogram', json={'y_threshold': 0}).get_json()
    flask_client.post('/cut_dendrogram', json={'y_threshold': 1})
    again = flask_client.post('/cut_dendrogram', json={'y_threshold': 0}).get_json()
    assert again['from_cache']
    saved = flask_client.post('/api/projects/save', json={'name': 'Cached cut'}).get_json()['project']
    loaded = flask_client.get(f"/api/projects/{saved['id']}/data").get_json()
    assert loaded['analysis']['medoids'] == first['medoids']
    assert loaded['analysis']['meta_labels'] == first['meta_labels']


def test_single_hierarchy_cut_and_headerless_csv(flask_client):
    response = flask_client.post('/batch', data={'file': (io.BytesIO(b'1,1\n2,2\n3,3\n4,4\n5,5\n'), 'no-header.csv'), 'algorithm': 'hdbscan', 'min_mpts': 2, 'max_mpts': 2, 'step': 1})
    assert response.status_code == 200
    assert response.get_json()['params']['n_samples'] == 5
    assert flask_client.post('/cut_dendrogram', json={'y_threshold': 0}).get_json()['meta_labels'] == [1]


def test_old_project_parameter_fallback():
    params = storage.restore_params({}, {'mpts_min': 2, 'mpts_max': 8, 'distance': 'MANHATTAN', 'algorithm': 'HDBSCAN', 'points': 90}, {'ordered_mpts': [2, 4, 6, 8]})
    assert params == {'min_mpts': 2, 'max_mpts': 8, 'metric': 'manhattan', 'algorithm': 'hdbscan', 'n_samples': 90, 'step': 2}


def test_ui_labels_and_metric_form(flask_client):
    html = flask_client.get('/').get_data(as_text=True)
    for text in ('HAI Similarity Matrix', 'Meta-Hierarchy Dendrogram', 'Representative hierarchy (medoid)', 'Maximum mpts:', 'Distance metric:', 'name="metric"'):
        assert text in html
    assert 'ed <li>' not in html and 'Medoid mpts:' not in html


def test_csv_numeric_column_names_can_be_explicit(flask_client):
    response = flask_client.post('/batch', data={'file': (io.BytesIO(b'0,1\n1,2\n2,3\n3,4\n4,5\n'), 'numeric-header.csv'), 'csv_header': 'present', 'algorithm': 'hdbscan', 'min_mpts': 2, 'max_mpts': 2})
    assert response.status_code == 200 and response.get_json()['params']['n_samples'] == 4


def test_zero_vectors_rejected_for_cosine(flask_client):
    response = flask_client.post('/batch', data={'file': (io.BytesIO(b'0,0\n1,2\n3,4\n5,6\n'), 'zero.csv'), 'metric': 'cosine', 'algorithm': 'hdbscan', 'min_mpts': 2, 'max_mpts': 2})
    assert response.status_code == 400 and 'zero vectors' in response.get_json()['error']


def test_cut_cache_boundary_includes_merges_at_exact_height(flask_client):
    from mustache.routes import SESSION_DATA
    SESSION_DATA.update(meta_linkage=[[0, 1, .5, 2]], hai_matrix=[[1, .5], [.5, 1]], ordered_mpts=[2, 4])
    below = flask_client.post('/cut_dendrogram', json={'y_threshold': .49}).get_json()
    exact = flask_client.post('/cut_dendrogram', json={'y_threshold': .5}).get_json()
    assert below['meta_labels'] == [1, 2] and exact['meta_labels'] == [1, 1]


def test_manual_groups_update_medoids_and_persist(flask_client):
    batch_post(flask_client)
    manual = flask_client.post('/cut_dendrogram', json={'mode': 'manual', 'groups': [[2, 4], [6]]}).get_json()
    assert manual['meta_labels'] == [0, 0, 1]
    assert manual['medoids'] == {'0': 2, '1': 6}
    saved = flask_client.post('/api/projects/save', json={'name': 'Manual groups', 'selected_mpts': [2, 4, 6]}).get_json()['project']
    restored = flask_client.get(f"/api/projects/{saved['id']}/data").get_json()['analysis']
    assert restored['manual_groups'] == [[2, 4], [6]]
    assert restored['selection_mode'] == 'manual' and restored['medoids'] == manual['medoids']


def test_manual_groups_reject_overlap_and_unknown_hierarchies(flask_client):
    batch_post(flask_client)
    for groups in ([[2, 4], [4, 6]], [[99]], [[2.5]], [[]]):
        assert flask_client.post('/cut_dendrogram', json={'mode': 'manual', 'groups': groups}).status_code == 400


def test_manual_unselected_hierarchies_are_not_automatic_outliers(flask_client):
    batch_post(flask_client)
    manual = flask_client.post('/cut_dendrogram', json={'mode': 'manual', 'groups': [[4]]}).get_json()
    assert manual['medoids'] == {'0': 4} and manual['outliers'] == []
    assert manual['unselected_count'] == 2 and manual['meta_labels'] == [-1, 0, -1]


def test_meta_clustering_uses_original_single_linkage_density_setting(monkeypatch):
    import mustache.core.hai as module
    actual = module.HDBSCAN
    calls = []
    def tracked(**kwargs):
        calls.append(kwargs); return actual(**kwargs)
    monkeypatch.setattr(module, 'HDBSCAN', tracked)
    module.run_meta_clustering(np.array([[1, .9, .1], [.9, 1, .2], [.1, .2, 1]]))
    assert calls[0]['min_samples'] == 1 and calls[0]['metric'] == 'precomputed'
