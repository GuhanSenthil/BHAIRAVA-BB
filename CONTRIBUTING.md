# Contributing

## Dev setup

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    pytest -q
    ruff check .

## Standards

- Python 3.11+
- Type hints on every public function
- Ruff clean
- No shell=True in subprocess calls
- Every active operation gated by ScopeGuard

## Pull requests

One feature per PR. Include tests.
