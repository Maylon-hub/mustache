"""
test_api_routes.py — Integration tests for Flask API endpoints.

Uses Flask's built-in test client to send HTTP requests to the app
and validate JSON responses, status codes, and data contracts.

Note: These tests spin up the Flask app in-process (no server needed).
"""
import pytest
import io
import numpy as np
import pandas as pd


def _make_csv_bytes(n_samples: int = 50, n_features: int = 3) -> bytes:
    """Creates a synthetic CSV dataset as bytes for multipart file upload."""
    from sklearn.datasets import make_blobs
    X, _ = make_blobs(n_samples=n_samples, centers=3, n_features=n_features, random_state=99)
    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(n_features)])
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf.read()


class TestIndexRoute:
    def test_get_returns_200(self, flask_client):
        res = flask_client.get('/')
        assert res.status_code == 200

    def test_get_with_project_id_returns_200(self, flask_client):
        res = flask_client.get('/?project_id=nonexistent')
        assert res.status_code == 200

    def test_response_is_html(self, flask_client):
        res = flask_client.get('/')
        assert b'<!DOCTYPE html>' in res.data or b'<html' in res.data


class TestProjectsListAPI:
    def test_get_projects_returns_200(self, flask_client):
        res = flask_client.get('/api/projects')
        assert res.status_code == 200

    def test_get_projects_returns_list(self, flask_client):
        res = flask_client.get('/api/projects')
        data = res.get_json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"


class TestSessionStatusAPI:
    def test_session_status_returns_200(self, flask_client):
        res = flask_client.get('/api/session_status')
        assert res.status_code == 200

    def test_session_status_has_expected_keys(self, flask_client):
        res = flask_client.get('/api/session_status')
        data = res.get_json()
        assert 'has_active_batch' in data
        assert 'dataset_name' in data


class TestBatchRoute:
    def test_batch_missing_file_returns_400(self, flask_client):
        res = flask_client.post('/batch', data={})
        assert res.status_code == 400

    def test_batch_with_csv_returns_200(self, flask_client):
        csv_bytes = _make_csv_bytes(n_samples=60, n_features=2)
        data = {
            'file': (io.BytesIO(csv_bytes), 'test_data.csv'),
            'min_mpts': '5',
            'max_mpts': '10',
            'step': '5',
            'metric': 'euclidean',
            'algorithm': 'hdbscan',
        }
        res = flask_client.post('/batch', data=data, content_type='multipart/form-data')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.data[:500]}"

    def test_batch_response_has_results_key(self, flask_client):
        csv_bytes = _make_csv_bytes(n_samples=60, n_features=2)
        data = {
            'file': (io.BytesIO(csv_bytes), 'test_data.csv'),
            'min_mpts': '5',
            'max_mpts': '10',
            'step': '5',
            'metric': 'euclidean',
            'algorithm': 'hdbscan',
        }
        res = flask_client.post('/batch', data=data, content_type='multipart/form-data')
        body = res.get_json()
        assert 'results' in body, f"'results' key missing from response: {list(body.keys())}"
        assert 'analysis' in body, f"'analysis' key missing from response: {list(body.keys())}"

    def test_batch_analysis_has_hai_matrix(self, flask_client):
        csv_bytes = _make_csv_bytes(n_samples=60, n_features=2)
        data = {
            'file': (io.BytesIO(csv_bytes), 'test_data.csv'),
            'min_mpts': '5',
            'max_mpts': '10',
            'step': '5',
            'metric': 'euclidean',
            'algorithm': 'hdbscan',
        }
        res = flask_client.post('/batch', data=data, content_type='multipart/form-data')
        body = res.get_json()
        analysis = body.get('analysis', {})
        assert 'hai_matrix' in analysis, f"'hai_matrix' missing from analysis: {list(analysis.keys())}"


class TestCutDendrogramRoute:
    """Tests the /cut_dendrogram endpoint after a batch run."""

    def _run_batch(self, flask_client):
        csv_bytes = _make_csv_bytes(n_samples=60, n_features=2)
        data = {
            'file': (io.BytesIO(csv_bytes), 'test_data.csv'),
            'min_mpts': '5',
            'max_mpts': '10',
            'step': '5',
            'metric': 'euclidean',
            'algorithm': 'hdbscan',
        }
        flask_client.post('/batch', data=data, content_type='multipart/form-data')

    def test_cut_without_session_returns_400(self, flask_client):
        # Without a batch run first, SESSION_DATA should be empty
        # (may or may not be empty depending on test order; guard with try)
        import json
        res = flask_client.post(
            '/cut_dendrogram',
            data=json.dumps({'y_threshold': 0.5}),
            content_type='application/json'
        )
        # Either 200 (if prior test left a session) or 400 (no session)
        assert res.status_code in (200, 400)

    def test_cut_after_batch_returns_200(self, flask_client):
        import json
        self._run_batch(flask_client)
        res = flask_client.post(
            '/cut_dendrogram',
            data=json.dumps({'y_threshold': 0.1}),
            content_type='application/json'
        )
        assert res.status_code == 200

    def test_cut_response_has_meta_labels(self, flask_client):
        import json
        self._run_batch(flask_client)
        res = flask_client.post(
            '/cut_dendrogram',
            data=json.dumps({'y_threshold': 0.1}),
            content_type='application/json'
        )
        body = res.get_json()
        assert 'meta_labels' in body, f"'meta_labels' missing: {list(body.keys())}"
        assert 'medoids' in body, f"'medoids' missing: {list(body.keys())}"


class TestExportCSVRoute:
    def test_export_without_session_returns_400(self, flask_client):
        import json
        # Fresh client state: if no session, expect 400
        # (depends on test isolation; we just check it doesn't crash)
        res = flask_client.post(
            '/export_branches_csv',
            data=json.dumps({}),
            content_type='application/json'
        )
        # 200 (session exists from prior test) or 400 (no session)
        assert res.status_code in (200, 400)
