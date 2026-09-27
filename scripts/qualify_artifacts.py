"""Qualify wheels and sdists in new venvs without source-shadowed imports.

The same driver lives in both repositories so each can be qualified separately.
Only test inputs/scripts are read from Git; production packages come from pip.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import tomllib
import venv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", choices=("core-sg", "mustache"), required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--companion-artifacts", type=Path)
    parser.add_argument("--companion-source", type=Path, help="Companion scripts and source identity, never an import path")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke-only", action="store_true", help="Local diagnostic only; mandatory CI runs full suites")
    args = parser.parse_args()
    assert sys.version_info[:2] == (3, 11)
    assert sys.platform in ("win32", "linux")
    assert platform.machine().lower() in ("amd64", "x86_64")
    source = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    assert not output.exists(), "Qualification output and venvs must be new"
    assert not output.is_relative_to(source), "Create environments outside the checkout"
    output.mkdir(parents=True)
    # Copy test helpers, never the production package, to the neutral test root.
    shutil.copytree(source / "scripts", output / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["NUMBA_CACHE_DIR"] = str(output / "numba-cache")
    env["MPLCONFIGDIR"] = str(output / "matplotlib-cache")
    evidence = {"project": args.project, "platform": platform.platform(), "machine": platform.machine(),
                "python": sys.version, "full_suites": not args.smoke_only, "commands": [], "artifacts": [], "status": "RUNNING"}

    def source_identity(path):
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    evidence["source_sha"] = source_identity(source)
    if args.project == "mustache":
        assert args.companion_source, "Retain the exact companion source SHA"
        evidence["companion_sha"] = source_identity(args.companion_source.resolve())

    def run(label, command, cwd=output):
        start = time.monotonic()
        log = output / (label + ".log")
        with log.open("w", encoding="utf-8") as stream:
            completed = subprocess.run(list(map(str, command)), cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
        evidence["commands"].append({"label": label, "command": list(map(str, command)), "cwd": str(cwd),
                                     "exit_code": completed.returncode, "seconds": round(time.monotonic()-start, 3)})
        if completed.returncode:
            print(log.read_text(encoding="utf-8", errors="replace")[-8000:], flush=True)
            raise RuntimeError(f"Qualification failed: {label}; see {log.name}")
        print("PASS", label, flush=True)

    def select(folder, extension):
        matches = list(folder.resolve().glob("*" + extension))
        assert len(matches) == 1, (folder, extension, matches)
        path = matches[0]
        evidence["artifacts"].append({"filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        return path

    try:
        for kind, extension in (("wheel", ".whl"), ("sdist", ".tar.gz")):
            prefix = output / (kind + "-venv")
            venv.EnvBuilder(with_pip=True).create(prefix)
            python = prefix / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            run(kind + "-bootstrap", [python, "-m", "pip", "install", "--upgrade", "pip"])
            if args.project == "mustache":
                assert args.companion_artifacts, "Install newly built CORE-SG first"
                companion = select(args.companion_artifacts, extension)
                run(kind + "-install-core", [python, "-m", "pip", "install", companion])
            artifact = select(args.artifacts, extension)
            run(kind + "-install", [python, "-m", "pip", "install", artifact])
            run(kind + "-test-tools", [python, "-m", "pip", "install", "pytest", "pytest-cov"])
            run(kind + "-pip-check", [python, "-m", "pip", "check"])
            if args.project == "mustache":
                run(kind + "-native-companion", [python, args.companion_source.resolve() / "scripts/rc_smoke.py"])
            run(kind + "-smoke", [python, source / "scripts/rc_smoke.py"])
            if args.project == "mustache":
                run(kind + "-cli", [python, "-m", "mustache.cli", "--help"])
                run(kind + "-example", [python, source / "examples/rc_minimal.py"])
            if not args.smoke_only:
                if args.project == "core-sg":
                    run(kind + "-full-suite", [python, source / "scripts/run_installed_tests.py", "--junitxml", output / (kind + "-tests.xml")])
                else:
                    tests = output / (kind + "-tests")
                    shutil.copytree(source / "tests", tests)
                    run(kind + "-full-suite", [python, "-m", "pytest", tests, "-q", "-p", "no:flask", "-o", "python_files=test_*.py", "--junitxml", output / (kind + "-tests.xml")])
            run(kind + "-freeze", [python, "-m", "pip", "freeze", "--all"])
        evidence["metadata"] = tomllib.loads((source / "pyproject.toml").read_text())["project"]
        evidence["status"] = "PASS"
    finally:
        (output / "qualification.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
