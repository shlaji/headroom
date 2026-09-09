"""Reject remote wrapping before unsupported integrations mutate local state."""

from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from headroom.cli import wrap as wrap_mod
from headroom.cli.main import main


@pytest.mark.parametrize("tool", ["grok", "grok-build", "copilot", "zcode", "kimi", "vibe", "omp"])
def test_remote_proxy_rejects_unsupported_tool_before_setup(
    monkeypatch: pytest.MonkeyPatch, tool: str
) -> None:
    monkeypatch.setenv("HEADROOM_REMOTE_PROXY_URL", "https://proxy.example/base")
    callback = Mock()
    purge = Mock(return_value=False)
    monkeypatch.setattr(wrap_mod.wrap.commands[tool], "callback", callback)
    monkeypatch.setattr(wrap_mod, "_should_purge_context_tools", purge)

    result = CliRunner().invoke(main, ["wrap", tool])

    assert result.exit_code == 1
    assert "HEADROOM_REMOTE_PROXY_URL" in result.output
    assert tool in result.output
    callback.assert_not_called()
    purge.assert_not_called()


@pytest.mark.parametrize("remote", [False, True])
@pytest.mark.parametrize(
    "tool",
    ["claude", "codex", "opencode", "aider", "cursor", "cline", "continue", "goose", "openhands"],
)
def test_supported_tool_reaches_setup(
    monkeypatch: pytest.MonkeyPatch, tool: str, remote: bool
) -> None:
    monkeypatch.delenv("HEADROOM_REMOTE_PROXY_URL", raising=False)
    if remote:
        monkeypatch.setenv("HEADROOM_REMOTE_PROXY_URL", "https://proxy.example/base")
    callback = Mock()
    monkeypatch.setattr(wrap_mod.wrap.commands[tool], "callback", callback)
    monkeypatch.setattr(wrap_mod, "_should_purge_context_tools", lambda _ctx: False)

    result = CliRunner().invoke(main, ["wrap", tool])

    assert result.exit_code == 0, result.output
    callback.assert_called_once()


def test_local_grok_still_reaches_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HEADROOM_REMOTE_PROXY_URL", raising=False)
    callback = Mock()
    monkeypatch.setattr(wrap_mod.wrap.commands["grok"], "callback", callback)
    monkeypatch.setattr(wrap_mod, "_should_purge_context_tools", lambda _ctx: False)

    result = CliRunner().invoke(main, ["wrap", "grok"])

    assert result.exit_code == 0, result.output
    callback.assert_called_once()
