"""Inspect release contents and print complete inventories with SHA-256."""
from pathlib import Path
import hashlib
import json
import sys
import tarfile
import zipfile

report = []
for artifact in sorted(Path(sys.argv[1]).iterdir()):
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            names = archive.namelist()
            contents = {n: archive.read(n) for n in names if not n.endswith("/")}
        is_wheel = True
    elif artifact.name.endswith(".tar.gz"):
        with tarfile.open(artifact) as archive:
            names = [m.name for m in archive.getmembers() if m.isfile()]
            contents = {n: archive.extractfile(n).read() for n in names}
        is_wheel = False
    else:
        continue
    forbidden = ("/.venv/", "/__pycache__/", "/.git/", "/.pytest_cache/", "/legacy/", "/datasets/", "/results/", "final_audit_", "final_summary_", "technical_review_", ".pyc", ".pdf", ".tex", ".log")
    assert not [n for n in names if any(p in "/" + n for p in forbidden)], artifact
    assert not any(n.endswith(".c") for n in names), "Regenerate Cython C during build"
    profile = str(Path.home())
    private_paths = (profile.encode(), profile.replace(chr(92), "/").encode(), profile.replace(chr(92), chr(92) * 2).encode())
    leaked = [n for n, data in contents.items() if any(p in data for p in private_paths)]
    assert not leaked, ("Local profile path leaked into artifact", artifact.name, leaked)
    for required in ("LICENSE", "CITATION.cff", "CHANGELOG.md", "RELEASE_NOTES.md", "DATASETS.md", "AUTHORS.md"):
        assert any(n.endswith("/" + required) for n in names), (artifact, required)
    if is_wheel:
        assert any(n.endswith(".dist-info/METADATA") for n in names)
        if artifact.name.startswith("core_sg_"):
            for extension in ("_mst_kruskal", "_reweight"):
                assert any(extension in n and n.endswith((".pyd", ".so")) for n in names), (artifact, extension)
        else:
            for resource in ("mustache/templates/index.html", "mustache/static/js/main.js", "mustache/static/img/Mustache_Logo_SVG.svg"):
                assert resource in names, (artifact, resource)
    else:
        assert any(n.endswith("/pyproject.toml") for n in names)
        assert not any(n.endswith((".pyd", ".so", ".dll")) for n in names)
    report.append({"artifact": artifact.name, "bytes": artifact.stat().st_size,
                   "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(), "entries": names})
assert report, "No distributions found"
print(json.dumps(report, indent=2))
