"""
conftest.py — Shared fixtures for MustaCHE pytest suite.
Generates synthetic datasets using scikit-learn utilities.
"""
import pytest
import numpy as np
from sklearn.datasets import make_blobs, make_moons


@pytest.fixture(scope="session")
def blobs_100():
    """100 samples, 4 well-separated Gaussian clusters, 2D."""
    X, y = make_blobs(n_samples=100, centers=4, cluster_std=0.6, random_state=42)
    return X.astype(np.float64), y


@pytest.fixture(scope="session")
def blobs_200():
    """200 samples, 3 Gaussian clusters, 3D."""
    X, y = make_blobs(n_samples=200, centers=3, n_features=3, cluster_std=0.8, random_state=7)
    return X.astype(np.float64), y


@pytest.fixture(scope="session")
def moons_150():
    """150 samples, 2 interleaved moons (non-convex clusters)."""
    X, y = make_moons(n_samples=150, noise=0.05, random_state=0)
    return X.astype(np.float64), y


@pytest.fixture(scope="session")
def flask_client():
    """Returns a Flask test client for integration tests."""
    from mustache import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
