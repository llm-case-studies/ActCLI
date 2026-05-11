Work in:

`/home/alex/Projects/ActCLI` on `Acer-HL`.

If the repo is not yet on this machine, clone it first:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone git@github.com:llm-case-studies/ActCLI.git
cd ActCLI
```

If it is already there, fetch and check status:

```bash
cd ~/Projects/ActCLI
git fetch origin
git status --short --branch
```

If there are uncommitted changes from another lane, stop and report.

Branch:

`feature/evaluation-path/pypi-readiness-dry-run`

Check it out:

```bash
git checkout feature/evaluation-path/pypi-readiness-dry-run
git pull --ff-only
```

This sprint proves ActCLI can be built, metadata-checked, installed from a
wheel into a fresh virtual environment outside the repo, and then used through
the installed console script:

```bash
actcli demo pricing-rnd --out "$TMPDIR/pricing-rnd"
```

Do not publish to PyPI. This is a local package-readiness dry run only.

Read first:

- `AGENTS.md`
- `docs/DEPLOYMENT_AND_DISTRIBUTION_2026-05-08.md`
- `docs/expert-briefs/README.md`
- `docs/expert-briefs/initiatives/evaluation-path/README.md`
- `docs/expert-briefs/initiatives/evaluation-path/active/2026-05-08_pypi-readiness-dry-run/01-brief.md`
- `testing/initiatives/evaluation-path/2026-05-08_pypi-readiness-dry-run/request.md`
- `pyproject.toml`
- `src/actcli/cli.py`
- `src/actcli/commands/demo.py`
- `tests/integration/test_demo_pricing_rnd.py`

Environment:

- Use Python 3.10+.
- Prefer a shared user-level env such as `$HOME/.venvs/actcli-python`.
- Do not install project dependencies into system Python.
- It is OK to install or declare packaging tools such as `build` and `twine`
  inside the project/dev environment.

Before handoff:

1. `python -m pytest tests/integration/test_demo_pricing_rnd.py -q`
2. `python -m build`
3. `python -m twine check dist/*`
4. Install the built wheel into a fresh virtual environment outside the repo.
5. From a temporary working directory outside the repo, run `actcli version`,
   `actcli doctor`, and `actcli demo pricing-rnd --out "$TMPDIR/pricing-rnd"`.
6. Confirm the installed demo creates the six expected artifacts.
7. Fill
   `docs/expert-briefs/initiatives/evaluation-path/active/2026-05-08_pypi-readiness-dry-run/02-result-template.md`.
8. Commit and push the branch.
