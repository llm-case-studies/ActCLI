# Sprint Brief - PyPI Readiness Dry Run

**Initiative:** `evaluation-path`
**Sprint:** `2026-05-08_pypi-readiness-dry-run`
**Target branch:** `feature/evaluation-path/pypi-readiness-dry-run`
**Merge target:** `main`
**Validation branch:** `validation/evaluation-path/pypi-readiness-dry-run`

## Goal

Prove that ActCLI can be built and tried like a normal Python CLI package before
any public release work starts.

The successful path should be:

```bash
python -m build
python -m twine check dist/*
python -m venv "$VERIFY_DIR/venv"
"$VERIFY_DIR/venv/bin/python" -m pip install dist/*.whl
cd "$VERIFY_DIR"
actcli version
actcli doctor
actcli demo pricing-rnd --out "$VERIFY_DIR/pricing-rnd"
```

The key product claim is not "PyPI is published." The key claim is "a Pricing
R&D evaluator can install a package artifact and run the first demo without
knowing the source checkout layout."

## Why Now

The first evaluation sprint validated:

```bash
actcli demo pricing-rnd --out out/evaluation/pricing-rnd
```

That proves the evaluator experience from source. The next risk is packaging
friction: missing package data, broken console entry points, unlisted build
tools, docs that assume a checkout, or commands that only work because the repo
is on `PYTHONPATH`.

This sprint is intentionally small. It should make the later real PyPI release
boring.

## Scope Fence

Expected touch set:

- `pyproject.toml`
- `README.md` if packaging/install instructions need a small correction
- `docs/release/PYPI_DRY_RUN.md` or similarly named packaging dry-run note
- `tests/integration/test_demo_pricing_rnd.py` only if installed-package smoke
  expectations reveal a real gap
- small packaging/support files if required by Hatchling

Good scope:

- Ensure declared dev tooling includes the commands needed for packaging checks
  if the current project metadata omits them.
- Ensure `python -m build` produces both wheel and sdist artifacts.
- Ensure `python -m twine check dist/*` passes.
- Ensure the wheel installs into a brand-new venv outside the checkout.
- Ensure installed console scripts include `actcli`.
- Ensure `actcli version`, `actcli doctor`, and `actcli demo pricing-rnd` work
  from outside the repo.
- Add a concise dry-run document with exact commands and known assumptions.

Still out of scope:

- Publishing to PyPI or TestPyPI.
- Creating, reserving, or changing package ownership.
- Homebrew, Docker, PyInstaller, Nuitka, MSI, or signed installers.
- Real OpenAI/Anthropic/Google/Ollama setup.
- Changing the demo scenario content unless packaging exposes a true bug.
- Large dependency cleanup unrelated to build/install readiness.

## Acceptance Target

- `python -m pytest tests/integration/test_demo_pricing_rnd.py -q` exits 0.
- `python -m build` exits 0 and creates at least one `.whl` and one `.tar.gz`
  in `dist/`.
- `python -m twine check dist/*` exits 0.
- A fresh venv outside the repo can install the built wheel with no editable
  install and no `PYTHONPATH`.
- From a working directory outside the repo, `actcli version` exits 0.
- From a working directory outside the repo, `actcli doctor` exits 0.
- From a working directory outside the repo, `actcli demo pricing-rnd --out
  "$VERIFY_DIR/pricing-rnd"` exits 0.
- The installed demo output contains exactly:
  `README.md`, `prompt.md`, `transcript.md`, `workpaper.md`, `audit.json`, and
  `repro.sh`.
- `audit.json` records at least three local/demo participants.
- `README.md`, `prompt.md`, and `workpaper.md` contain `synthetic`.
- The dry-run note records the final commands, Python version used, and any
  packaging caveats.

## Honest-Failure Mode

If the package cannot pass a real dry run without larger product decisions,
do not hide it. Record the blocker and the smallest next decision needed. A
clear `BLOCKED` with evidence is better than a fake packaging victory.

Examples of acceptable blockers:

- project metadata is missing required PyPI fields and needs a product decision
- package import relies on files that are not included in the wheel
- console scripts expose a command that cannot run outside a checkout
- dependency versions conflict on a clean install

## Hosts

- coding host: `Acer-HL`
- validation host: `iMacDebian`
- orchestration host: local Codex/Claude session on the user's primary
  workstation

## Host Safety

No protected production services are involved in this sprint. Standard host
safety still applies:

- do not publish anything to PyPI or TestPyPI
- do not commit host-local Claude/Codex memory
- do not install project dependencies into system Python
- do not use real API keys or proprietary data
- do not contact cloud providers during tests or smokes
- keep verification venvs outside the repo or under temporary directories
