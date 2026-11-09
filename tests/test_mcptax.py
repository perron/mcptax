import io
import json
from pathlib import Path
import pytest
import mcptax.cli as mt


def test_help_and_version():
    with pytest.raises(SystemExit) as exc:
        mt.main(["--help"])
    assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        mt.main(["--version"])
    assert exc.value.code == 0


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
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(tools)))
    assert mt.main(["-"]) == 0
    assert "total" in capsys.readouterr().out


def test_estimator_is_stable():
    assert mt.estimate_tokens("") == 0
    assert mt.estimate_tokens("abcd") == 1
    assert mt.estimate_tokens("abcde") == 2
    assert mt.estimate_tokens("あいう") >= 2


def test_missing_file(tmp_path, capsys):
    assert mt.main([str(tmp_path / "nope.json")]) == 1
    assert "file not found" in capsys.readouterr().err


def test_bad_json(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text("{not json")
    assert mt.main([str(path)]) == 1
    assert "error:" in capsys.readouterr().err


def test_empty_file(tmp_path, capsys):
    path = tmp_path / "empty.json"
    path.write_text("")
    assert mt.main([str(path)]) == 1
    assert "error:" in capsys.readouterr().err


def test_negative_window(tmp_path, capsys):
    path = tmp_path / "tools.json"
    path.write_text("[]")
    assert mt.main([str(path), "--window", "0"]) == 1
    assert "window must be positive" in capsys.readouterr().err


def test_empty_tools(tmp_path, capsys):
    path = tmp_path / "tools.json"
    path.write_text(json.dumps({"tools": []}))
    assert mt.main([str(path), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["total_tokens"] == 0


def test_tools_object_format(tmp_path, capsys):
    path = tmp_path / "tools.json"
    path.write_text(json.dumps({
        "name": "demo",
        "tools": [{"name": "echo", "description": "エコーします", "inputSchema": {"type": "object"}}],
    }))
    assert mt.main([str(path), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["servers"][0]["server"] == "demo"
    assert data["total_tokens"] > 0


def test_unrecognized_json(tmp_path, capsys):
    path = tmp_path / "tools.json"
    path.write_text(json.dumps({"foo": 1}))
    assert mt.main([str(path)]) == 1
    assert "unrecognized JSON" in capsys.readouterr().err


def test_unnamed_tool(tmp_path, capsys):
    path = tmp_path / "tools.json"
    path.write_text(json.dumps([{"description": "mystery", "inputSchema": {"type": "object"}}]))
    assert mt.main([str(path), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["servers"][0]["tool_breakdown"][0]["name"] == "(unnamed)"
