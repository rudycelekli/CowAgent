from unittest.mock import Mock
import pytest
from models.minimax.minimax_bot import MinimaxBot


@pytest.mark.parametrize(
    "wire",
    [
        b'data:{"choices":[{"delta":{"content":"hello"}}]}\n\ndata:[DONE]\n\n',
        b'data: {"choices":\ndata: [{"delta":{"content":"hello"}}]}\n\ndata: [DONE]\n\n',
        b'\xef\xbb\xbfdata:{"choices":[{"delta":{"content":"hello"}}]}\r\rdata:[DONE]\r\r',
        'data:{"choices":[{"delta":{"content":"你好\u2028world"}}]}\r\n\r\ndata:[DONE]\r\n\r\n'.encode(),
    ],
)
def test_valid_sse_frames_are_delivered(monkeypatch, wire):
    bot = MinimaxBot.__new__(MinimaxBot)
    monkeypatch.setattr("models.minimax.minimax_bot.conf", lambda: {"minimax_api_key": "test"})
    response = Mock(status_code=200)
    response.iter_content.return_value = iter([bytes([byte]) for byte in wire])
    response.iter_lines.return_value = iter(wire.splitlines())
    monkeypatch.setattr("models.minimax.minimax_bot.requests.post", Mock(return_value=response))
    chunks = list(bot._handle_stream_response({}))
    text = "".join(c.get("choices", [{}])[0].get("delta", {}).get("content", "") for c in chunks)
    assert text == ("你好\u2028world" if "你好".encode() in wire else "hello")


def test_existing_spaced_data_frames_unchanged(monkeypatch):
    bot = MinimaxBot.__new__(MinimaxBot)
    monkeypatch.setattr("models.minimax.minimax_bot.conf", lambda: {"minimax_api_key": "test"})
    wire = b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\ndata: [DONE]\n\n'
    response = Mock(status_code=200)
    response.iter_content.return_value = iter([wire])
    response.iter_lines.return_value = iter(wire.splitlines())
    monkeypatch.setattr("models.minimax.minimax_bot.requests.post", Mock(return_value=response))
    chunks = list(bot._handle_stream_response({}))
    assert chunks[0]["choices"][0]["delta"]["content"] == "hello"
