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


@pytest.mark.parametrize("filename", [
    " report.txt",
    pytest.param("report.txt ", marks=pytest.mark.skipif(os.name == "nt", reason="Win32 trims trailing filename spaces")),
])
def test_send_selects_literal_local_file(tmp_path, filename):
    from agent.tools.send.send import Send

    target = tmp_path / filename
    neighbor = tmp_path / "report.txt"
    target.write_text("TARGET CONTENT", encoding="utf-8")
    neighbor.write_text("OTHER", encoding="utf-8")
    result = Send({"cwd": str(tmp_path)}).execute({"path": filename})
    assert result.status == "success"
    assert result.result["path"] == str(target)
    assert result.result["file_name"] == filename
    assert result.result["size"] == target.stat().st_size
    assert target.read_text(encoding="utf-8") == "TARGET CONTENT"
    assert neighbor.read_text(encoding="utf-8") == "OTHER"


def test_send_url_whitespace_still_normalizes_without_fetch(tmp_path):
    from agent.tools.send.send import Send

    result = Send({"cwd": str(tmp_path)}).execute({"path": "  https://example.com/control.png  "})
    assert result.status == "success"
    assert result.result["url"] == "https://example.com/control.png"


@pytest.mark.parametrize("path", ["", "  "])
def test_send_still_rejects_blank_path(tmp_path, path):
    from agent.tools.send.send import Send

    result = Send({"cwd": str(tmp_path)}).execute({"path": path})
    assert result.status == "error"
    assert "path parameter is required" in result.result
    assert list(tmp_path.iterdir()) == []


def test_vision_sends_literal_local_image_bytes(tmp_path, monkeypatch):
    import base64
    import http.server
    import io
    import json
    import threading

    from PIL import Image

    from agent.tools.vision.vision import Vision
    from config import conf

    target = tmp_path / " image.png"
    neighbor = tmp_path / "image.png"
    Image.new("RGB", (3, 3), "blue").save(target)
    Image.new("RGB", (3, 3), "red").save(neighbor)
    captured = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            uri = request["messages"][0]["content"][1]["image_url"]["url"]
            captured.append(base64.b64decode(uri.split(",", 1)[1]))
            body = json.dumps({"choices": [{"message": {"content": "owned wire fixture"}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    monkeypatch.setitem(conf(), "custom_providers", [{
        "id": "owned-path-test", "name": "Owned wire fixture", "api_key": "owned-unused-key",
        "api_base": f"http://127.0.0.1:{server.server_port}/v1", "model": "owned",
    }])
    monkeypatch.setitem(conf(), "tools", {"vision": {"provider": "custom:owned-path-test", "model": "owned"}})
    try:
        tool = Vision({"cwd": str(tmp_path)})
        for name, color in [("image.png", (255, 0, 0)), (" image.png", (0, 0, 255))]:
            result = tool.execute({"image": name, "question": "owned wire fidelity check"})
            assert result.status == "success", result.result
            with Image.open(io.BytesIO(captured[-1])) as sent:
                assert sent.getpixel((0, 0)) == color
        for blank in ["", "  "]:
            result = tool.execute({"image": blank, "question": "owned check"})
            assert result.status == "error"
            assert "'image' parameter is required" in result.result
        assert len(captured) == 2
    finally:
        server.shutdown()
        server.server_close()
        worker.join(2)
