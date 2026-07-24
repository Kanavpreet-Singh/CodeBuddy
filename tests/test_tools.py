import pathlib
import shutil
import tempfile

import pytest

from agent.tools import read_file, set_project_root, write_file


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
