import pytest

from server.sandbox import UnrunnableAppError, detect_run_config


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
