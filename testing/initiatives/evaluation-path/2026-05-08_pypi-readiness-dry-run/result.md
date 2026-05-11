# Validation Result - PyPI Readiness Dry Run

## Verdict

PASS with findings

## Product Commit Tested

a243da590b82c191b9fcac1f7a6abd36c483c97a

## Environment

- Python: 3.13.5 (GCC 14.2.0)
- Venv: /home/alex/.venvs/actcli-python
- build: 1.5.0
- twine: 6.2.0
- hatchling: not in [dev] extras (PEP 517 build backend, handled by build isolation)

## Checks

| Check | Result |
|---|---|
| Demo integration tests | 2 passed in 0.03s |
| Build wheel and sdist | actcli-0.0.1.tar.gz + actcli-0.0.1-py3-none-any.whl |
| Twine metadata check | PASSED (both artifacts) |
| Fresh venv wheel install outside repo | 26 packages installed successfully |
| Installed `actcli version` | ActCLI 0.0.1 |
| Installed `actcli doctor` | All checks ran, no errors |
| Installed `actcli demo pricing-rnd` | 6/6 expected files created, 3 local/demo participants |
| Artifact content and safety | All assertions passed: synthetic marker present, no home paths in repro.sh |
| Cleanup | Only validation evidence files modified |

## Evidence Files

- `testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/00_commit.txt`
- `testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/01_preflight.txt`
- `testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/02_demo_tests.txt`
- `testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/03_build_and_metadata.txt`
- `testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/04_fresh_venv_install.txt`
- `testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/05_installed_demo_run.txt`
- `testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/06_artifact_content_and_safety.txt`
- `testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/evidence/07_cleanup.txt`

## Notes

Finding: The generated `repro.sh` references `python -m actcli demo pricing-rnd --out out/evaluation/pricing-rnd`. The installed console-script (`actcli` from `$PATH`) works correctly, but `repro.sh` still uses the module invocation path. This does not block the acceptance criteria but should be noted for future improvement.
