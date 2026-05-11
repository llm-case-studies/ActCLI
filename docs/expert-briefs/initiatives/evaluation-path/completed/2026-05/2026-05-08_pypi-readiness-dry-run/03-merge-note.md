# Merge Note - PyPI Readiness Dry Run

## Branches

- working branch: `feature/evaluation-path/pypi-readiness-dry-run`
- merge target: `main`
- validation branch: `validation/evaluation-path/pypi-readiness-dry-run`

## Validation Outcome

- implementation host: `Acer-HL`
- validation host: `iMacDebian`
- tested product commit: `a243da590b82c191b9fcac1f7a6abd36c483c97a`
- implementation commits:
  - `bfaad06` - `docs: seed pypi readiness dry-run sprint`
  - `117be0f` - `feat(packaging): add build and twine to dev deps; fill pypi dry-run result`
  - `a243da5` - `docs: correct pypi dry-run result commit`
- validation evidence commits:
  - `61e74be` - `validation: pypi-readiness-dry-run - PASS with findings`
- verdict: **PASS with findings**
- result path:
  `testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/result.md`

## Evidence Summary

- `python -m pytest tests/integration/test_demo_pricing_rnd.py -q`:
  2 passed.
- `python -m build`: created `actcli-0.0.1.tar.gz` and
  `actcli-0.0.1-py3-none-any.whl`.
- `python -m twine check dist/*`: PASSED for both artifacts.
- Fresh venv wheel install outside repo: succeeded, with 26 packages installed.
- Installed `actcli version`: printed `ActCLI 0.0.1`.
- Installed `actcli doctor`: ran successfully; non-interactive TTY/color and
  missing optional providers reported as WARN/INFO, not failures.
- Installed `actcli demo pricing-rnd`: created all six expected artifacts with
  three local/demo participants.
- Artifact safety checks passed: synthetic markers present and no `/home/alex`
  or `/Users/alex` paths in `repro.sh`.

## Findings

- The wheel/sdist dry-run is healthy enough to continue toward a real PyPI
  release once product-facing reproduction instructions are tightened.
- Adding `build` and `twine` to the `dev` optional dependency set made packaging
  checks explicit instead of host-magic.
- Hatchling is not installed as a dev extra on iMacDebian, but the PEP 517
  build path handled it via build isolation. That is acceptable for this dry
  run.
- The generated demo `repro.sh` still says to run from the ActCLI repository
  root and uses `python -m actcli demo ...`. The installed console-script path
  works, so this did not block acceptance, but it should be fixed before public
  PyPI-facing instructions.

## Decision

- merge to `main`: yes
- close sprint: yes
- split follow-up: yes

## Follow-Up

- `portable-demo-repro-script`: generate `repro.sh` for installed-package users
  by preferring the `actcli` console script and avoiding repo-root assumptions.
- `landing-demo-script`: turn the validated demo and install path into a
  5-minute evaluation/demo outline.
