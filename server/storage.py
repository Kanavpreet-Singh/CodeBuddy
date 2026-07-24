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


def read_app_files(user_id: str, app_id: str) -> dict[str, str]:
    """Reads all text files for an app into a {relative_path: content} mapping."""
    root = app_root(user_id, app_id)
    out: dict[str, str] = {}
    if root.exists():
        for f in sorted(root.glob("**/*")):
            if f.is_file():
                rel = str(f.relative_to(root)).replace("\\", "/")
                try:
                    out[rel] = f.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue  # skip binary files
    return out
