"""Small, deterministic datasets bundled through scikit-learn for UI demos."""

from dataclasses import dataclass

import pandas as pd
from sklearn.datasets import (
    load_breast_cancer,
    load_iris,
    load_wine,
    make_blobs,
    make_circles,
    make_moons,
)


@dataclass(frozen=True)
class DatasetInfo:
    key: str
    name: str
    description: str
    samples: int
    features: int
    kind: str


DATASETS = {
    "iris": DatasetInfo("iris", "Iris", "Three flower species with four measurements.", 150, 4, "Classic"),
    "wine": DatasetInfo("wine", "Wine", "Chemical analysis of wines from three cultivars.", 178, 13, "Classic"),
    "breast-cancer": DatasetInfo("breast-cancer", "Breast Cancer Wisconsin", "Thirty numeric features from diagnostic images.", 569, 30, "Classic"),
    "moons": DatasetInfo("moons", "Two Moons", "Two interleaving non-convex clusters with light noise.", 500, 2, "Synthetic"),
    "circles": DatasetInfo("circles", "Concentric Circles", "Two nested clusters that challenge distance-based methods.", 500, 2, "Synthetic"),
    "blobs": DatasetInfo("blobs", "Four Blobs", "Four well-separated Gaussian groups for a baseline test.", 500, 2, "Synthetic"),
}


def list_datasets() -> list[dict]:
    return [info.__dict__.copy() for info in DATASETS.values()]


def load_dataset(key: str) -> tuple[pd.DataFrame, DatasetInfo]:
    if key not in DATASETS:
        raise KeyError(f"Unknown sample dataset: {key}")

    if key == "iris":
        bunch = load_iris()
        frame = pd.DataFrame(bunch.data, columns=bunch.feature_names)
    elif key == "wine":
        bunch = load_wine()
        frame = pd.DataFrame(bunch.data, columns=bunch.feature_names)
    elif key == "breast-cancer":
        bunch = load_breast_cancer()
        frame = pd.DataFrame(bunch.data, columns=bunch.feature_names)
    elif key == "moons":
        values, _ = make_moons(n_samples=500, noise=0.06, random_state=42)
        frame = pd.DataFrame(values, columns=["x", "y"])
    elif key == "circles":
        values, _ = make_circles(n_samples=500, noise=0.035, factor=0.45, random_state=42)
        frame = pd.DataFrame(values, columns=["x", "y"])
    else:
        values, _ = make_blobs(n_samples=500, centers=4, cluster_std=0.75, random_state=42)
        frame = pd.DataFrame(values, columns=["x", "y"])

    return frame, DATASETS[key]
