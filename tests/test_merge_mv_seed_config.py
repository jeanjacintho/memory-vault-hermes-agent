"""Home COPY of config.yaml is shadowed; vault gates have to land on the seed."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

QUIET = {
    "tool_progress": "off",
    "interim_assistant_messages": False,
    "long_running_notifications": False,
    "busy_ack_detail": False,
    "live_status": "off",
    "platforms": {
        "plow_chat": {
            "tool_progress": "off",
            "interim_assistant_messages": False,
            "long_running_notifications": False,
            "busy_ack_detail": False,
            "live_status": "off",
        }
    },
}


def _load():
    path = ROOT / "image/merge_mv_seed_config.py"
    spec = importlib.util.spec_from_file_location("merge_mv_seed", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_overlay_keeps_relay_and_stamps_vault_gates():
    merge = _load()
    seed = {
        "mcp_servers": {"plow": {"url": "stdio"}},
        "plugins": {"enabled": ["other"], "entries": {"other": {}}},
        "display": {"busy_ack_enabled": False},
    }
    ours = {
        "_config_version": 39,
        "group_sessions_per_user": False,
        "context_file_max_chars": 40000,
        "memory": {"provider": "holographic"},
        "mcp_servers": {"latch": {"url": "https://api.plow.co/v1/relay/devices/${DOMO_DEVICE_UID}/mcp"}},
        "plugins": {
            "enabled": ["plow-chat-platform"],
            "entries": {"plow-chat-platform": {"allow_tool_override": False}},
            "hermes-memory-store": {"db_path": "${HERMES_HOME}/memory_store.db"},
        },
        "agent": {"disabled_toolsets": ["web", "search", "browser"]},
        "display": QUIET,
    }
    out = merge.overlay(seed, ours)
    assert out["mcp_servers"]["plow"]["url"] == "stdio"
    assert "latch" in out["mcp_servers"]
    assert out["memory"]["provider"] == "holographic"
    assert out["group_sessions_per_user"] is False
    assert out["_config_version"] == 39
    assert "plow-chat-platform" in out["plugins"]["enabled"]
    assert "other" in out["plugins"]["enabled"]
    assert out["plugins"]["hermes-memory-store"]["db_path"] == "${HERMES_HOME}/memory_store.db"
    assert out["display"]["busy_ack_enabled"] is False
    assert out["display"]["interim_assistant_messages"] is False
    merge._require(out)


def test_overlay_unions_disabled_toolsets_with_the_seed():
    merge = _load()
    out = merge.overlay(
        {"agent": {"disabled_toolsets": ["clarify"], "api_max_retries": 3}},
        {"agent": {"disabled_toolsets": ["web", "search", "browser"]}},
    )
    assert out["agent"]["api_max_retries"] == 3
    assert out["agent"]["disabled_toolsets"] == [
        "clarify",
        "web",
        "search",
        "browser",
    ]


def test_overlay_turns_off_loud_plow_chat_defaults():
    merge = _load()
    out = merge.overlay_display(
        {"display": {"memory_notifications": "on", "interim_assistant_messages": True}},
        {"display": QUIET},
    )
    disp = out["display"]
    pc = disp["platforms"]["plow_chat"]
    assert disp["memory_notifications"] == "on"
    assert disp["interim_assistant_messages"] is False
    assert disp["tool_progress"] == "off"
    assert pc["interim_assistant_messages"] is False
    assert pc["tool_progress"] == "off"


def test_require_rejects_web_in_the_toolset():
    merge = _load()
    seed = {
        "memory": {"provider": "holographic"},
        "mcp_servers": {"latch": {}},
        "group_sessions_per_user": False,
        "context_file_max_chars": 40000,
        "display": QUIET,
        "agent": {"disabled_toolsets": ["search", "browser"]},
    }
    with pytest.raises(SystemExit, match="web"):
        merge._require(seed)
