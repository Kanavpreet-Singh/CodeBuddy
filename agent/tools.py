import ast
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


def _python_syntax_error(path: pathlib.Path, content: str) -> Optional[str]:
    """Returns a description of the syntax error in `content` if it's a .py file
    with invalid syntax, else None. Catching this at write-time (rather than only
    at run time in the sandbox) prevents a bad edit from ever landing on disk —
    e.g. an edit_file/write_file call that garbles two function definitions
    together, which otherwise silently crashes the app on startup much later."""
    if path.suffix != ".py":
        return None
    try:
        ast.parse(content)
        return None
    except SyntaxError as e:
        pointer = f" near: {e.text.strip()!r}" if e.text else ""
        return f"SyntaxError: {e.msg} at line {e.lineno}{pointer}"


@tool
def write_file(path: str, content: str) -> str:
    """Writes content to a file at the specified path within the project root."""
    p = safe_path_for_project(path)
    error = _python_syntax_error(p, content)
    if error:
        return (
            f"ERROR: not written — this content has invalid Python syntax: {error}. "
            "Fix the syntax and call write_file again with corrected content."
        )
    _ensure_dir(p.parent)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"WROTE:{p}"


@tool
def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Makes a targeted edit to an existing file: replaces one exact occurrence of
    old_string with new_string, leaving the rest of the file untouched. Use this
    instead of write_file whenever you are fixing or adjusting part of a file that
    already has correct content — it only touches the text you specify, so it can't
    accidentally discard or regress unrelated working code. old_string must match
    the current file content exactly (including whitespace/indentation) and must be
    unique in the file; include a few surrounding lines if needed to make it unique.
    """
    p = safe_path_for_project(path)
    if not p.exists():
        return f"ERROR: {path} does not exist. Use write_file to create a new file."
    content = p.read_text(encoding="utf-8")
    count = content.count(old_string)
    if count == 0:
        return (
            "ERROR: old_string was not found in the file. It must match the file's "
            "current content exactly, including whitespace and line breaks. "
            "Re-read the file with read_file and try again with the exact text."
        )
    if count > 1:
        return (
            f"ERROR: old_string matches {count} locations in the file, not 1. "
            "Include more surrounding context so it uniquely identifies one location."
        )
    new_content = content.replace(old_string, new_string, 1)
    error = _python_syntax_error(p, new_content)
    if error:
        return (
            f"ERROR: not applied — this edit would leave invalid Python syntax: {error}. "
            "Re-read the file, check indentation and surrounding braces/colons, and "
            "try edit_file again with a corrected old_string/new_string."
        )
    p.write_text(new_content, encoding="utf-8")
    return f"EDITED:{p}"


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
