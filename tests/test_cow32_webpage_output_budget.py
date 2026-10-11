from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

@contextmanager
def serve(body, content_type="text/plain; charset=utf-8", length=None, chunks=None, delay=0):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            if length is not None:
                self.send_header("Content-Length", str(length))
            self.end_headers()
            try:
                for chunk in (chunks if chunks is not None else [body]):
                    if delay:
                        import time
                        time.sleep(delay)
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

import pytest
from agent.tools.web_fetch.web_fetch import WebFetch
from agent.tools.utils.truncate import DEFAULT_MAX_BYTES

def test_native_large_page_returns_bounded_text(tmp_path, monkeypatch):
    monkeypatch.setenv("WEB_SECURITY_SSRF_PROTECTION", "0")
    body = ("<p>" + "known content " * 30 + "</p>") * 300
    with serve(body.encode(), content_type="text/html; charset=utf-8") as url:
        result = WebFetch({"cwd": str(tmp_path)}).execute({"url": url + "/page"})
    assert result.status == "success", result.result
    assert "known content" in result.result
    assert "Content truncated" in result.result
    assert len(result.result.encode()) <= DEFAULT_MAX_BYTES

@pytest.mark.parametrize("body", ["Readable body", "<p>" + "large body " * 9000 + "</p>"])
def test_native_huge_title_and_body_share_output_budget(tmp_path, monkeypatch, body):
    monkeypatch.setenv("WEB_SECURITY_SSRF_PROTECTION", "0")
    html = "<title>" + "🐄" * 30000 + "</title>" + body
    with serve(html.encode(), content_type="text/html; charset=utf-8") as url:
        result = WebFetch({"cwd": str(tmp_path)}).execute({"url": url + "/page"})
    assert result.status == "success", result.result
    assert "Content truncated" in result.result
    assert len(result.result.encode()) <= DEFAULT_MAX_BYTES

def test_native_small_page_has_unchanged_output(tmp_path, monkeypatch):
    monkeypatch.setenv("WEB_SECURITY_SSRF_PROTECTION", "0")
    with serve(b"<title>Small</title><p>Readable</p>", content_type="text/html") as url:
        result = WebFetch({"cwd": str(tmp_path)}).execute({"url": url + "/page"})
    assert result.result == "Title: Small\n\nContent:\nSmall\nReadable"
