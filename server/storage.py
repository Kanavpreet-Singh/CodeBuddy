import os
from pathlib import Path


def get_storage_root() -> Path:
    """Base directory under which each app's generated files live."""
    return Path(os.environ.get("STORAGE_ROOT", "./generated_projects")).resolve()


def app_root(user_id: str, app_id: str) -> Path:
    return get_storage_root() / user_id / app_id


def safe_file_path(user_id: str, app_id: str, rel_path: str) -> Path:
    """Resolve a file path inside an app's storage dir, guarding against traversal."""
    root = app_root(user_id, app_id).resolve()
    p = (root / rel_path).resolve()
    if root != p and root not in p.parents:
        raise ValueError("Attempt to access outside app root")
    return p
