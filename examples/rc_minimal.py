"""Small reproducible API example; run using installed release artifacts."""
import pandas as pd
from sklearn.datasets import make_blobs
from mustache.core.batch import run_batch_clustering, analyze_batch_results

X, _ = make_blobs(n_samples=90, n_features=3, centers=3, random_state=42)
for metric in ("euclidean", "manhattan"):
    results = run_batch_clustering(pd.DataFrame(X), 4, 8, 2,
                                   metric=metric, algorithm="core-sg")
    analysis = analyze_batch_results(results)
    assert analysis["ordered_mpts"] == [4, 6, 8]
    print(metric, analysis["hai_computation"], analysis["medoids"])
