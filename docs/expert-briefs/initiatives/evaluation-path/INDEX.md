# Evaluation Path - Sprint Index

## Active

| Sprint | Branch | Status | Coding host | Validation host |
|---|---|---|---|---|
| none | - | - | - | - |

## Queued

| Sprint | Why queued | Depends on |
|---|---|---|
| `portable-demo-repro-script` | Make generated demo `repro.sh` use the installed `actcli` console-script path, not repo-root `python -m actcli` | PyPI dry-run finding |
| `landing-demo-script` | Turn the evaluation kit into a 5-minute demo script/video outline | package dry-run confirms the install path |

## Completed

| Sprint | Branch | Verdict | Notes |
|---|---|---|---|
| `2026-05-08_first-10-minutes-evaluation-kit` | `feature/evaluation-path/first-10-minutes-evaluation-kit` | PASS | `actcli demo pricing-rnd` evaluation kit validated on iMacDebian |
| `2026-05-08_pypi-readiness-dry-run` | `feature/evaluation-path/pypi-readiness-dry-run` | PASS with findings | Wheel/sdist build, twine check, fresh venv install, and installed console-script demo validated on iMacDebian |
