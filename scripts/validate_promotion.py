"""Validate promotion of already-tested artifacts; never publish from an untested run."""
import json
import os
import urllib.request
import sys
try:
    import tomllib
except ImportError:
    import tomli as tomllib

project = tomllib.loads(open("pyproject.toml", encoding="utf-8").read())["project"]
version = project["version"]
assert os.environ["CONFIRM_VERSION"] == version
assert os.environ["GITHUB_REF"] == "refs/tags/v" + version, "Dispatch on the matching version tag"
repo = os.environ["GITHUB_REPOSITORY"]
run_id = os.environ["VALIDATION_RUN_ID"]
assert run_id.isdigit()
url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}"
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"], "Accept": "application/vnd.github+json"})
with urllib.request.urlopen(req, timeout=30) as response:
    run = json.load(response)
assert run["path"] == ".github/workflows/ci.yml", "Expected the complete RC validation workflow"
assert run["head_sha"] == os.environ["GITHUB_SHA"], "Validation must cover this exact commit"
assert run["head_repository"]["full_name"] == repo, "No fork artifacts"
assert run["event"] in ("push", "workflow_dispatch"), "No PR artifacts"
assert run["status"] == "completed" and run["conclusion"] == "success"
print("Validated CI run", run_id, "at", run["head_sha"], "for", version)
