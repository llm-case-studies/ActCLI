# Test Request - First 10 Minutes Evaluation Kit

**Date issued:** 2026-05-08
**Initiative:** `evaluation-path`
**Sprint:** `2026-05-08_first-10-minutes-evaluation-kit`
**Product branch:** `feature/evaluation-path/first-10-minutes-evaluation-kit`
**Validation branch:** `validation/evaluation-path/first-10-minutes-evaluation-kit`
**Validation host:** `iMacDebian`

## What You Are Validating

That ActCLI now has a safe first-10-minutes evaluation path:

1. `actcli demo pricing-rnd` runs without cloud keys, proprietary data, or
   network access.
2. It writes a complete evaluation kit with prompt, transcript, workpaper,
   audit metadata, reproduction script, and evaluator README.
3. Tests and smoke probes prove the artifacts are deterministic enough for a
   Pricing R&D evaluator to inspect.

## Important Host Safety

`iMacDebian` runs the validator's local development environment. Do not disturb
unrelated services or shells.

Specifically:

- do not stop, restart, or kill anything outside this repo's spawned test
  processes
- do not bind to persistent ports
- do not install project dependencies into system Python
- do not use real API keys or proprietary data
- do not contact OpenAI, Anthropic, Google, Ollama, or other model services

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
git checkout feature/evaluation-path/first-10-minutes-evaluation-kit
git pull --ff-only
git rev-parse HEAD
git checkout -b validation/evaluation-path/first-10-minutes-evaluation-kit
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/00_commit.txt`

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
python -m pip install -e '.[dev]'
python -m pip show pytest
python -m pip show typer
python -m pip show rich
git diff origin/main...HEAD --stat
git status --short
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/01_preflight.txt`

## Static Checks

```bash
python -m pytest tests/integration/test_demo_pricing_rnd.py -q
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/02_demo_tests.txt`

```bash
python -m pytest tests/integration/test_chat_roundtable.py tests/unit/test_transcript.py -q
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/03_regression_tests.txt`

## Run And Probe

### Probe 1 - direct demo run

```bash
export DEMO_OUT="$(mktemp -d)/pricing-rnd"
unset OPENAI_API_KEY ANTHROPIC_API_KEY GOOGLE_API_KEY
python -m actcli demo pricing-rnd --out "$DEMO_OUT"
find "$DEMO_OUT" -maxdepth 1 -type f -printf '%f\n' | sort
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/04_direct_demo_run.txt`

Expected files:

- `README.md`
- `audit.json`
- `prompt.md`
- `repro.sh`
- `transcript.md`
- `workpaper.md`

### Probe 2 - artifact content and safety

```bash
python - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["DEMO_OUT"])
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
print("participants", len(participants))
assert len(participants) >= 3
assert all(p.get("local") is True or p.get("demo") is True for p in participants)

for name in ("README.md", "prompt.md", "workpaper.md"):
    text = (root / name).read_text(encoding="utf-8").lower()
    print(name, "synthetic" in text)
    assert "synthetic" in text

repro = (root / "repro.sh").read_text(encoding="utf-8")
assert "/home/alex" not in repro
assert "/Users/alex" not in repro
PY
```

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/05_artifact_content_and_safety.txt`

## Cleanup

```bash
git status --short
```

Confirm only validation result/evidence files are new or modified on the
validation branch.

Save output to:

`testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/06_cleanup.txt`

## Result

Fill:

`testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/result.md`

Verdict options: `PASS`, `PASS with findings`, `FAIL`, `BLOCKED`.

Commit result and evidence to:

`validation/evaluation-path/first-10-minutes-evaluation-kit`

Push the validation branch.
