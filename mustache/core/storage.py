import os
import json
import uuid
import time
import shutil
import zipfile
import io
import pandas as pd
from pathlib import Path

def get_projects_dir() -> Path:
    """Returns the user projects storage directory (~/.mustache/projects)."""
    home = Path.home()
    projects_dir = home / ".mustache" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir

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

    n_samples = len(raw_df) if raw_df is not None else 0
    date_str = time.strftime("%m/%d/%Y %H:%M")

    metadata = {
        "id": project_id,
        "name": name or "Unnamed Analysis",
        "date_added": date_str,
        "timestamp": time.time(),
        "points": n_samples,
        "distance": params.get("metric", "euclidean").upper(),
        "algorithm": params.get("algorithm", "core-sg").upper(),
        "mpts_min": params.get("min_mpts", 2),
        "mpts_max": params.get("max_mpts", 10),
        "step": params.get("step", 1),
        "status": "COMPLETED"
    }

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
    proj_dir = get_projects_dir() / project_id
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
        "params": payload.get("params", {}),
        "analysis": payload.get("analysis", {}),
        "results": payload.get("results", {}),
        "raw_df": raw_df
    }

def delete_project(project_id: str) -> bool:
    """Deletes a saved project directory."""
    proj_dir = get_projects_dir() / project_id
    if proj_dir.exists():
        shutil.rmtree(proj_dir)
        return True
    return False

def create_project_zip(project_id: str) -> io.BytesIO:
    """Creates a zip archive containing project files."""
    proj_dir = get_projects_dir() / project_id
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
