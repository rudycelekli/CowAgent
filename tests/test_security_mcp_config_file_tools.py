"""File tools must not modify auto-loaded MCP server configuration."""

import os

import pytest

from agent.tools.edit.edit import Edit
from agent.tools.write.write import Write


def test_write_rejects_mcp_config_in_any_workspace(tmp_path):
    config = {"cwd": str(tmp_path)}
    for path in ("mcp.json", str(tmp_path / "other-agent" / "mcp.json")):
        result = Write(config).execute({"path": path, "content": '{"mcpServers": {}}'})
        assert result.status == "error"
        assert not (tmp_path / path).exists()


def test_edit_rejects_existing_mcp_config(tmp_path):
    target = tmp_path / "mcp.json"
    original = '{"mcpServers": {}}\n'
    target.write_text(original)

    result = Edit({"cwd": str(tmp_path)}).execute(
        {"path": str(target), "oldText": "mcpServers", "newText": "mcp_servers"}
    )

    assert result.status == "error"
    assert target.read_text() == original


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
@pytest.mark.parametrize("tool,args", [
    (Write, {"content": '{"mcpServers": {}}'}),
    (Edit, {"oldText": "mcpServers", "newText": "mcp_servers"}),
])
def test_file_tools_reject_symlink_to_mcp_config(tmp_path, tool, args):
    target = tmp_path / "mcp.json"
    original = '{"mcpServers": {}}\n'
    target.write_text(original)
    alias = tmp_path / "ordinary.json"
    try:
        alias.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable")

    result = tool({"cwd": str(tmp_path)}).execute({"path": str(alias), **args})

    assert result.status == "error"
    assert target.read_text() == original


def test_unrelated_json_remains_editable(tmp_path):
    target = tmp_path / "notes.json"
    assert Write({"cwd": str(tmp_path)}).execute(
        {"path": str(target), "content": '{"value": 1}\n'}
    ).status == "success"
    assert Edit({"cwd": str(tmp_path)}).execute(
        {"path": str(target), "oldText": "1", "newText": "2"}
    ).status == "success"
    assert target.read_text() == '{"value": 2}\n'
