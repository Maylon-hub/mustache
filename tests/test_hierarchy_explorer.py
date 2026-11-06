"""Scientific and persistence regressions for individual hierarchy inspection."""

import io

import hdbscan
import numpy as np
import pandas as pd
import pytest
from scipy.cluster.hierarchy import dendrogram
from sklearn.datasets import make_blobs
from sklearn.metrics import adjusted_rand_score

from mustache.core.batch import run_batch_clustering
from mustache.core.clustering import hierarchy_reachability, run_clustering
from mustache.core.group_tree import group_members, group_tree_summary, point_trajectory


ROWS = [
    {'parent': 4, 'child': 5, 'lambda_val': 1.0, 'child_size': 2},
    {'parent': 4, 'child': 6, 'lambda_val': 1.0, 'child_size': 2},
    {'parent': 5, 'child': 0, 'lambda_val': 2.0, 'child_size': 1},
    {'parent': 5, 'child': 1, 'lambda_val': 3.0, 'child_size': 1},
    {'parent': 6, 'child': 2, 'lambda_val': 4.0, 'child_size': 1},
    {'parent': 6, 'child': 3, 'lambda_val': 5.0, 'child_size': 1},
]


@pytest.fixture
def separated():
    data, _ = make_blobs(n_samples=48, centers=[(-8, -8), (0, 8), (8, -8)],
                         cluster_std=.18, random_state=17)
    return pd.DataFrame(data, columns=['x', 'y'])


def test_condensed_group_members_are_input_rows_not_leaf_positions():
    summary = group_tree_summary(ROWS, 4, 2)
    assert summary['root'] == 4
    assert {group['id']: group['size_at_birth'] for group in summary['groups']} == {4: 4, 5: 2, 6: 2}
    assert group_members(ROWS, 4, 4) == [0, 1, 2, 3]
    assert group_members(ROWS, 4, 5) == [0, 1]
    assert group_members(ROWS, 4, 6) == [2, 3]
    with pytest.raises(ValueError, match='Unknown group'):
        group_members(ROWS, 4, 1)


def test_point_trajectory_uses_edges_not_final_label():
    path = point_trajectory(ROWS, 4, 0, flat_label=-1)
    assert [node['group_id'] for node in path['groups']] == [4, 5]
    assert [node['size_at_birth'] for node in path['groups']] == [4, 2]
    assert [node['exit_lambda'] for node in path['groups']] == [1, 2]
    assert path['flat_status'] == 'noise' and path['point_departure_lambda'] == 2
    assert point_trajectory(ROWS, 4, 0, flat_label=0)['flat_status'] == 'cluster'
    with pytest.raises(ValueError, match='outside'):
        point_trajectory(ROWS, 4, 4, flat_label=-1)


def test_reachability_labels_follow_original_rows_after_leaf_reordering():
    linkage = np.array([[1, 2, .2, 2], [0, 4, .5, 3], [3, 5, 2, 4]], float)
    labels = np.array([-1, 0, 1, 2])
    reach = hierarchy_reachability(linkage, labels, mpts=2, metric='euclidean')
    order = dendrogram(linkage, no_plot=True)['leaves']
    assert reach['ordering'] == order
    assert reach['labels'] == labels[order].tolist()
    assert sorted(reach['ordering']) == list(range(4))
    assert reach['labels'][reach['ordering'].index(0)] == -1
    assert reach['labels'][reach['ordering'].index(1)] == 0


def test_explicit_and_automatic_minimum_cluster_size_are_distinct(separated):
    automatic = run_batch_clustering(separated, 2, 6, 2)
    explicit = run_batch_clustering(separated, 2, 6, 2, min_cluster_size=7)
    assert [automatic[str(m)]['min_cluster_size'] for m in (2, 4, 6)] == [2, 4, 6]
    assert [explicit[str(m)]['min_cluster_size'] for m in (2, 4, 6)] == [7, 7, 7]
    assert [explicit[str(m)]['min_samples'] for m in (2, 4, 6)] == [2, 4, 6]
    for result in explicit.values():
        assert result['group_tree']['min_cluster_size'] == 7
        assert result['condensation_threshold'] == 8
        assert result['group_tree']['condensation_threshold'] == 8
        assert sorted(result['reachability_data']['ordering']) == list(range(len(separated)))
        np.testing.assert_array_equal(np.asarray(result['labels'])[result['reachability_data']['ordering']],
                                      result['reachability_data']['labels'])
    for invalid in (1, len(separated) + 1):
        with pytest.raises(ValueError, match='Minimum cluster size'):
            run_batch_clustering(separated, 2, 4, 2, min_cluster_size=invalid)


def test_core_condensed_tree_and_labels_match_reference_fit(separated):
    result = run_clustering(separated, min_cluster_size=7, min_samples=4, compact=True)
    reference = hdbscan.HDBSCAN(min_cluster_size=7, min_samples=4,
        match_reference_implementation=True, approx_min_span_tree=False,
        core_dist_n_jobs=1).fit(separated.to_numpy())
    assert adjusted_rand_score(result['labels'], reference.labels_) == 1
    assert result['n_clusters'] >= 2
    assert result['group_tree']['method'] == 'hdbscan-condense-tree-from-fitted-linkage'
    assert {tuple((row['parent'], row['child'], row['child_size'])) for row in result['condensed_tree']} == {
        tuple((int(row['parent']), int(row['child']), int(row['child_size'])))
        for row in reference.condensed_tree_.to_numpy()}
    assert len(group_members(result['condensed_tree'], len(separated), result['group_tree']['root'])) == len(separated)


def test_no_valid_flat_clusters_remains_genuine_noise(separated):
    result = run_clustering(separated, min_cluster_size=len(separated), min_samples=5, compact=True)
    assert result['n_clusters'] == 0
    assert result['noise_points'] == len(separated)
    assert set(result['labels']) == {-1}
    assert set(result['reachability_data']['labels']) == {-1}
    assert result['group_tree']['root'] >= len(separated)


@pytest.mark.parametrize('minimum_size, expected_noise', [(2, True), (5, False), (20, True)])
def test_noise_and_clusters_match_reference_on_two_blobs(minimum_size, expected_noise):
    points, _ = make_blobs(n_samples=40, centers=[(-6, -6), (6, 6)],
                           cluster_std=.18, random_state=11)
    data = pd.DataFrame(points, columns=['x', 'y'])
    result = run_clustering(data, min_cluster_size=minimum_size,
                            min_samples=2, compact=True)
    reference = hdbscan.HDBSCAN(
        min_cluster_size=minimum_size, min_samples=2,
        match_reference_implementation=True, approx_min_span_tree=False,
        core_dist_n_jobs=1,
    ).fit(points)
    assert adjusted_rand_score(result['labels'], reference.labels_) == 1
    assert (result['noise_points'] > 0) is expected_noise
    assert result['n_clusters'] == len(set(result['labels']) - {-1})
    order = result['reachability_data']['ordering']
    assert sorted(order) == list(range(len(points)))
    assert result['reachability_data']['labels'] == np.asarray(result['labels'])[order].tolist()
    assert result['group_tree']['n_samples'] == len(points)


def test_single_flat_cluster_is_not_misidentified_as_noise():
    # The reachability mapper must preserve a legitimate cluster-0 label even
    # when no other flat cluster exists. This is independent of cluster policy.
    linkage = np.array([[0, 2, .1, 2], [1, 3, .3, 3], [4, 5, .7, 4]], float)
    reach = hierarchy_reachability(linkage, [0, 0, 0, 0], mpts=2, metric='euclidean')
    assert reach['labels'] == [0, 0, 0, 0]
    assert reach['ordering'] != [0, 1, 2, 3]


def test_three_flat_clusters_and_noise_survive_leaf_reordering():
    linkage = np.array([[0, 2, .1, 2], [1, 3, .3, 3], [4, 5, .7, 4]], float)
    labels = np.array([-1, 0, 1, 2])
    reach = hierarchy_reachability(linkage, labels, mpts=2, metric='euclidean')
    assert set(reach['labels']) == {-1, 0, 1, 2}
    assert all(reach['labels'][position] == int(labels[row])
               for position, row in enumerate(reach['ordering']))


def test_batch_api_group_point_save_reload_and_export(flask_client, separated):
    csv = separated.to_csv(index=False).encode()
    response = flask_client.post('/batch', data={
        'file': (io.BytesIO(csv), 'separated.csv'), 'csv_header': 'present',
        'min_mpts': '2', 'max_mpts': '4', 'step': '2', 'algorithm': 'core-sg',
        'metric': 'manhattan', 'min_cluster_size_mode': 'explicit',
        'min_cluster_size': '7',
    }, content_type='multipart/form-data')
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body['params']['min_cluster_size'] == 7
    assert body['params']['min_cluster_size_mode'] == 'explicit'
    assert body['results']['2']['min_samples'] == 2
    root = body['results']['2']['group_tree']['root']
    group = flask_client.get(f'/api/hierarchies/2/groups/{root}')
    assert group.status_code == 200
    assert group.get_json()['sample_indices'] == list(range(len(separated)))
    point = flask_client.get('/api/hierarchies/2/points/0')
    assert point.status_code == 200
    assert point.get_json()['trajectory']['point_id'] == 0
    assert flask_client.get('/api/hierarchies/2/points/999').status_code == 400
    saved = flask_client.post('/api/projects/save', json={
        'name': 'Explorer test',
        'explorer_selection': {'mpts': 2, 'group_id': root, 'point_id': 0},
    }).get_json()
    assert saved['success']
    project_id = saved['project']['id']
    restored = flask_client.get(f'/api/projects/{project_id}/data').get_json()
    assert restored['params']['min_cluster_size'] == 7
    assert restored['analysis']['explorer_selection']['group_id'] == root
    assert flask_client.get(f'/api/hierarchies/2/groups/{root}').get_json()['count'] == len(separated)
    exported = flask_client.post('/export_branches_csv', json={'mpts_list': [2]})
    assert exported.status_code == 200
    assert 'MinClusterSize_mpts_2' in exported.get_data(as_text=True)
    assert 'MinSamples_mpts_2' in exported.get_data(as_text=True)
    assert flask_client.get(f'/api/projects/{project_id}/export_zip').status_code == 200
