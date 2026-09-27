import os
import json
import uuid
import time
import shutil
import zipfile
import io
import re
import hashlib
import platform
import importlib.util
import pandas as pd
from pathlib import Path
from importlib.metadata import PackageNotFoundError, version


def _package_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "development"


def runtime_provenance():
    """Distribution versions alone do not identify an edited source checkout."""
    sources = {}
    for name in ('hai.py', 'clustering.py', 'batch.py'):
        source = Path(__file__).parent / name
        sources[f'mustache/core/{name}'] = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.find_spec('core_sg')
    if spec and spec.origin:
        for name in ('core_sg.py', 'hdbscan_adapter.py'):
            source = Path(spec.origin).parent / name
            if source.exists():
                sources[f'core_sg/{name}'] = hashlib.sha256(source.read_bytes()).hexdigest()
    return {'python': platform.python_version(), 'platform': platform.platform(),
            'distributions': {name: _package_version(name) for name in
                ('mustache-core', 'core-sg-mustache', 'hdbscan', 'numpy', 'scipy', 'scikit-learn')},
            'source_sha256': sources}

def get_projects_dir() -> Path:
    """Returns the user projects storage directory (~/.mustache/projects)."""
    home = Path.home()
    projects_dir = Path(os.environ['MUSTACHE_PROJECTS_DIR']).expanduser() if os.environ.get('MUSTACHE_PROJECTS_DIR') else home / ".mustache" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir


def _project_dir(project_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', project_id):
        raise ValueError('Invalid project identifier.')
    return get_projects_dir() / project_id


def restore_params(params, metadata, analysis):
    """Read old aliases without recomputing or overwriting scientific results."""
    restored = dict(params)
    ordered = analysis.get('ordered_mpts') or []
    aliases = {'min_mpts': 'mpts_min', 'max_mpts': 'mpts_max', 'metric': 'distance',
               'algorithm': 'algorithm', 'step': 'step', 'dataset_name': 'dataset_name',
               'n_samples': 'points', 'execution_time': 'execution_time'}
    for key, alias in aliases.items():
        if key not in restored and alias in metadata:
            restored[key] = metadata[alias]
    if ordered:
        restored.setdefault('min_mpts', min(ordered))
        restored.setdefault('max_mpts', max(ordered))
        if len(ordered) > 1:
            gaps = [b - a for a, b in zip(sorted(ordered), sorted(ordered)[1:])]
            if len(set(gaps)) == 1:
                restored.setdefault('step', gaps[0])
    for key in ('algorithm', 'metric'):
        if restored.get(key):
            restored[key] = restored[key].lower()
    return restored

def list_projects() -> list:
    """Lists all saved projects sorted by creation date descending."""
    projects_dir = get_projects_dir()
    projects = []
    
    for item in projects_dir.iterdir():
        if item.is_dir():
            meta_path = item / "metadata.json"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        meta["id"] = item.name
                        projects.append(meta)
                except Exception as e:
                    print(f"Error reading project {item.name}: {e}")
                    
    # Sort by timestamp descending
    projects.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return projects

def save_project(name: str, params: dict, analysis: dict, results: dict, raw_df: pd.DataFrame = None) -> dict:
    """Saves an execution as a project."""
    projects_dir = get_projects_dir()
    project_id = str(uuid.uuid4())[:8]
    proj_dir = projects_dir / project_id
    proj_dir.mkdir(parents=True, exist_ok=True)

    n_samples = len(raw_df) if raw_df is not None else params.get('n_samples', 0)
    date_str = time.strftime("%m/%d/%Y %H:%M")

    metadata = {
        "schema_version": 2,
        "id": project_id,
        "name": name or "Unnamed Analysis",
        "dataset_name": params.get('dataset_name'),
        "execution_time": params.get('execution_time'),
        "date_added": date_str,
        "timestamp": time.time(),
        "points": n_samples,
        "distance": params.get("metric", "euclidean").upper(),
        "algorithm": params.get("algorithm", "core-sg").upper(),
        "mpts_min": params.get("min_mpts", 2),
        "mpts_max": params.get("max_mpts", 10),
        "step": params.get("step", 1),
        "mustache_version": _package_version("mustache-core"),
        "core_sg_version": _package_version("core-sg-mustache"),
        "status": "COMPLETED"
    }
    metadata['runtime_provenance'] = runtime_provenance()
    if raw_df is not None:
        # Hash the exact persisted CSV representation, not a platform-dependent
        # binary memory layout; this also includes column order and names.
        metadata['dataset_sha256'] = hashlib.sha256(raw_df.to_csv(index=False).encode('utf-8')).hexdigest()

    # Write metadata.json
    with open(proj_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Write results.json
    payload = {
        "params": params,
        "analysis": analysis,
        "results": results
    }
    with open(proj_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(payload, f)

    # Write raw_data.csv if present
    if raw_df is not None:
        raw_df.to_csv(proj_dir / "data.csv", index=False)

    return metadata

def load_project(project_id: str) -> dict:
    """Loads a project by ID."""
    proj_dir = _project_dir(project_id)
    if not proj_dir.exists():
        raise FileNotFoundError(f"Project {project_id} does not exist.")

    with open(proj_dir / "metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    with open(proj_dir / "results.json", "r", encoding="utf-8") as f:
        payload = json.load(f)

    data_path = proj_dir / "data.csv"
    raw_df = pd.read_csv(data_path) if data_path.exists() else None

    return {
        "metadata": metadata,
        "params": restore_params(payload.get("params", {}), metadata, payload.get('analysis', {})),
        "analysis": payload.get("analysis", {}),
        "results": payload.get("results", {}),
        "raw_df": raw_df
    }

def delete_project(project_id: str) -> bool:
    """Deletes a saved project directory."""
    proj_dir = _project_dir(project_id)
    if proj_dir.exists():
        shutil.rmtree(proj_dir)
        return True
    return False

def create_project_zip(project_id: str) -> io.BytesIO:
    """Creates a zip archive containing project files."""
    proj_dir = _project_dir(project_id)
    if not proj_dir.exists():
        raise FileNotFoundError(f"Project {project_id} does not exist.")

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(proj_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(proj_dir)
                zf.write(file_path, arcname)

    memory_file.seek(0)
    return memory_file
