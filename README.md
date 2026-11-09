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

## 30-second quick start

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

Sample output from that exact example:

```
$ mcptax tools-tax.json --window 200000
estimator: ceil(utf8_bytes / 4)
window: 200000 tokens
server	tools	tokens	% window
github	1	69	0.03%
  create_issue	69
total	69	0.03% of window
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

## Use it with your agent

You can point a coding agent at this repository and ask it to use the tool, adapt it, or write a small tool in the same style. That works with Claude Code, Codex, Cursor, Grok Bot, and anything else that can clone a git repo and run a Python CLI.

A short prompt you can paste:

> Clone https://github.com/perron/mcptax, install it, and measure the token tax of the MCP tool dump at ./tools.json against a 200000-token window. Tell me which tools are the most expensive.

If you want a new tool in this style, say so explicitly: one job, standard-library Python, pytest first, no API key, and an honest Limits section.

## Contributing / how you can help

Bug reports, tight tests, and small honest features are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to run the suite and for pull request guidelines.

Good first issues:

- Pretty-print the table when stdout is a TTY, keep the current text format otherwise.
- Add a `--compare FILE` that diffs two dumps and shows which tools grew.
- Document how to capture a `tools/list` dump from a popular MCP client.

If you are unsure whether an idea fits, open an issue before writing a large patch.

## License

MIT. See `LICENSE`. Please read `SECURITY.md` before filing a vulnerability report. Agents should also read `AGENTS.md`.
