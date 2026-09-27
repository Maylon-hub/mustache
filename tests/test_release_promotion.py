"""Publication gates use synthetic evidence; these are not OS qualification."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import zipfile

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/collect_release_artifacts.py"
spec = importlib.util.spec_from_file_location("rc_promotion", SCRIPT)
promotion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promotion)
SHA = "a" * 40
LABELS = ("wheel-full-suite", "sdist-full-suite", "wheel-smoke",
          "sdist-smoke", "wheel-pip-check", "sdist-pip-check")


@pytest.mark.parametrize("tag", [
    "cp311-cp311-macosx_10_9_x86_64", "cp311-cp311-win32",
    "cp312-cp312-win_amd64", "cp311-cp311-linux_x86_64",
    "cp311-cp311-manylinux_2_28_aarch64",
    "cp311-cp311-manylinux2014_aarch64", "cp311-cp311-manylinux2099_x86_64",
])
def test_reject_unqualified_wheel_tags(tag):
    with pytest.raises(AssertionError):
        promotion.validate_tags([tag], "core-sg-mustache")


def test_accept_auditwheel_manylinux_compatibility_aliases():
    tags = [
        "cp311-cp311-manylinux2014_x86_64",
        "cp311-cp311-manylinux_2_17_x86_64",
        "cp311-cp311-manylinux_2_28_x86_64",
    ]
    assert promotion.validate_tags(tags, "core-sg-mustache") == "Linux"


@pytest.fixture
def evidence(tmp_path):
    def create(name="core-sg-mustache"):
        project = {"name": name, "version": "0.4.5rc3" if name.startswith("core") else "0.3.0rc3"}
        src = tmp_path / "artifacts"
        src.mkdir()
        artifacts = []
        families = ("Windows", "Linux") if name.startswith("core") else ("any",)
        for family in families:
            tag = {"Windows": "cp311-cp311-win_amd64", "Linux": "cp311-cp311-manylinux_2_28_x86_64", "any": "py3-none-any"}[family]
            path = src / (name.replace("-", "_") + "-" + project["version"] + "-" + tag + ".whl")
            metadata = f"Name: {name}\nVersion: {project['version']}\nRequires-Python: <3.12,>=3.11\n"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(name + ".dist-info/METADATA", metadata)
                archive.writestr(name + ".dist-info/WHEEL", "Tag: " + tag + "\n")
            artifacts.append({"filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        path = src / (name.replace("-", "_") + "-" + project["version"] + ".tar.gz")
        data = f"Name: {name}\nVersion: {project['version']}\n".encode()
        with tarfile.open(path, "w:gz") as archive:
            member = tarfile.TarInfo("release/PKG-INFO")
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
        artifacts.append({"filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        reports = []
        for family in ("Windows", "Linux"):
            reports.append({"platform": family, "machine": "x86_64", "python": "3.11.0",
                "status": "PASS", "full_suites": True, "source_sha": SHA,
                "companion_sha": "b" * 40, "metadata": project,
                "commands": [{"label": label, "exit_code": 0} for label in LABELS],
                "artifacts": copy.deepcopy(artifacts)})
        return src, tmp_path / "promoted", project, reports
    return create


def save_reports(folder, reports):
    folder.mkdir()
    for i, report in enumerate(reports):
        sub = folder / str(i)
        sub.mkdir()
        (sub / "qualification.json").write_text(json.dumps(report))
    return folder


@pytest.mark.parametrize("name", ["core-sg-mustache", "mustache-core"])
def test_promote_only_passing_two_platform_artifacts(evidence, tmp_path, name):
    src, dst, project, reports = evidence(name)
    promotion.promote(src, dst, project, save_reports(tmp_path / "evidence", reports), SHA)
    assert {p.name for p in src.iterdir()} == {p.name for p in dst.iterdir()}


@pytest.mark.parametrize("fault", [
    "missing-linux", "smoke-only", "failed-command", "wrong-source",
    "wrong-python", "wrong-architecture", "unqualified-os", "tampered-artifact",
    "missing-suite", "different-companion",
])
def test_invalid_evidence_never_creates_destination(evidence, tmp_path, fault):
    src, dst, project, reports = evidence("mustache-core")
    if fault == "missing-linux":
        reports.pop()
    elif fault == "smoke-only":
        reports[1]["full_suites"] = False
    elif fault == "failed-command":
        reports[1]["commands"][0]["exit_code"] = 1
    elif fault == "wrong-source":
        reports[1]["source_sha"] = "c" * 40
    elif fault == "wrong-python":
        reports[1]["python"] = "3.12.0"
    elif fault == "wrong-architecture":
        reports[1]["machine"] = "aarch64"
    elif fault == "unqualified-os":
        reports[1]["platform"] = "macOS"
    elif fault == "tampered-artifact":
        reports[1]["artifacts"][0]["sha256"] = "0" * 64
    elif fault == "missing-suite":
        reports[1]["commands"].pop(0)
    elif fault == "different-companion":
        reports[1]["companion_sha"] = "c" * 40
    with pytest.raises(AssertionError):
        promotion.promote(src, dst, project, save_reports(tmp_path / "evidence", reports), SHA)
    assert not dst.exists()
