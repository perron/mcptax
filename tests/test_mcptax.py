import json
from pathlib import Path
import mcptax.cli as mt


def test_tool_list_tax(tmp_path, capsys):
    payload = {
        "servers": [
            {
                "name": "github",
                "tools": [
                    {
                        "name": "create_issue",
                        "description": "Create an issue in a repository. Needs owner, repo, title, body.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "owner": {"type": "string"},
                                "repo": {"type": "string"},
                                "title": {"type": "string"},
                                "body": {"type": "string"},
                            },
                            "required": ["owner", "repo", "title"],
                        },
                    },
                    {"name": "ping", "description": "pong", "inputSchema": {"type": "object", "properties": {}}},
                ],
            },
            {
                "name": "tiny",
                "tools": [{"name": "echo", "description": "echo", "inputSchema": {"type": "object"}}],
            },
        ]
    }
    path = tmp_path / "tools.json"
    path.write_text(json.dumps(payload))
    assert mt.main([str(path), "--window", "2000", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["total_tokens"] > 0
    assert data["servers"][0]["server"] == "github"
    assert data["servers"][0]["tokens"] >= data["servers"][1]["tokens"]
    assert data["percent_of_window"] == round(data["total_tokens"] / 2000 * 100, 2)


def test_mcp_config_without_schemas(tmp_path, capsys):
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps({"mcpServers": {"slack": {"command": "npx", "args": ["-y", "slack"]}}}))
    assert mt.main([str(path)]) == 0
    out = capsys.readouterr().out
    assert "config only" in out
    assert "slack" in out


def test_stdin_flat_list(capsys, monkeypatch):
    tools = [{"name": "a", "description": "aaaa", "inputSchema": {"type": "object"}}]
    monkeypatch.setattr("sys.stdin", type("S", (), {"read": lambda self: json.dumps(tools)})())
    assert mt.main(["-"]) == 0
    assert "total" in capsys.readouterr().out


def test_estimator_is_stable():
    assert mt.estimate_tokens("") == 0
    assert mt.estimate_tokens("abcd") == 1
    assert mt.estimate_tokens("abcde") == 2
