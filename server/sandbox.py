import os
from dataclasses import dataclass
from typing import Optional

from e2b import AsyncSandbox

REMOTE_APP_DIR = "/home/user/app"


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


def _pick_entry(py_files: list[str], preferred: tuple[str, ...]) -> Optional[str]:
    lower = {f.lower(): f for f in py_files}
    for name in preferred:
        if name in lower:
            return lower[name]
    return py_files[0] if py_files else None


def detect_run_config(
    files: dict[str, str],
) -> tuple[str, Optional[str], str, Optional[int]]:
    """Heuristically infer (kind, install_cmd, start_cmd, port) from the file tree."""
    names = list(files.keys())
    lower = {n.lower() for n in names}

    # Node web app
    if "package.json" in lower:
        pkg = files.get("package.json", "") + files.get("package.JSON", "")
        start = "npm run dev" if '"dev"' in pkg else "npm start"
        return "web", "npm install", start, 3000

    py_files = [n for n in names if n.endswith(".py")]
    install = "pip install -r requirements.txt" if "requirements.txt" in lower else None
    joined = "\n".join(files.get(n, "") for n in py_files).lower()

    web_frameworks = ("flask", "fastapi", "uvicorn", "gunicorn", "http.server", "aiohttp", "starlette")
    if any(fw in joined for fw in web_frameworks):
        entry = _pick_entry(py_files, ("app.py", "main.py", "server.py", "wsgi.py")) or "app.py"
        if "flask" in joined:
            return "web", install, f"flask --app {entry[:-3]} run --host 0.0.0.0 --port 5000", 5000
        if "fastapi" in joined or "uvicorn" in joined or "starlette" in joined:
            module = entry[:-3].replace("/", ".")
            return "web", install, f"uvicorn {module}:app --host 0.0.0.0 --port 8000", 8000
        return "web", install, f"python {entry}", 8000

    # CLI / script
    entry = _pick_entry(py_files, ("main.py", "app.py"))
    start = f"python {entry}" if entry else "echo 'No entry point found'"
    return "script", install, start, None


async def run_app(files: dict[str, str]) -> RunResult:
    kind, install_cmd, start_cmd, port = detect_run_config(files)

    sbx = await AsyncSandbox.create(timeout=get_timeout())
    _active[sbx.sandbox_id] = sbx
    try:
        for path, content in files.items():
            await sbx.files.write(f"{REMOTE_APP_DIR}/{path}", content)

        if install_cmd:
            await sbx.commands.run(install_cmd, cwd=REMOTE_APP_DIR, timeout=300)

        if kind == "web":
            await sbx.commands.run(start_cmd, cwd=REMOTE_APP_DIR, background=True)
            preview_url = f"https://{sbx.get_host(port)}"
            return RunResult(sbx.sandbox_id, "web", preview_url, None, port)

        # script: run to completion, capture output, then release the sandbox
        result = await sbx.commands.run(start_cmd, cwd=REMOTE_APP_DIR, timeout=60)
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
