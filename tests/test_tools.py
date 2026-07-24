import pathlib
import shutil
import tempfile

import pytest

from agent.tools import edit_file, read_file, set_project_root, write_file


@pytest.fixture
def project_root():
    d = pathlib.Path(tempfile.mkdtemp())
    set_project_root(d)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_write_and_read_roundtrip(project_root):
    write_file.invoke({"path": "app.py", "content": "print('hi')"})
    assert read_file.invoke({"path": "app.py"}) == "print('hi')"


def test_write_creates_nested_dirs(project_root):
    write_file.invoke({"path": "a/b/c.txt", "content": "x"})
    assert (project_root / "a" / "b" / "c.txt").read_text() == "x"


def test_write_heals_stray_file_blocking_dir(project_root):
    # The coder sometimes writes a bare file where a directory is needed.
    (project_root / "templates").write_text("")
    assert (project_root / "templates").is_file()

    write_file.invoke({"path": "templates/index.html", "content": "<h1>hi</h1>"})

    assert (project_root / "templates").is_dir()
    assert read_file.invoke({"path": "templates/index.html"}) == "<h1>hi</h1>"


def test_write_outside_root_is_blocked(project_root):
    with pytest.raises(ValueError):
        write_file.invoke({"path": "../escape.txt", "content": "nope"})


def test_edit_file_replaces_only_the_matched_text(project_root):
    write_file.invoke(
        {
            "path": "app.py",
            "content": "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/health')\ndef health():\n    return 'ok'\n",
        }
    )

    result = edit_file.invoke(
        {
            "path": "app.py",
            "old_string": "@app.route('/health')\ndef health():\n    return 'ok'\n",
            "new_string": "@app.route('/')\ndef index():\n    return 'home'\n\n@app.route('/health')\ndef health():\n    return 'ok'\n",
        }
    )

    assert result.startswith("EDITED:")
    content = read_file.invoke({"path": "app.py"})
    assert "from flask import Flask" in content  # untouched code preserved
    assert "def index():" in content
    assert "def health():" in content  # original route preserved too


def test_edit_file_missing_old_string_errors(project_root):
    write_file.invoke({"path": "app.py", "content": "x = 1\n"})
    result = edit_file.invoke({"path": "app.py", "old_string": "y = 2", "new_string": "y = 3"})
    assert result.startswith("ERROR")
    assert read_file.invoke({"path": "app.py"}) == "x = 1\n"  # unchanged


def test_edit_file_ambiguous_match_errors(project_root):
    write_file.invoke({"path": "app.py", "content": "x = 1\nx = 1\n"})
    result = edit_file.invoke({"path": "app.py", "old_string": "x = 1", "new_string": "x = 2"})
    assert result.startswith("ERROR")
    assert "2 locations" in result
    assert read_file.invoke({"path": "app.py"}) == "x = 1\nx = 1\n"  # unchanged


def test_edit_file_nonexistent_file_errors(project_root):
    result = edit_file.invoke({"path": "missing.py", "old_string": "a", "new_string": "b"})
    assert result.startswith("ERROR")
