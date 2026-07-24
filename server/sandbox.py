import os
import posixpath
from dataclasses import dataclass
from typing import Optional

from e2b import AsyncSandbox

REMOTE_APP_DIR = "/home/user/app"


class UnrunnableAppError(Exception):
    """Raised when we cannot determine how to run the generated app."""


def get_timeout() -> int:
    return int(os.environ.get("E2B_SANDBOX_TIMEOUT", "900"))  # 15 min default


# In-process registry so /stop can kill a sandbox without reconnecting
# (single-instance MVP; a horizontally-scaled deployment would reconnect by id).
_active: dict[str, AsyncSandbox] = {}


@dataclass
class RunResult:
    sandbox_id: str
    kind: str  # "web" | "script"
    preview_url: Optional[str]
    output: Optional[str]
    port: Optional[int]


@dataclass
class RunConfig:
    kind: str  # "web" | "script"
    install_cmd: Optional[str]
    start_cmd: str
    port: Optional[int]
    work_dir: str  # subdirectory (relative to app root) to run from


def _basename(path: str) -> str:
    return path.split("/")[-1]


def _dirname(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""


def _shallowest(paths: list[str]) -> str:
    return sorted(paths, key=lambda p: (p.count("/"), len(p)))[0]


def _pick_entry(py_files: list[str], preferred: tuple[str, ...]) -> Optional[str]:
    """Prefers a known entry filename (shallowest wins), else the shallowest .py."""
    for name in preferred:
        matches = [f for f in py_files if _basename(f).lower() == name]
        if matches:
            return _shallowest(matches)
    return _shallowest(py_files) if py_files else None


def detect_run_config(files: dict[str, str]) -> RunConfig:
    """Infer how to run the app, searching nested folders and preferring the
    shallowest entry point. Raises UnrunnableAppError if nothing runnable is found."""
    names = list(files.keys())

    # 1. Node app — locate the shallowest package.json and run from its folder.
    pkgs = [n for n in names if _basename(n) == "package.json"]
    if pkgs:
        pkg_path = _shallowest(pkgs)
        work_dir = _dirname(pkg_path) or "."
        pkg = files.get(pkg_path, "")
        if '"dev"' in pkg:
            start = "npm run dev"
        elif '"start"' in pkg:
            start = "npm start"
        else:
            node_entry = _pick_entry(
                [n for n in names if n.endswith(".js") and (_dirname(n) or ".") == work_dir],
                ("index.js", "server.js", "app.js"),
            )
            start = f"node {_basename(node_entry)}" if node_entry else "npm start"
        return RunConfig("web", "npm install", start, 3000, work_dir)

    # 2. Python web app.
    py_files = [n for n in names if n.endswith(".py")]
    joined = "\n".join(files.get(n, "") for n in py_files).lower()
    web_frameworks = ("flask", "fastapi", "uvicorn", "gunicorn", "http.server", "aiohttp", "starlette")
    if py_files and any(fw in joined for fw in web_frameworks):
        entry = _pick_entry(py_files, ("app.py", "main.py", "server.py", "wsgi.py")) or _shallowest(py_files)
        work_dir = _dirname(entry) or "."
        install = _install_for(names, work_dir)
        base = _basename(entry)
        if "flask" in joined:
            return RunConfig("web", install, f"flask --app {base[:-3]} run --host 0.0.0.0 --port 5000", 5000, work_dir)
        if "fastapi" in joined or "uvicorn" in joined or "starlette" in joined:
            return RunConfig("web", install, f"uvicorn {base[:-3]}:app --host 0.0.0.0 --port 8000", 8000, work_dir)
        return RunConfig("web", install, f"python {base}", 8000, work_dir)

    # 3. Python script / CLI.
    if py_files:
        entry = _pick_entry(py_files, ("main.py", "app.py")) or _shallowest(py_files)
        work_dir = _dirname(entry) or "."
        return RunConfig("script", _install_for(names, work_dir), f"python {_basename(entry)}", None, work_dir)

    # 4. Static site — serve the folder containing the shallowest index.html.
    html = [n for n in names if _basename(n).lower() == "index.html"]
    if html:
        work_dir = _dirname(_shallowest(html)) or "."
        return RunConfig("web", None, "python3 -m http.server 8000", 8000, work_dir)

    raise UnrunnableAppError(
        "Could not determine how to run this app. Expected a package.json, a Python "
        "entry point (app.py/main.py), or an index.html, but found: "
        + ", ".join(sorted(names)[:20])
    )


def _install_for(names: list[str], work_dir: str) -> Optional[str]:
    reqs = [n for n in names if _basename(n) == "requirements.txt"]
    if not reqs:
        return None
    # Prefer a requirements.txt in the work dir, else the shallowest one.
    in_dir = [n for n in reqs if (_dirname(n) or ".") == work_dir]
    chosen = in_dir[0] if in_dir else _shallowest(reqs)
    rel = _basename(chosen) if (_dirname(chosen) or ".") == work_dir else posixpath.relpath(chosen, work_dir)
    return f"pip install -r {rel}"


async def run_app(files: dict[str, str]) -> RunResult:
    cfg = detect_run_config(files)
    run_dir = REMOTE_APP_DIR if cfg.work_dir in (".", "") else f"{REMOTE_APP_DIR}/{cfg.work_dir}"

    sbx = await AsyncSandbox.create(timeout=get_timeout())
    _active[sbx.sandbox_id] = sbx
    try:
        for path, content in files.items():
            await sbx.files.write(f"{REMOTE_APP_DIR}/{path}", content)

        if cfg.install_cmd:
            await sbx.commands.run(cfg.install_cmd, cwd=run_dir, timeout=300)

        if cfg.kind == "web":
            await sbx.commands.run(cfg.start_cmd, cwd=run_dir, background=True)
            preview_url = f"https://{sbx.get_host(cfg.port)}"
            return RunResult(sbx.sandbox_id, "web", preview_url, None, cfg.port)

        # script: run to completion, capture output, then release the sandbox
        result = await sbx.commands.run(cfg.start_cmd, cwd=run_dir, timeout=60)
        output = (result.stdout or "") + (result.stderr or "")
        await sbx.kill()
        _active.pop(sbx.sandbox_id, None)
        return RunResult(sbx.sandbox_id, "script", None, output or "(no output)", None)
    except Exception:
        # ensure we don't leak a sandbox on failure
        await sbx.kill()
        _active.pop(sbx.sandbox_id, None)
        raise


async def stop_sandbox(sandbox_id: str) -> None:
    sbx = _active.pop(sandbox_id, None)
    if sbx is not None:
        await sbx.kill()
        return
    # Fallback: reconnect by id and kill (e.g. after a server restart).
    try:
        reconnected = await AsyncSandbox.connect(sandbox_id)
        await reconnected.kill()
    except Exception:
        pass  # best-effort; the sandbox will expire on its own timeout
