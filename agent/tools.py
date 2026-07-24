import pathlib
import subprocess
from contextvars import ContextVar
from typing import Optional, Tuple

from langchain_core.tools import tool

_DEFAULT_PROJECT_ROOT = pathlib.Path.cwd() / "generated_project"
_project_root: ContextVar[pathlib.Path] = ContextVar("project_root", default=_DEFAULT_PROJECT_ROOT)


def get_project_root() -> pathlib.Path:
    """Returns the project root for the current request/task context."""
    return _project_root.get()


def set_project_root(path: pathlib.Path) -> None:
    """Sets the project root for the current request/task context and ensures it exists."""
    path.mkdir(parents=True, exist_ok=True)
    _project_root.set(path)


def safe_path_for_project(path: str) -> pathlib.Path:
    root = get_project_root().resolve()
    p = (root / path).resolve()
    if root not in p.parents and root != p.parent and root != p:
        raise ValueError("Attempt to write outside project root")
    return p


def _ensure_dir(directory: pathlib.Path) -> None:
    """Creates `directory`, removing any stray file that occupies a path
    component where a directory is needed (the coder occasionally writes a bare
    file like `templates` before writing `templates/index.html`)."""
    root = get_project_root().resolve()
    directory = directory.resolve()
    if directory == root:
        return
    cur = root
    for part in directory.relative_to(root).parts:
        cur = cur / part
        if cur.exists() and not cur.is_dir():
            cur.unlink()
        cur.mkdir(exist_ok=True)


@tool
def write_file(path: str, content: str) -> str:
    """Writes content to a file at the specified path within the project root."""
    p = safe_path_for_project(path)
    _ensure_dir(p.parent)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"WROTE:{p}"


@tool
def read_file(path: str) -> str:
    """Reads content from a file at the specified path within the project root."""
    p = safe_path_for_project(path)
    if not p.exists():
        return ""
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


@tool
def get_current_directory() -> str:
    """Returns the current working directory."""
    return str(get_project_root())


@tool
def list_files(directory: str = ".") -> str:
    """Lists all files in the specified directory within the project root."""
    p = safe_path_for_project(directory)
    if not p.is_dir():
        return f"ERROR: {p} is not a directory"
    root = get_project_root()
    files = [str(f.relative_to(root)) for f in p.glob("**/*") if f.is_file()]
    return "\n".join(files) if files else "No files found."


@tool
def run_cmd(cmd: str, cwd: Optional[str] = None, timeout: int = 30) -> Tuple[int, str, str]:
    """Runs a shell command in the specified directory and returns the result."""
    cwd_dir = safe_path_for_project(cwd) if cwd else get_project_root()
    res = subprocess.run(cmd, shell=True, cwd=str(cwd_dir), capture_output=True, text=True, timeout=timeout)
    return res.returncode, res.stdout, res.stderr


def init_project_root() -> str:
    root = get_project_root()
    root.mkdir(parents=True, exist_ok=True)
    return str(root)
