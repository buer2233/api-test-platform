# Repository Guidelines

## Project Structure & Module Organization
The active project lives in `api_test/`; the repository root is mainly a wrapper. Core HTTP helpers are in `api_test/core/` (`base_api.py`, `public_api.py`). Test suites live in `api_test/tests/` and follow the `test_*.py` pattern. Shared fixtures and pytest hooks are centralized in `api_test/conftest.py`. Runtime settings are in `api_test/config.py`, while local credential-style test data sits in `api_test/test_data/`. Generated HTML reports are written to `api_test/report/` and should be treated as build output.

## Build, Test, and Development Commands
Work from `api_test/` unless a command explicitly targets the repo root.

- `cd api_test` ！ enter the project directory.
- `python -m venv .venv && .venv\Scripts\activate` ！ create and activate a local virtual environment.
- `pip install -r requirements.txt` ！ install pytest and API-test dependencies.
- `pytest` ！ run the full test suite using `pytest.ini` defaults.
- `pytest -m smoke` ！ run smoke coverage only.
- `python run_test.py --html` ！ run tests and generate `report/report.html`.
- `python run_test.py -f tests/test_demo.py --reruns 2` ！ run one file with reruns.

## Coding Style & Naming Conventions
Follow existing Python conventions: 4-space indentation, grouped imports, and short docstrings on public classes and helpers. Use `PascalCase` for classes, `snake_case` for functions, fixtures, and variables, and `UPPER_SNAKE_CASE` for constants and config values. Keep new helpers close to the layer they belong to: reusable request logic in `core/`, test-only setup in `conftest.py`, and test scenarios in `tests/`.

## Testing Guidelines
This project uses `pytest` with `pytest-html`, `pytest-rerunfailures`, and custom markers defined in `api_test/pytest.ini`. Name test classes `Test...` and test methods `test_...`. Reuse fixtures such as `admin_account` and `employee_account` instead of hardcoding credentials in tests. For each new scenario, include at least one success path and one edge or failure check. During development, narrow runs with commands like `pytest tests/test_demo.py -k login`.

## Commit & Pull Request Guidelines
The current history only shows `first commit`, so there is no strong house style yet. Prefer short, imperative commit messages with an optional scope, for example `test: add smoke coverage for login`. Pull requests should describe affected modules, list commands run, note any changes to `config.py` or `test_data/`, and include report output paths when relevant.

## Security & Configuration Tips
Do not commit real hosts, credentials, or environment-specific secrets from `api_test/config.py` or `api_test/test_data/account.txt`. Sanitize examples before sharing logs or reports, and keep generated artifacts in `api_test/report/` out of code review unless they help explain a failure.
