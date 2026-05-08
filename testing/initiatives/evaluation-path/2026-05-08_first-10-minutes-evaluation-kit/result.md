# Validation Result - First 10 Minutes Evaluation Kit

## Verdict

PASS

## Product Commit Tested

be32010bdb433c26798dad0a5fe84a1c6a4a47a3

## Environment

- Python: 3.13.5 (GCC 14.2.0)
- Venv: /home/alex/.venvs/actcli-python
- pytest: 9.0.3
- typer: 0.25.1
- rich: 15.0.0

## Checks

| Check | Result |
|---|---|
| Demo integration tests | 2 passed in 0.03s |
| Chat/transcript regression tests | 2 passed in 0.07s |
| Direct demo run | 6/6 expected files created |
| Artifact content and safety | All assertions passed: 3 local/demo participants, synthetic marker present, no home paths in repro.sh |
| Cleanup | Only validation evidence files modified |

## Evidence Files

- `testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/00_commit.txt`
- `testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/01_preflight.txt`
- `testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/02_demo_tests.txt`
- `testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/03_regression_tests.txt`
- `testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/04_direct_demo_run.txt`
- `testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/05_artifact_content_and_safety.txt`
- `testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/evidence/06_cleanup.txt`

## Notes

All checks passed. Demo ran offline with synthetic participants, no network or API keys needed. Output kit is complete with all 6 expected artifacts, each containing the "synthetic" marker. repro.sh is free of local filesystem paths.
