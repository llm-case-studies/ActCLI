# Test Request - PyPI Readiness Dry Run

**Date issued:** 2026-05-08
**Initiative:** `evaluation-path`
**Sprint:** `2026-05-08_pypi-readiness-dry-run`
**Product branch:** `feature/evaluation-path/pypi-readiness-dry-run`
**Validation branch:** `validation/evaluation-path/pypi-readiness-dry-run`
**Validation host:** `iMacDebian`

## What You Are Validating

That ActCLI can be built and tried from a package artifact without relying on
an editable checkout:

1. Build wheel and sdist artifacts from the product branch.
2. Run metadata checks on those artifacts.
3. Install the wheel into a fresh virtual environment outside the repo.
4. From outside the repo, run installed `actcli` commands including the
   validated `demo pricing-rnd` path.

Do not publish to PyPI or TestPyPI.

## Important Host Safety

`iMacDebian` runs the validator's local development environment. Do not disturb
unrelated services or shells.

Specifically:

- do not stop, restart, or kill anything outside this repo's spawned test
  processes
- do not bind to persistent ports
- do not install project dependencies into system Python
- do not use real API keys or proprietary data
- do not contact OpenAI, Anthropic, Google, Ollama, PyPI upload endpoints, or
  other model/provider services

Unacceptable command shapes:

- `kill $(...)`
- `ss ... | head -1 | xargs kill`
- `lsof ... | head -1 | xargs kill`
- `pkill -f bash`
- `pkill -f python`

## Product Commit Under Test

```bash
cd ~/Projects/ActCLI
git fetch origin
git checkout feature/evaluation-path/pypi-readiness-dry-run
git pull --ff-only
git rev-parse HEAD
git checkout -b validation/evaluation-path/pypi-readiness-dry-run
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/00_commit.txt`

If the validation branch already exists locally, stop and ask the orchestrator
whether to reuse it or start fresh.

## Preflight

Use a shared user-level Python env, not system Python. If `python3` is not
Python >=3.10, set `ACTCLI_PYTHON_BIN` first.

```bash
export ACTCLI_PYTHON_BIN="${ACTCLI_PYTHON_BIN:-python3}"
"$ACTCLI_PYTHON_BIN" - <<'PY'
import sys
print(sys.version)
if sys.version_info < (3, 10):
    raise SystemExit("ActCLI requires Python >=3.10; set ACTCLI_PYTHON_BIN.")
PY

export ACTCLI_PY_ENV="${ACTCLI_PY_ENV:-$HOME/.venvs/actcli-python}"
if [ ! -d "$ACTCLI_PY_ENV" ]; then
  "$ACTCLI_PYTHON_BIN" -m venv "$ACTCLI_PY_ENV"
fi
. "$ACTCLI_PY_ENV/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pip show pytest
python -m pip show build
python -m pip show twine
python -m pip show hatchling
git diff origin/main...HEAD --stat
git status --short
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/01_preflight.txt`

If `build` or `twine` is missing after `.[dev]`, report `BLOCKED` unless the
implementer explicitly documented a different local packaging-tool setup in the
result template.

## Tests

```bash
python -m pytest tests/integration/test_demo_pricing_rnd.py -q
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/02_demo_tests.txt`

## Build And Metadata Check

```bash
rm -rf dist build *.egg-info
python -m build
python -m twine check dist/*
python - <<'PY'
from pathlib import Path

files = sorted(p.name for p in Path("dist").iterdir() if p.is_file())
print("dist files", files)
assert any(name.endswith(".whl") for name in files), files
assert any(name.endswith(".tar.gz") for name in files), files
PY
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/03_build_and_metadata.txt`

## Fresh Venv Install

```bash
export VERIFY_DIR="$(mktemp -d)"
export WHEEL_PATH="$(python - <<'PY'
from pathlib import Path

wheels = sorted(Path("dist").glob("*.whl"))
if len(wheels) != 1:
    raise SystemExit(f"expected exactly one wheel, found {wheels}")
print(wheels[0].resolve())
PY
)"
"$ACTCLI_PYTHON_BIN" -m venv "$VERIFY_DIR/venv"
"$VERIFY_DIR/venv/bin/python" -m pip install --upgrade pip
"$VERIFY_DIR/venv/bin/python" -m pip install "$WHEEL_PATH"
"$VERIFY_DIR/venv/bin/python" -m pip show actcli
cd "$VERIFY_DIR"
unset PYTHONPATH
"$VERIFY_DIR/venv/bin/actcli" version
"$VERIFY_DIR/venv/bin/actcli" doctor
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/04_fresh_venv_install.txt`

## Installed Demo Smoke

```bash
cd "$VERIFY_DIR"
unset OPENAI_API_KEY ANTHROPIC_API_KEY GOOGLE_API_KEY PYTHONPATH
"$VERIFY_DIR/venv/bin/actcli" demo pricing-rnd --out "$VERIFY_DIR/pricing-rnd"
find "$VERIFY_DIR/pricing-rnd" -maxdepth 1 -type f -printf '%f\n' | sort
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/05_installed_demo_run.txt`

Expected files:

- `README.md`
- `audit.json`
- `prompt.md`
- `repro.sh`
- `transcript.md`
- `workpaper.md`

## Artifact Content And Safety

```bash
"$VERIFY_DIR/venv/bin/python" - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["VERIFY_DIR"]) / "pricing-rnd"
expected = {
    "README.md",
    "prompt.md",
    "transcript.md",
    "workpaper.md",
    "audit.json",
    "repro.sh",
}
found = {p.name for p in root.iterdir() if p.is_file()}
print("found", sorted(found))
missing = expected - found
extra = found - expected
print("missing", sorted(missing))
print("extra", sorted(extra))
assert not missing
assert not extra

audit = json.loads((root / "audit.json").read_text(encoding="utf-8"))
participants = audit.get("participants", [])
print("participants", participants)
assert len(participants) >= 3
assert all(p.get("local") is True or p.get("demo") is True for p in participants)

for name in ("README.md", "prompt.md", "workpaper.md"):
    text = (root / name).read_text(encoding="utf-8").lower()
    print(name, "contains synthetic:", "synthetic" in text)
    assert "synthetic" in text

repro = (root / "repro.sh").read_text(encoding="utf-8")
print("repro length", len(repro))
assert "/home/alex" not in repro
assert "/Users/alex" not in repro
PY
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/06_artifact_content_and_safety.txt`

## Cleanup

```bash
cd ~/Projects/ActCLI
git status --short
```

Confirm only validation result/evidence files are new or modified on the
validation branch.

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/07_cleanup.txt`

## Result

Fill:

`testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/result.md`

Verdict options: `PASS`, `PASS with findings`, `FAIL`, `BLOCKED`.

Commit result and evidence to:

`validation/evaluation-path/pypi-readiness-dry-run`

Push the validation branch.
