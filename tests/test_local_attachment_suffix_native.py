"""Native local attachment consumers must not parse filenames as URL paths."""

import base64
import json
import os
from pathlib import Path

import pytest

from channel.feishu.feishu_message import FeishuMessage
from common.utils import get_path_suffix


def file_message(name, key="owned-file"):
    return FeishuMessage({
        "app_id": "owned-app",
        "sender": {"sender_id": {"open_id": "owned-user"}},
        "message": {
            "message_id": "owned-msg", "create_time": "1", "message_type": "file",
            "content": json.dumps({"file_key": key, "file_name": name}),
        },
    }, access_token="owned-unused")


@pytest.mark.parametrize("name", ["board.docx", "board#v2.docx", "board?v2.docx", "board%v2.docx"])
def test_native_feishu_file_event_retains_original_format_suffix(name):
    # File downloads are deferred by this real constructor. No Feishu service
    # request is made; the staged format is the property under test.
    message = file_message(name)
    assert Path(message.content).suffix == Path(name).suffix


@pytest.mark.parametrize("name", ["board.docx", "board#v2.docx", "board?v2.docx", "board%v2.docx"])
def test_generated_word_attachment_is_readable_from_native_staged_path(name):
    Document = pytest.importorskip("docx").Document
    from agent.tools.read.read import Read

    message = file_message(name, "owned-docx")
    document = Document()
    document.add_paragraph("Owned native Word attachment text")
    document.save(message.content)
    result = Read().execute({"path": message.content})
    assert result.status == "success", result.result
    assert "Owned native Word attachment text" in str(result.result)


@pytest.mark.parametrize("name", ["photo.png", "photo#v2.png", "photo?v2.png", "photo%v2.png"])
def test_linkai_native_png_payload_uses_the_local_filename_suffix(name, tmp_path):
    if os.name == "nt" and "?" in name:
        pytest.skip("Windows does not admit '?' in a native filename")
    Image = pytest.importorskip("PIL.Image")
    from models.linkai.link_ai_bot import LinkAIBot

    path = tmp_path / name
    Image.new("RGB", (2, 2), "blue").save(path, format="PNG")
    message = LinkAIBot()._build_vision_msg("owned question", str(path))
    url = message[0]["content"][1]["image_url"]["url"]
    assert base64.b64decode(url.split(",", 1)[1]) == path.read_bytes()
    assert url.startswith("data:image/png;base64,")


@pytest.mark.parametrize("url", [
    "https://owned.invalid/board.png?token=owned",
    "https://owned.invalid/board.png#fragment",
])
def test_url_suffix_query_and_fragment_controls_remain_unchanged(url):
    assert get_path_suffix(url) == "png"
