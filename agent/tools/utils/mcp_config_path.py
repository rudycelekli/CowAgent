"""Protect auto-loaded MCP configuration from agent file-tool writes."""

import os


def is_mcp_config_path(path: str) -> bool:
    """Cover shared/per-agent mcp.json paths and symlinks to either one."""
    return any(
        os.path.basename(candidate).casefold() == "mcp.json"
        for candidate in (os.path.normpath(path), os.path.realpath(path))
    )
