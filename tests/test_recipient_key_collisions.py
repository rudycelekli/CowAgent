"""Recipient identities must stay distinct across ambiguous separator pairs."""

import json

import pytest

from agent.tools.scheduler.recipient_store import RecipientStore


def test_colon_pairs_persist_as_distinct_recipients(tmp_path):
    path = tmp_path / "recipients.json"
    store = RecipientStore(str(path))
    store.remember("feishu", "room:user", instance_id="bot", name="First")
    store.remember("feishu", "user", instance_id="bot:room", name="Second")

    reloaded = RecipientStore(str(path))
    assert reloaded.get("bot", "room:user")["name"] == "First"
    assert reloaded.get("bot:room", "user")["name"] == "Second"
    assert len(reloaded.list()) == 2


def test_legacy_joined_key_does_not_resolve_another_identity(tmp_path):
    path = tmp_path / "recipients.json"
    path.write_text(json.dumps({"version": 1, "recipients": {
        "bot:room:user": {"channel_type": "feishu", "instance_id": "bot:room",
                          "receiver": "user", "name": "Existing"},
    }}))
    store = RecipientStore(str(path))
    assert store.get("bot", "room:user") is None
    assert store.get("bot:room", "user")["name"] == "Existing"

    store.remember("feishu", "room:user", instance_id="bot", name="New")
    assert RecipientStore(str(path)).get("bot:room", "user")["name"] == "Existing"
    assert len(store.list()) == 2


def test_percent_escape_literals_stay_distinct(tmp_path):
    store = RecipientStore(str(tmp_path / "recipients.json"))
    store.remember("feishu", "room:user", instance_id="bot", name="Colon")
    store.remember("feishu", "room%3Auser", instance_id="bot", name="Literal")
    assert store.get("bot", "room:user")["name"] == "Colon"
    assert store.get("bot", "room%3Auser")["name"] == "Literal"


@pytest.mark.parametrize("unknown", [
    {"note": "retained historical metadata"},
    "unrecognized historical entry",
    {"channel_type": "feishu", "receiver": None},
])
def test_unknown_legacy_entries_do_not_break_valid_lookups_or_saves(tmp_path, unknown):
    path = tmp_path / "recipients.json"
    valid = {"channel_type": "feishu", "receiver": "room:user", "name": "Existing",
             "annotation": "keep this field"}
    path.write_text(json.dumps({"version": 1, "recipients": {
        "feishu:room:user": valid, "historical-metadata": unknown,
    }}))
    original = path.read_bytes()
    store = RecipientStore(str(path))

    assert store.get("feishu", "room:user")["name"] == "Existing"
    assert path.read_bytes() == original  # migration on read stays read-only
    store.remember("feishu", "new-user", name="New")

    persisted = json.loads(path.read_text())["recipients"]
    assert persisted["historical-metadata"] == unknown
    assert persisted["feishu:room%3Auser"] == valid
    assert RecipientStore(str(path)).get("feishu", "new-user")["name"] == "New"
