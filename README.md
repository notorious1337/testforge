# TestForge QA Automation Framework

TestForge combines browser functional testing, a controlled MCP interface, and a local-only HTTP performance target. Selenium and Playwright exercise the public SauceDemo demonstration storefront; JMeter targets only the FastAPI app in this repository.

## Architecture

| Component | Purpose |
| --- | --- |
| Selenium WebDriver | SauceDemo login, invalid-login feedback, and add-to-cart validation |
| Playwright for Python | SauceDemo inventory, invalid-login, and cart-to-checkout-summary journeys |
| FastAPI | Local `/health` and `/products` endpoints for performance testing |
| Apache JMeter | Small `/health` smoke plan against the local FastAPI target |
| pytest | Test discovery, markers, JUnit XML, and HTML reports |
| MCP | Three fixed stdio tools for running the Selenium/Playwright suites and reading saved results |
| GitHub Actions | Browser tests on pushes and pull requests to `main`, plus manual dispatch; reports are uploaded even when tests fail |

The MCP server accepts no command or path from tool arguments. It maps each run tool to a predefined test directory and invokes pytest without a shell.

## Requirements

- Python 3.11 (the project CI runtime)
- Chrome or Chromium for Selenium; Playwright Chromium for Playwright
- Java JDK and Apache JMeter 5.6.3 for the performance smoke plan
- Git
- Node.js/npm only if using the MCP Inspector

## Setup (Windows PowerShell)

Run from the repository root. Confirm that the Python launcher can find 3.11 with `py -0p`.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again. Selenium Manager locates/manages ChromeDriver; set `CHROME_BINARY` if Chrome is not discoverable:

```powershell
$env:CHROME_BINARY = "C:\path\to\chrome.exe"
```

The SauceDemo URL and demo credentials can be overridden with `SAUCEDEMO_URL`, `SAUCEDEMO_USERNAME`, and `SAUCEDEMO_PASSWORD`. Selenium runs headless by default; set `HEADLESS=false` to show its browser.

## Browser tests and reports

```powershell
python -m pytest tests\selenium -v -m selenium
python -m pytest tests\playwright -v -m playwright
```

Run both suites and generate JUnit XML and a self-contained HTML report:

```powershell
New-Item -ItemType Directory -Force artifacts | Out-Null
python -m pytest tests -v `
  --junitxml=artifacts\junit.xml `
  --html=artifacts\pytest-report.html `
  --self-contained-html
```

Generated reports and performance results under `artifacts/` are ignored by Git, except for the tracked `.gitkeep`.

## Local performance target and JMeter

Start the target in one terminal:

```powershell
python -m uvicorn app.performance_target:app --host 127.0.0.1 --port 8000
```

Verify the endpoints from another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/products
```

With a JDK and JMeter 5.6.3 installed and available on `PATH`, run the small local health smoke plan:

```powershell
New-Item -ItemType Directory -Force artifacts | Out-Null
jmeter -n -t performance\health_smoke.jmx `
  -l artifacts\jmeter-results.jtl `
  -e -o artifacts\jmeter-dashboard
```

The plan uses two virtual users, ten iterations each, and asserts HTTP 200 from `127.0.0.1:8000/health` by default. Use `-Jhost` and `-Jport` only for another authorized local target. JMeter requires a new/empty dashboard output directory; choose a new name for each report rather than overwriting an existing one. This smoke plan is not a capacity benchmark. Do not run it against SauceDemo or another public site.

## MCP server

The stdio server can be launched by an MCP-compatible client:

```powershell
python -m mcp_server.server
```

Its only tools are `run_selenium_tests`, `run_playwright_tests`, and `get_latest_results`. To inspect them with MCP Inspector, run:

```powershell
npx -y @modelcontextprotocol/inspector .\.venv\Scripts\python.exe -m mcp_server.server
```

Test-run summaries and per-suite JUnit XML are written under `artifacts/`. Manually running pytest does not update the MCP summaries.

## CI

`.github/workflows/tests.yml` runs the browser tests on pushes and pull requests targeting `main`, and on manual dispatch. It installs Python 3.11, project dependencies, and Playwright Chromium, then uploads JUnit/HTML reports even if the test step fails. The workflow must run in GitHub Actions before its CI result can be claimed.

## Observed validation and limitations

Local validation on 2026-10-17 used Python 3.13.14 because the machine's Python 3.11 launcher entry pointed to a missing executable and a user-scoped Python 3.11 installation failed in Windows Installer. The full browser suite passed: 6 tests (3 Selenium and 3 Playwright); `artifacts/junit.xml` and `artifacts/pytest-report.html` were generated. An MCP stdio client discovered the three tools, ran the Playwright suite (3 passed), and retrieved its saved result. The FastAPI endpoints returned HTTP 200, and the JMX XML and workflow YAML parsed successfully. Python 3.11 CI execution and GitHub Actions results have not been observed from this machine. The MCP Inspector web UI was not independently validated.

Java is present on this machine but `java -version` exits abnormally, and JMeter is not installed. The local FastAPI endpoints and JMeter plan structure were checked, but a JMeter run, JTL results, and dashboard have not been produced here. Do not report performance measurements until a real JMeter run completes.

SauceDemo is a public demo storefront, not a service controlled by this project. Browser results can be affected by network availability and upstream UI changes. JMeter results, when collected, describe only the local FastAPI target and depend on the machine and workload. No screenshots or performance figures are included unless they have been captured/measured in an actual run.
