"""Native file tools must use the requested path, not a trimmed neighbor."""

import os

import pytest

from agent.tools.edit.edit import Edit
from agent.tools.ls.ls import Ls
from agent.tools.read.read import Read
from agent.tools.write.write import Write


@pytest.mark.parametrize("filename", [
    " report",
    pytest.param("report ", marks=pytest.mark.skipif(os.name == "nt", reason="Win32 trims trailing filename spaces")),
])
@pytest.mark.parametrize("absolute", [False, True])
def test_file_tools_preserve_literal_path_components(tmp_path, filename, absolute):
    target = tmp_path / filename
    neighbor = tmp_path / "report"
    target.write_text("TARGET", encoding="utf-8")
    neighbor.write_text("NEIGHBOR", encoding="utf-8")
    argument = str(target) if absolute else filename
    read = Read({"cwd": str(tmp_path)}).execute({"path": argument})
    assert read.status == "success"
    assert "TARGET" in read.result["content"]
    assert "NEIGHBOR" not in read.result["content"]

    write = Write({"cwd": str(tmp_path)}).execute({"path": argument, "content": "REPLACED"})
    assert write.status == "success"
    assert target.read_text(encoding="utf-8") == "REPLACED"
    assert neighbor.read_text(encoding="utf-8") == "NEIGHBOR"

    # Both files contain the same match, so a redirected edit could otherwise
    # appear successful even though it changed the wrong file.
    neighbor.write_text("REPLACED", encoding="utf-8")
    edit = Edit({"cwd": str(tmp_path)}).execute({
        "path": argument, "oldText": "REPLACED", "newText": "EDITED",
    })
    assert edit.status == "success"
    assert target.read_text(encoding="utf-8") == "EDITED"
    assert neighbor.read_text(encoding="utf-8") == "REPLACED"


@pytest.mark.parametrize("dirname", [
    " folder",
    pytest.param("folder ", marks=pytest.mark.skipif(os.name == "nt", reason="Win32 trims trailing filename spaces")),
])
def test_ls_preserves_literal_directory_name(tmp_path, dirname):
    target = tmp_path / dirname
    neighbor = tmp_path / "folder"
    target.mkdir()
    neighbor.mkdir()
    (target / "target.txt").touch()
    (neighbor / "neighbor.txt").touch()
    result = Ls({"cwd": str(tmp_path)}).execute({"path": dirname})
    assert result.status == "success"
    assert result.result["output"] == "target.txt"


@pytest.mark.parametrize("tool", [Read, Write, Edit])
@pytest.mark.parametrize("path", ["", "  "])
def test_required_file_paths_still_reject_blank_values(tmp_path, tool, path):
    result = tool({"cwd": str(tmp_path)}).execute({
        "path": path, "content": "owned", "oldText": "owned", "newText": "new",
    })
    assert result.status == "error"
    assert "path parameter is required" in result.result
    assert list(tmp_path.iterdir()) == []


def test_ordinary_paths_and_default_ls_still_work(tmp_path):
    result = Write({"cwd": str(tmp_path)}).execute({"path": "plain.txt", "content": "hello"})
    assert result.status == "success"
    result = Read({"cwd": str(tmp_path)}).execute({"location": "plain.txt"})
    assert result.status == "success"
    assert "hello" in result.result["content"]
    result = Ls({"cwd": str(tmp_path)}).execute({})
    assert result.status == "success"
    assert result.result["output"] == "plain.txt"
