"""Artifact-only integration: execute outside both production source trees."""
import importlib.metadata as metadata
import io
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import zipfile

import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs
import core_sg
import mustache


def main():
    for module in (mustache, core_sg):
        assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), module.__file__
    from mustache.routes import SESSION_DATA
    from mustache.core import storage
    root = Path(tempfile.mkdtemp(prefix="mustache-rc-smoke-"))
    os.environ["MUSTACHE_PROJECTS_DIR"] = str(root)
    X, _ = make_blobs(n_samples=90, n_features=3, centers=3, random_state=42)
    data = pd.DataFrame(X).to_csv(index=False).encode()
    summary = []
    for algorithm, metric in (("core-sg", "manhattan"), ("core-sg", "euclidean"), ("hdbscan", "euclidean")):
        app = mustache.create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        response = client.post("/batch", data={"file": (io.BytesIO(data), "seed42.csv"),
            "algorithm": algorithm, "metric": metric, "min_mpts": "4", "max_mpts": "8", "step": "2", "csv_header": "present"})
        assert response.status_code == 200, response.get_data(as_text=True)
        payload = response.get_json()
        analysis = payload["analysis"]
        assert analysis["ordered_mpts"] == [4, 6, 8]
        H = np.asarray(analysis["hai_matrix"])
        np.testing.assert_allclose(H, H.T)
        np.testing.assert_allclose(np.diag(H), 1)
        assert np.all((H >= 0) & (H <= 1))
        assert analysis["hai_computation"]["approximate"] is False
        for key, result in payload["results"].items():
            assert result["reachability_data"]["mpts"] == int(key)
            assert result["reachability_data"]["metric"] == metric
        saved = client.post("/api/projects/save", json={"name": f"RC {algorithm} {metric}"})
        assert saved.status_code == 200, saved.get_data(as_text=True)
        project_id = saved.get_json()["project"]["id"]
        original = storage.load_project(project_id)
        SESSION_DATA.clear()
        del client, app
        # New app/client and empty process state: reopening must restore disk data.
        client = mustache.create_app().test_client()
        reopened = client.get(f"/api/projects/{project_id}/data")
        assert reopened.status_code == 200, reopened.get_data(as_text=True)
        restored = storage.load_project(project_id)
        assert restored["analysis"] == original["analysis"]
        assert restored["results"] == original["results"]
        for key, expected in {"algorithm": algorithm, "metric": metric, "min_mpts": 4, "max_mpts": 8, "step": 2, "n_samples": 90}.items():
            assert restored["params"][key] == expected, (key, restored["params"])
        csv = client.post("/export_branches_csv", json={})
        assert csv.status_code == 200, csv.get_data(as_text=True)
        assert len(pd.read_csv(io.BytesIO(csv.data))) == 90
        archive = client.get(f"/api/projects/{project_id}/export_zip")
        assert archive.status_code == 200, archive.get_data(as_text=True)
        with zipfile.ZipFile(io.BytesIO(archive.data)) as z:
            assert {"metadata.json", "results.json", "data.csv"} <= set(z.namelist())
            assert json.loads(z.read("results.json"))["analysis"]["medoids"] == analysis["medoids"]
        summary.append({"algorithm": algorithm, "metric": metric, "project": project_id, "medoids": analysis["medoids"], "status": "PASS"})
        SESSION_DATA.clear()
    subprocess.run([sys.executable, Path(__file__).with_name("rc_cli_smoke.py")], check=True)
    print(json.dumps({"modules": {"mustache": mustache.__file__, "core_sg": core_sg.__file__},
        "versions": {n: metadata.version(n) for n in ("mustache-core", "core-sg-mustache", "hdbscan")},
        "projects": str(root), "scenarios": summary}, indent=2))


if __name__ == "__main__":
    main()
