import json
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

from mcp.server.fastmcp import FastMCP


class SuiteSummary(TypedDict):
    suite: str
    exit_code: int | None
    ok: bool
    stdout: str
    stderr: str
    junit_report: str
    error: str


mcp = FastMCP("TestForge QA Automation")
ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"
ALLOWED_SUITES = {
    "selenium": ROOT / "tests" / "selenium",
    "playwright": ROOT / "tests" / "playwright",
}


def _text_output(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def run_suite(suite: str) -> SuiteSummary:
    """Run one predefined pytest suite without a shell."""
    if suite not in ALLOWED_SUITES:
        return {
            "suite": suite,
            "exit_code": None,
            "ok": False,
            "stdout": "",
            "stderr": "",
            "junit_report": "",
            "error": f"Unsupported test suite. Choose one of: {', '.join(ALLOWED_SUITES)}",
        }

    ARTIFACTS.mkdir(exist_ok=True)
    junit_file = ARTIFACTS / f"junit-{suite}.xml"
    summary_file = ARTIFACTS / f"summary-{suite}.json"
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(ALLOWED_SUITES[suite]),
        "-v",
        f"--junitxml={junit_file}",
    ]

    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        summary: SuiteSummary = {
            "suite": suite,
            "exit_code": None,
            "ok": False,
            "stdout": _text_output(exc.stdout)[-12000:],
            "stderr": _text_output(exc.stderr)[-4000:],
            "junit_report": str(junit_file.relative_to(ROOT)),
            "error": "Test suite timed out after 300 seconds",
        }
    else:
        summary = {
            "suite": suite,
            "exit_code": result.returncode,
            "ok": result.returncode == 0,
            "stdout": result.stdout[-12000:],
            "stderr": result.stderr[-4000:],
            "junit_report": str(junit_file.relative_to(ROOT)),
            "error": "",
        }

    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


@mcp.tool()
def run_selenium_tests() -> SuiteSummary:
    """Run the predefined Selenium WebDriver tests."""
    return run_suite("selenium")


@mcp.tool()
def run_playwright_tests() -> SuiteSummary:
    """Run the predefined Playwright browser tests."""
    return run_suite("playwright")


@mcp.tool()
def get_latest_results() -> dict[str, object]:
    """Read saved summaries from the latest MCP-triggered test runs."""
    summaries: dict[str, SuiteSummary] = {}
    for suite in ALLOWED_SUITES:
        path = ARTIFACTS / f"summary-{suite}.json"
        if path.is_file():
            try:
                summaries[suite] = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                summaries[suite] = {"error": f"Could not read summary: {exc}"}

    return {
        "available_summaries": summaries,
        "message": (
            "No saved results yet. Run a test suite first."
            if not summaries
            else "Saved test summaries retrieved."
        ),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
