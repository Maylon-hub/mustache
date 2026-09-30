"""Promote only the Windows/Linux cp311 artifacts with passing qualification."""
import argparse
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tarfile
import tomllib
import zipfile


def read_wheel(path):
    with zipfile.ZipFile(path) as archive:
        meta = BytesParser().parsebytes(archive.read(next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))))
        tags = BytesParser().parsebytes(archive.read(next(n for n in archive.namelist() if n.endswith(".dist-info/WHEEL")))).get_all("Tag", [])
    return meta, tags


def validate_tags(tags, project_name):
    assert tags, "Wheel has no tags"
    if project_name == "mustache-core":
        assert set(tags) == {"py3-none-any"}
        return "any"
    families = set()
    for tag in tags:
        python, abi, platform = tag.split("-")
        assert python == abi == "cp311", "Only qualified CPython 3.11 wheels"
        if platform == "win_amd64":
            families.add("Windows")
        # auditwheel can add the manylinux2014 alias to a PEP 600 wheel.
        # Accept that standard x86-64 alias, not arbitrary Linux platforms.
        elif platform == "manylinux2014_x86_64" or re.fullmatch(r"manylinux_(?:[0-9]+_?)+_x86_64", platform):
            families.add("Linux")
        else:
            raise AssertionError("Unqualified RC wheel platform: " + platform)
    assert len(families) == 1
    return families.pop()


def promote(src, dst, project, qualification, expected_sha):
    assert not dst.exists(), "Use a new destination"
    reports = [json.loads(p.read_text()) for p in qualification.rglob("qualification.json")]
    assert len(reports) == 2, "Require exactly Windows and Linux qualification evidence"
    by_os = {}
    for report in reports:
        os_name = "Windows" if report["platform"].startswith("Windows") else "Linux" if report["platform"].startswith("Linux") else None
        assert os_name and os_name not in by_os, "No unqualified/duplicate platform"
        assert report["machine"].lower() in ("amd64", "x86_64")
        assert report["python"].startswith("3.11.")
        assert report["status"] == "PASS" and report["full_suites"] is True
        assert report["source_sha"] == expected_sha
        assert report["metadata"]["name"] == project["name"]
        assert report["metadata"]["version"] == project["version"]
        assert report["commands"] and all(c["exit_code"] == 0 for c in report["commands"])
        labels = {c["label"] for c in report["commands"]}
        assert {"wheel-full-suite", "sdist-full-suite", "wheel-smoke", "sdist-smoke",
                "wheel-pip-check", "sdist-pip-check"} <= labels
        by_os[os_name] = report
    assert set(by_os) == {"Windows", "Linux"}
    if project["name"] == "mustache-core":
        companions = {r.get("companion_sha") for r in reports}
        assert len(companions) == 1 and all(re.fullmatch(r"[0-9a-f]{40}", s or "") for s in companions), "Both platforms must qualify the same CORE-SG source"

    wheels = sorted(src.rglob("*.whl"))
    sdists = sorted(src.rglob("*.tar.gz"))
    assert len(sdists) == 1, "Promote the single common source distribution"
    assert len(wheels) == (1 if project["name"] == "mustache-core" else 2)
    chosen = []
    families = set()
    for wheel in wheels:
        meta, tags = read_wheel(wheel)
        assert meta["Name"] == project["name"] and meta["Version"] == project["version"]
        assert set(meta["Requires-Python"].split(",")) == {">=3.11", "<3.12"}
        family = validate_tags(tags, project["name"])
        assert family not in families
        families.add(family)
        sha = hashlib.sha256(wheel.read_bytes()).hexdigest()
        relevant = reports if family == "any" else [by_os[family]]
        assert all(any(a["sha256"] == sha and a["filename"] == wheel.name for a in r["artifacts"]) for r in relevant), "Selected wheel was not qualified"
        chosen.append(wheel)
    assert families == ({"any"} if project["name"] == "mustache-core" else {"Windows", "Linux"})
    sdist = sdists[0]
    with tarfile.open(sdist) as archive:
        members = [m for m in archive.getmembers() if m.name.count("/") == 1 and m.name.endswith("/PKG-INFO")]
        assert len(members) == 1
        meta = BytesParser().parsebytes(archive.extractfile(members[0]).read())
    assert meta["Name"] == project["name"] and meta["Version"] == project["version"]
    sha = hashlib.sha256(sdist.read_bytes()).hexdigest()
    assert all(any(a["sha256"] == sha and a["filename"] == sdist.name for a in r["artifacts"]) for r in reports), "Common sdist was not qualified on both platforms"
    chosen.append(sdist)
    assert len({p.name for p in chosen}) == len(chosen)
    dst.mkdir(parents=True)
    for artifact in chosen:
        shutil.copy2(artifact, dst / artifact.name)
    print("Selected qualified artifacts:", [p.name for p in chosen])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--qualification", type=Path, required=True)
    args = parser.parse_args()
    project = tomllib.loads(Path("pyproject.toml").read_text())["project"]
    promote(args.source, args.destination, project, args.qualification, os.environ["GITHUB_SHA"])


if __name__ == "__main__":
    main()
