import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import mcp_server.server as server


def test_unsupported_suite_is_rejected_without_running_process(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("Unsupported suites must not start a process")

    monkeypatch.setattr(server, "ROOT", tmp_path)
    monkeypatch.setattr(server, "ARTIFACTS", tmp_path / "artifacts")
    monkeypatch.setattr(server.subprocess, "run", fail_if_called)

    result = server.run_suite("arbitrary-command")

    assert result["ok"] is False
    assert result["exit_code"] is None
    assert "Unsupported test suite" in result["error"]
    assert not (tmp_path / "artifacts").exists()


def test_allowed_suite_uses_fixed_pytest_target_and_saves_summary(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append((command, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout="3 passed",
            stderr="",
        )

    monkeypatch.setattr(server, "ROOT", tmp_path)
    monkeypatch.setattr(server, "ARTIFACTS", tmp_path / "artifacts")
    monkeypatch.setattr(server.subprocess, "run", fake_run)

    result = server.run_suite("playwright")

    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command[:3] == [server.sys.executable, "-m", "pytest"]
    assert Path(command[3]) == server.ALLOWED_SUITES["playwright"]
    assert command[4] == "-v"
    assert command[5].startswith("--junitxml=")
    assert kwargs["cwd"] == server.ROOT
    assert kwargs["stdin"] == subprocess.DEVNULL
    assert "shell" not in kwargs

    saved = json.loads(
        (tmp_path / "artifacts" / "summary-playwright.json").read_text(encoding="utf-8")
    )
    assert saved == result


def test_timed_out_suite_returns_and_saves_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(
            cmd="pytest",
            timeout=300,
            output=b"partial stdout",
            stderr=b"partial stderr",
        )

    monkeypatch.setattr(server, "ROOT", tmp_path)
    monkeypatch.setattr(server, "ARTIFACTS", tmp_path / "artifacts")
    monkeypatch.setattr(server.subprocess, "run", timeout)

    result = server.run_suite("selenium")

    assert result["ok"] is False
    assert result["exit_code"] is None
    assert result["stdout"] == "partial stdout"
    assert result["stderr"] == "partial stderr"
    assert result["error"] == "Test suite timed out after 300 seconds"
    saved = json.loads(
        (tmp_path / "artifacts" / "summary-selenium.json").read_text(encoding="utf-8")
    )
    assert saved == result
