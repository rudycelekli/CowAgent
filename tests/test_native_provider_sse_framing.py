import importlib
from unittest.mock import Mock
import pytest

PROVIDERS = [
    ("deepseek", "deepseek_bot", "DeepSeekBot"),
    ("mimo", "mimo_bot", "MimoBot"),
    ("moonshot", "moonshot_bot", "MoonshotBot"),
    ("doubao", "doubao_bot", "DoubaoBot"),
]


def prepare(monkeypatch, provider, module, clsname, response):
    source = importlib.import_module(f"models.{provider}.{module}")
    cls = getattr(source, clsname)
    bot = cls.__new__(cls)
    bot.args = {}
    monkeypatch.setattr(source, "conf", lambda: {})
    monkeypatch.setattr(source.requests, "post", Mock(return_value=response))
    return bot


@pytest.mark.parametrize("provider,module,clsname", PROVIDERS)
@pytest.mark.parametrize(
    "wire",
    [
        b'data:{"choices":[{"delta":{"content":"hello"}}]}\n\ndata:[DONE]\n\n',
        b'data: {"choices":\ndata: [{"delta":{"content":"hello"}}]}\n\ndata: [DONE]\n\n',
        b'\xef\xbb\xbfdata:{"choices":[{"delta":{"content":"hello"}}]}\r\rdata:[DONE]\r\r',
    ],
)
def test_native_stream_decodes_complete_sse_events(monkeypatch, provider, module, clsname, wire):
    response = Mock(status_code=200)
    response.iter_lines.return_value = iter(wire.splitlines())
    response.iter_content.return_value = iter([bytes([b]) for b in wire])
    bot = prepare(monkeypatch, provider, module, clsname, response)
    chunks = list(bot._handle_stream_response({}))
    text = "".join(c.get("choices", [{}])[0].get("delta", {}).get("content", "") for c in chunks)
    assert text == "hello"
