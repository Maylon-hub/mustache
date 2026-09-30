"""Installed CLI + real process restart + persisted CORE-SG HTTP scenarios."""
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs
import mustache
import core_sg


def main():
    for module in (mustache, core_sg):
        assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    root = Path(tempfile.mkdtemp(prefix="mustache-cli-rc-"))
    env = dict(os.environ, MUSTACHE_PROJECTS_DIR=str(root / "projects"))
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    X, _ = make_blobs(n_samples=90, n_features=3, centers=3, random_state=42)
    csv_data = pd.DataFrame(X).to_csv(index=False).encode()
    saved = []
    proc = None

    def fetch(path, payload=None, content_type="application/json"):
        body = json.dumps(payload).encode() if isinstance(payload, dict) else payload
        request = urllib.request.Request(base + path, data=body,
            headers={"Content-Type": content_type} if body is not None else {})
        with urllib.request.urlopen(request, timeout=30) as response:
            assert response.status == 200
            return response.read()

    def start(log):
        process = subprocess.Popen([sys.executable, "-m", "mustache.cli", "--port", str(port), "--host", "127.0.0.1"],
            cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Installed CLI exited before becoming ready")
            try:
                with urllib.request.urlopen(base + "/api/session_status", timeout=1) as response:
                    assert not json.load(response)["has_active_batch"]
                return process
            except (OSError, urllib.error.URLError):
                time.sleep(0.2)
        process.terminate()
        process.wait(timeout=10)
        raise RuntimeError("Installed CLI readiness timed out")

    def stop(process):
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)

    with (root / "cli.log").open("wb") as log:
        try:
            proc = start(log)
            assert b"HAI Similarity Matrix" in fetch("/")
            assert fetch("/static/img/Mustache_Logo_SVG.svg")
            for metric in ("euclidean", "manhattan"):
                boundary = "mustache-rc-seed42"
                parts = []
                for key, value in {"algorithm":"core-sg", "metric":metric, "min_mpts":"4", "max_mpts":"8", "step":"2", "csv_header":"present"}.items():
                    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
                parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="seed42.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode()+csv_data+b"\r\n")
                parts.append(f"--{boundary}--\r\n".encode())
                result = json.loads(fetch("/batch", b"".join(parts), "multipart/form-data; boundary="+boundary))
                analysis = result["analysis"]
                assert analysis["ordered_mpts"] == [4, 6, 8]
                H = np.asarray(analysis["hai_matrix"])
                np.testing.assert_allclose(H, H.T)
                np.testing.assert_allclose(np.diag(H), 1)
                assert np.all((H >= 0) & (H <= 1))
                for mpts, hierarchy in result["results"].items():
                    assert hierarchy["reachability_data"]["mpts"] == int(mpts)
                    assert hierarchy["reachability_data"]["metric"] == metric
                project = json.loads(fetch("/api/projects/save", {"name":"HTTP RC "+metric}))["project"]
                before = json.loads(fetch(f"/api/projects/{project['id']}/data"))
                saved.append((metric, project["id"], before))
            stop(proc)
            proc = None
            proc = start(log)  # A genuinely different CLI process, not a new app object.
            for metric, project_id, before in saved:
                restored = json.loads(fetch(f"/api/projects/{project_id}/data"))
                assert restored == before
                for key, value in {"algorithm":"core-sg", "metric":metric, "min_mpts":4, "max_mpts":8, "step":2, "n_samples":90}.items():
                    assert restored["params"][key] == value
                assert json.loads(fetch("/api/session_status"))["has_active_batch"]
                assert len(pd.read_csv(io.BytesIO(fetch("/export_branches_csv", {})))) == 90
                with zipfile.ZipFile(io.BytesIO(fetch(f"/api/projects/{project_id}/export_zip"))) as archive:
                    assert {"metadata.json", "results.json", "data.csv"} <= set(archive.namelist())
                    assert json.loads(archive.read("results.json"))["analysis"]["medoids"] == before["analysis"]["medoids"]
        finally:
            if proc is not None:
                stop(proc)
    print(json.dumps({"status":"PASS", "real_cli_restart":True, "metrics":[m for m, _, _ in saved],
        "modules":{"mustache":mustache.__file__,"core_sg":core_sg.__file__},"cli_log":str(root/"cli.log")},indent=2))


if __name__ == "__main__":
    main()
