from dataclasses import replace

import pytest

from agent.registry import AgentProfile, AgentRegistry, AgentRegistryError


def test_rejected_disabled_default_preserves_routing(tmp_path):
    original = AgentProfile(id="main", name="Original", workspace=str(tmp_path / "main"))
    registry = AgentRegistry([original], "main")
    with pytest.raises(AgentRegistryError, match="disabled"):
        registry.upsert(replace(original, name="Rejected", enabled=False))
    assert registry.get_addressed("default") == original
    assert registry.list() == [original]


def test_valid_default_update_is_applied(tmp_path):
    original = AgentProfile(id="main", name="Original", workspace=str(tmp_path / "main"))
    registry = AgentRegistry([original], "main")
    updated = replace(original, name="Updated")
    registry.upsert(updated)
    assert registry.get_addressed("default") == updated


def test_nondefault_can_be_disabled(tmp_path):
    main = AgentProfile(id="main", name="Main", workspace=str(tmp_path / "main"))
    other = AgentProfile(id="other", name="Other", workspace=str(tmp_path / "other"))
    registry = AgentRegistry([main, other], "main")
    updated = replace(other, enabled=False)
    registry.upsert(updated)
    assert registry.get("other", require_enabled=False) == updated
    assert registry.get_addressed("default") == main
