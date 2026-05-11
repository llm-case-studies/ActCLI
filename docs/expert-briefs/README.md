# ActCLI Expert Briefs

This folder holds initiative-first sprint packs for work that spans agents,
hosts, or validation lanes.

Use this process when a task should be handed from an orchestrator to an
implementer and then independently validated. Keep durable project memory here,
not in host-local agent chats.

Folder shape:

```text
docs/expert-briefs/
  INDEX.md
  LESSONS.md
  initiatives/<initiative>/
    README.md
    INDEX.md
    LESSONS.md
    active/<YYYY-MM-DD_slug>/
    completed/<YYYY-MM>/<YYYY-MM-DD_slug>/

testing/initiatives/<initiative>/<YYYY-MM-DD_slug>/
  request.md
  result.md
  evidence/
```

The first active initiative is `evaluation-path`: making ActCLI easy for a
Pricing R&D actuary to try safely in the first 10 minutes.

## Current Handoff - 2026-05-08

The sprint-pack process was introduced here from the proven ActCLI-Bench
workflow. If a fresh orchestrator session starts in this repo, resume by
checking:

```bash
git status --short --branch
git fetch origin
git log --oneline --decorate --max-count=8
find docs/expert-briefs/initiatives -path '*/active/*' -maxdepth 6 -type f | sort
```

Current state after the first two evaluation-path sprints:

```text
initiative: evaluation-path
active sprint: none
completed sprints:
  - 2026-05-08_first-10-minutes-evaluation-kit
  - 2026-05-08_pypi-readiness-dry-run
validated command: actcli demo pricing-rnd --out out/evaluation/pricing-rnd
package dry-run: PASS with findings
next candidates: portable-demo-repro-script, landing-demo-script
```

The intended product surface is:

```bash
actcli demo pricing-rnd --out out/evaluation/pricing-rnd
```

The first sprint proved the evaluator experience: no proprietary data, no cloud
keys, no network dependency, and inspectable artifacts that a Pricing R&D
actuary can show colleagues. Future packaging or landing-page work should use
that command as the smoke target.

The `pypi-readiness-dry-run` sprint proved that ActCLI can build wheel/sdist
artifacts, validate package metadata, install the wheel into a fresh virtual
environment outside the checkout, and run the same `actcli demo pricing-rnd`
smoke target from the installed console script.

Known follow-up: the generated demo `repro.sh` still uses `python -m actcli`
and says to run from the repo root. The installed `actcli` console script works,
but before a real PyPI release the generated reproduction script should be made
portable for installed-package users.
