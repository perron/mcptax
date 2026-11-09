# mcptax

Measure the hidden token tax of MCP tool schemas *before* you connect those
servers. Every active MCP server injects its tool names, descriptions, and
parameter schemas on every turn — including the first one, before you have
typed a prompt.

Token counts use a documented approximation: `ceil(utf-8 bytes / 4)`. No
API key is required, and the number is deterministic.

## Install

```bash
python3 -m pip install -e .
mcptax tools.json
```

## 30-second example

```bash
cat > tools.json << 'EOF'
{
  "servers": [
    {
      "name": "github",
      "tools": [
        {
          "name": "create_issue",
          "description": "Create an issue. Needs owner, repo, title, body.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "owner": {"type": "string"},
              "repo": {"type": "string"},
              "title": {"type": "string"},
              "body": {"type": "string"}
            },
            "required": ["owner", "repo", "title"]
          }
        }
      ]
    }
  ]
}
EOF

mcptax tools.json --window 200000
```

You can also pass a Claude/Cursor-style `{"mcpServers": {...}}` config. If a
server has no schemas, mcptax lists it as "config only" and tells you to
export a `tools/list` dump.

## Credit

Motivated by public reports in late Oct and early Nov 2026 that MCP schemas
are a per-turn context tax. Original code; no source was copied from any
MCP host or linter.
