import pytest

from server.sandbox import UnrunnableAppError, _ensure_flask_serves, _strip_stdlib_requirements, detect_run_config


def test_flask_app_detected_as_web():
    files = {
        "app.py": "from flask import Flask\napp = Flask(__name__)",
        "requirements.txt": "flask",
    }
    cfg = detect_run_config(files)
    assert cfg.kind == "web"
    assert cfg.port == 5000
    assert cfg.work_dir == "."
    assert cfg.install_cmd == "pip install -r requirements.txt"
    # Runs as a plain script (not `flask run`) so `if __name__ == "__main__":`
    # init code (DB setup etc.) actually executes.
    assert cfg.start_cmd == "python app.py"
    assert cfg.flask_entry == "app.py"


def test_fastapi_app_detected_as_web():
    files = {"main.py": "from fastapi import FastAPI\napp = FastAPI()"}
    cfg = detect_run_config(files)
    assert cfg.kind == "web"
    assert cfg.port == 8000
    assert "uvicorn main:app" in cfg.start_cmd


def test_cli_script_detected_as_script():
    files = {"main.py": "print('hello')"}
    cfg = detect_run_config(files)
    assert cfg.kind == "script"
    assert cfg.start_cmd == "python main.py"


def test_nested_node_server_runs_from_its_folder():
    files = {
        "server/package.json": '{"scripts": {"start": "node index.js"}, "dependencies": {"express": "^4"}}',
        "server/index.js": "const express = require('express')",
    }
    cfg = detect_run_config(files)
    assert cfg.kind == "web"
    assert cfg.work_dir == "server"
    assert cfg.start_cmd == "npm start"
    assert cfg.install_cmd == "npm install"


def test_static_site_served():
    files = {"index.html": "<h1>hi</h1>", "style.css": "body{}"}
    cfg = detect_run_config(files)
    assert cfg.kind == "web"
    assert "http.server" in cfg.start_cmd


def test_unrunnable_app_raises():
    files = {"notes.md": "# just docs", "data.csv": "a,b,c"}
    with pytest.raises(UnrunnableAppError):
        detect_run_config(files)


def test_strip_stdlib_requirements_removes_sqlite3():
    # Reproduces a real failure: pip has no distribution named "sqlite3" (it's
    # stdlib), so leaving it in requirements.txt fails the whole install.
    result = _strip_stdlib_requirements("Flask\nsqlite3\nrequests==2.31.0\n")
    lines = [l for l in result.splitlines() if l.strip()]
    assert lines == ["Flask", "requests==2.31.0"]


def test_strip_stdlib_requirements_handles_version_specifiers_and_comments():
    result = _strip_stdlib_requirements("# comment\nos\nflask>=2.0\njson==1.0\n\nuuid\n")
    lines = [l.strip() for l in result.splitlines() if l.strip() and not l.strip().startswith("#")]
    assert lines == ["flask>=2.0"]


def test_strip_stdlib_requirements_keeps_real_packages_untouched():
    original = "flask\nrequests\ngunicorn"
    assert _strip_stdlib_requirements(original) == original


def test_ensure_flask_serves_injects_host_into_bare_run_call():
    result = _ensure_flask_serves("app = Flask(__name__)\n\napp.run(debug=True)\n", 5000)
    assert 'app.run(host="0.0.0.0", port=5000, debug=True)' in result


def test_ensure_flask_serves_injects_into_empty_run_call():
    result = _ensure_flask_serves("app.run()", 5000)
    assert 'app.run(host="0.0.0.0", port=5000)' in result


def test_ensure_flask_serves_leaves_explicit_host_untouched():
    original = "app.run(host='127.0.0.1', port=3000)"
    assert _ensure_flask_serves(original, 5000) == original


def test_ensure_flask_serves_appends_run_call_when_missing():
    result = _ensure_flask_serves("app = Flask(__name__)\n", 5000)
    assert '__main__' in result
    assert 'app.run(host="0.0.0.0", port=5000)' in result
