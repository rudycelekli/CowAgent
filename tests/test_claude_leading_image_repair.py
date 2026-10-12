from copy import deepcopy
import pytest
from agent.protocol.message_utils import sanitize_claude_messages


@pytest.mark.parametrize(
    "input_block",
    [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "fixture"}},
        {"type": "document", "source": {"type": "text", "media_type": "text/plain", "data": "user document"}},
    ],
)
def test_leading_attachment_survives_orphan_result_removal(input_block):
    preserved = deepcopy(input_block)
    messages = [
        {
            "role": "user",
            "content": [input_block, {"type": "tool_result", "tool_use_id": "missing", "content": "orphan"}],
        }
    ]
    sanitize_claude_messages(messages)
    assert messages == [{"role": "user", "content": [preserved]}]
    assert sanitize_claude_messages(messages) == 0


def test_leading_result_only_message_is_still_removed():
    messages = [{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "missing", "content": "orphan"}]}]
    sanitize_claude_messages(messages)
    assert messages == []
