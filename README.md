# mcptax

Measure the hidden token tax of MCP tool schemas *before* you connect those
servers. Every active MCP server injects its tool names, descriptions, and
parameter schemas on every turn — including the first one, before you have
typed a prompt.

Token counts use a documented approximation: `ceil(utf-8 bytes / 4)`. No
API key is required, and the number is deterministic.

## Install

Python 3.10 or later.

From a checkout:

```bash
python3 -m pip install .
python3 -m pip install -e ".[dev]"  # optional, for tests
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

## Limits

- Token counts are an approximation: `ceil(utf-8 bytes / 4)`. They are deterministic and require no API key, but they are not a vendor tokenizer.
- mcptax does not connect to MCP servers. It only reads a JSON dump you already have.
- A Claude/Cursor-style `mcpServers` config with no tool schemas is listed as "config only" and is not measured.

From GitHub you can also install with:

```bash
python3 -m pip install git+https://github.com/perron/mcptax.git
```

This package is not published to PyPI.

## License

MIT. See `LICENSE`. Please read `SECURITY.md` before filing a vulnerability report.
