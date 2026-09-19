#!/usr/bin/env python3
"""Stamp Memory Vault gates onto plow-seed/config.yaml.

plow-init seeds an absent home from /opt/hermes/plow-seed/config.yaml and
rewrites seed-owned keys every boot. COPY of runtime/config.yaml into
/var/lib/hermes is shadowed by the agent-home volume, so holographic
memory, Latch, group sessions and the toolset-minus-web have to live on
the seed or a 1-click / recreate boots the generic Plow assistant.
"""

from __future__ import annotations

import sys


def _progress_token(value):
    """YAML 1.1 loads a bare `off` as False; Hermes wants the string `off`."""
    if value is False:
        return "off"
    if isinstance(value, str) and value.strip().lower() in {"off", "false", "no", "0"}:
        return "off"
    return value


def overlay_display(seed: dict, ours: dict) -> dict:
    seed_disp = dict(seed.get("display") or {})
    ours_disp = dict(ours.get("display") or {})
    if not ours_disp:
        return seed
    seed_plats = dict(seed_disp.get("platforms") or {})
    ours_plats = dict(ours_disp.get("platforms") or {})
    seed_pc = dict(seed_plats.get("plow_chat") or {})
    ours_pc = dict(ours_plats.get("plow_chat") or {})
    merged_pc = {**seed_pc, **ours_pc}
    merged = {**seed_disp, **ours_disp}
    for key in ("tool_progress", "live_status"):
        if key in merged:
            merged[key] = _progress_token(merged[key])
        if key in merged_pc:
            merged_pc[key] = _progress_token(merged_pc[key])
    merged["platforms"] = {**seed_plats, **ours_plats, "plow_chat": merged_pc}
    seed["display"] = merged
    return seed


def overlay(seed: dict, ours: dict) -> dict:
    for key in ("_config_version", "group_sessions_per_user", "memory", "platform_toolsets"):
        if key in ours:
            seed[key] = ours[key]
    overlay_display(seed, ours)
    seed_mcp = dict(seed.get("mcp_servers") or {})
    ours_mcp = dict(ours.get("mcp_servers") or {})
    seed["mcp_servers"] = {**seed_mcp, **ours_mcp}
    seed_plugins = dict(seed.get("plugins") or {})
    ours_plugins = dict(ours.get("plugins") or {})
    enabled = list(seed_plugins.get("enabled") or [])
    for name in ours_plugins.get("enabled") or []:
        if name not in enabled:
            enabled.append(name)
    if enabled:
        seed_plugins["enabled"] = enabled
    seed_plugins["entries"] = {
        **dict(seed_plugins.get("entries") or {}),
        **dict(ours_plugins.get("entries") or {}),
    }
    for key, value in ours_plugins.items():
        if key in ("enabled", "entries"):
            continue
        seed_plugins[key] = value
    seed["plugins"] = seed_plugins
    return seed


def _require(seed: dict) -> None:
    memory = seed.get("memory") or {}
    if memory.get("provider") != "holographic":
        raise SystemExit("refusing: seed memory.provider is not holographic")
    mcp = seed.get("mcp_servers") or {}
    if "latch" not in mcp:
        raise SystemExit("refusing: seed mcp_servers is missing latch")
    if seed.get("group_sessions_per_user") is not False:
        raise SystemExit("refusing: seed group_sessions_per_user is not false")
    disp = seed.get("display") or {}
    pc = (disp.get("platforms") or {}).get("plow_chat") or {}
    if disp.get("interim_assistant_messages") is not False:
        raise SystemExit("refusing: seed display.interim_assistant_messages is not false")
    if _progress_token(disp.get("tool_progress")) != "off":
        raise SystemExit("refusing: seed display.tool_progress is not off")
    if disp.get("long_running_notifications") is not False:
        raise SystemExit("refusing: seed display.long_running_notifications is not false")
    if pc.get("interim_assistant_messages") is not False:
        raise SystemExit("refusing: seed plow_chat.interim_assistant_messages is not false")
    if _progress_token(pc.get("tool_progress")) != "off":
        raise SystemExit("refusing: seed plow_chat.tool_progress is not off")
    if pc.get("long_running_notifications") is not False:
        raise SystemExit("refusing: seed plow_chat.long_running_notifications is not false")
    toolsets = seed.get("platform_toolsets") or {}
    for name, tools in toolsets.items():
        lowered = {str(item).strip().lower() for item in tools or []}
        for banned in ("web", "browser", "search"):
            if banned in lowered:
                raise SystemExit(f"refusing: platform_toolsets.{name} still lists {banned}")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        raise SystemExit("usage: merge_mv_seed_config.py <seed.yaml> <runtime.yaml>")
    seed_path, ours_path = argv
    import yaml

    with open(seed_path) as handle:
        seed = yaml.safe_load(handle) or {}
    with open(ours_path) as handle:
        ours = yaml.safe_load(handle) or {}
    overlay(seed, ours)
    _require(seed)
    with open(seed_path, "w") as handle:
        yaml.safe_dump(seed, handle, sort_keys=False)


if __name__ == "__main__":
    main()
