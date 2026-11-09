"""Measure the hidden token tax of MCP tool schemas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

__version__ = "0.1.1"

DEFAULT_WINDOW = 200_000


def estimate_tokens(text: str) -> int:
    """Approximate tokens as ceil(utf-8 bytes / 4). Documented, deterministic, no API key."""
    if not text:
        return 0
    return max(1, (len(text.encode("utf-8")) + 3) // 4)


def tool_tax(tool: dict[str, Any]) -> dict[str, Any]:
    name = str(tool.get("name") or tool.get("tool") or "")
    description = str(tool.get("description") or "")
    schema = tool.get("inputSchema") or tool.get("input_schema") or tool.get("parameters") or {}
    payload = json.dumps({"name": name, "description": description, "inputSchema": schema}, ensure_ascii=False, separators=(",", ":"))
    tokens = estimate_tokens(payload)
    return {"name": name or "(unnamed)", "tokens": tokens, "description_tokens": estimate_tokens(description)}


def normalize_servers(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [{"name": "(list)", "tools": data, "configured_only": False}]
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object or array")
    if "servers" in data:
        servers = []
        for server in data["servers"]:
            servers.append({
                "name": server.get("name") or "(unnamed)",
                "tools": server.get("tools") or [],
                "configured_only": False,
            })
        return servers
    if "mcpServers" in data:
        servers = []
        for name, cfg in data["mcpServers"].items():
            tools = []
            if isinstance(cfg, dict):
                tools = cfg.get("tools") or []
            servers.append({
                "name": name,
                "tools": tools,
                "configured_only": not bool(tools),
                "config": cfg if isinstance(cfg, dict) else {},
            })
        return servers
    if "tools" in data:
        return [{"name": data.get("name") or "(tools)", "tools": data["tools"], "configured_only": False}]
    raise ValueError("unrecognized JSON: expected servers, mcpServers, tools, or a tool array")


def report(servers: list[dict[str, Any]], window: int) -> dict[str, Any]:
    rows = []
    total = 0
    unmeasured = 0
    for server in servers:
        tools = [tool_tax(t) for t in server.get("tools") or []]
        tokens = sum(t["tokens"] for t in tools)
        total += tokens
        if server.get("configured_only"):
            unmeasured += 1
        rows.append({
            "server": server["name"],
            "tools": len(tools),
            "tokens": tokens,
            "configured_only": bool(server.get("configured_only")),
            "tool_breakdown": sorted(tools, key=lambda t: t["tokens"], reverse=True),
        })
    rows.sort(key=lambda r: r["tokens"], reverse=True)
    return {
        "window": window,
        "servers": rows,
        "total_tokens": total,
        "percent_of_window": round((total / window) * 100, 2) if window else 0.0,
        "configured_only_servers": unmeasured,
        "estimator": "ceil(utf8_bytes / 4)",
    }


def render(result: dict[str, Any]) -> str:
    lines = [
        f"estimator: {result['estimator']}",
        f"window: {result['window']} tokens",
        "server\ttools\ttokens\t% window",
    ]
    for row in result["servers"]:
        pct = (row["tokens"] / result["window"] * 100) if result["window"] else 0
        note = " (config only, no schemas)" if row["configured_only"] else ""
        lines.append(f"{row['server']}\t{row['tools']}\t{row['tokens']}\t{pct:.2f}%{note}")
        for tool in row["tool_breakdown"][:5]:
            lines.append(f"  {tool['name']}\t{tool['tokens']}")
        if len(row["tool_breakdown"]) > 5:
            lines.append(f"  … {len(row['tool_breakdown']) - 5} more tools")
    lines.append(f"total\t{result['total_tokens']}\t{result['percent_of_window']}% of window")
    if result["configured_only_servers"]:
        lines.append(
            f"note: {result['configured_only_servers']} server(s) had no tool schemas. "
            "Export tools/list JSON to measure them."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mcptax",
        description="Measure the hidden token tax of MCP tool schemas before you connect them.",
    )
    parser.add_argument("input", help="JSON file of tool schemas, or '-' for stdin")
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW, help="context window size (default 200000)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--version", action="version", version=f"mcptax {__version__}")
    args = parser.parse_args(argv)
    if args.window <= 0:
        print("error: --window must be positive", file=sys.stderr)
        return 1
    if args.input == "-":
        raw = sys.stdin.read()
    else:
        path = Path(args.input)
        if not path.is_file():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw)
        servers = normalize_servers(data)
        result = report(servers, args.window)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
