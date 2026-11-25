"""Entrypoint for the hosted Iris preview and the full local Docker app."""

import os
import platform
from importlib.metadata import version

from flask import Flask, abort, jsonify, render_template


def create_app():
    mode = os.environ.get("MUSTACHE_CONTAINER_MODE", "preview")
    if mode == "local":
        from mustache import create_app as create_mustache_app

        return create_mustache_app()
    if mode != "preview":
        raise ValueError("MUSTACHE_CONTAINER_MODE must be 'preview' or 'local'.")

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 1024

    @app.get("/healthz")
    def health():
        from core_sg import _mst_kruskal, _reweight

        return jsonify(
            python=platform.python_version(),
            mustache=version("mustache-core"),
            core_sg=version("core-sg-mustache"),
            native_extensions=[_mst_kruskal.__name__, _reweight.__name__],
            mode="preview",
        )

    @app.get("/")
    def index():
        return render_template("vercel_preview.html", rows=None, matrix=None)

    @app.post("/iris")
    def iris():
        from mustache.core.batch import analyze_batch_results, run_batch_clustering
        from mustache.core.sample_datasets import load_dataset

        frame, _ = load_dataset("iris")
        results = run_batch_clustering(frame, 2, 10, 2, metric="euclidean", algorithm="core-sg")
        analysis = analyze_batch_results(results)
        matrix = analysis.get("hai_matrix")
        if matrix is None:
            abort(500)
        rows = [
            (mpts, results[str(mpts)]["n_clusters"], results[str(mpts)]["noise_points"],
             len(results[str(mpts)]["condensed_tree"]))
            for mpts in analysis["ordered_mpts"]
        ]
        return render_template("vercel_preview.html", rows=rows, matrix=matrix)

    return app
