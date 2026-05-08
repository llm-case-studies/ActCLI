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

`feature/evaluation-path/first-10-minutes-evaluation-kit`

Check it out:

```bash
git checkout feature/evaluation-path/first-10-minutes-evaluation-kit
git pull --ff-only
```

This sprint creates the first "try ActCLI safely" path:

```bash
actcli demo pricing-rnd --out out/evaluation/pricing-rnd
```

The command must run offline with deterministic demo participants. It should
not require OpenAI, Anthropic, Google, Ollama, proprietary files, or network
access.

Read first:

- `AGENTS.md`
- `CLAUDE.md` if useful locally
- `docs/DEPLOYMENT_AND_DISTRIBUTION_2026-05-08.md`
- `docs/expert-briefs/README.md`
- `docs/expert-briefs/initiatives/evaluation-path/README.md`
- `docs/expert-briefs/initiatives/evaluation-path/active/2026-05-08_first-10-minutes-evaluation-kit/01-brief.md`
- `testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/request.md`
- `src/actcli/cli.py`
- `src/actcli/commands/chat.py`
- `src/actcli/transcript.py`
- `tests/integration/test_chat_roundtable.py`
- `tests/unit/test_transcript.py`

Environment:

- Use Python 3.10+.
- Prefer a shared user-level env such as `$HOME/.venvs/actcli-python`.
- Do not install project dependencies into system Python.

Before handoff:

1. `python -m pytest tests/integration/test_demo_pricing_rnd.py -q`
2. `python -m pytest tests/integration/test_chat_roundtable.py tests/unit/test_transcript.py -q`
3. Run `python -m actcli demo pricing-rnd --out "$(mktemp -d)/pricing-rnd"` and confirm the expected artifacts.
4. Confirm the demo works without cloud/API env vars and does not contact the network.
5. Fill
   `docs/expert-briefs/initiatives/evaluation-path/active/2026-05-08_first-10-minutes-evaluation-kit/02-result-template.md`.
6. Commit and push the branch.
