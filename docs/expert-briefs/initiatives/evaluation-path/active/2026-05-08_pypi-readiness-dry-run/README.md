# PyPI Readiness Dry Run

This sprint proves ActCLI is package-shaped enough for a developer-leaning
Pricing R&D evaluator to install and try from a built artifact.

It does not publish anything. The target is a local dry run:

```bash
python -m build
python -m twine check dist/*
python -m venv /tmp/actcli-wheel-check
/tmp/actcli-wheel-check/bin/python -m pip install dist/*.whl
cd /tmp
actcli demo pricing-rnd --out pricing-rnd
```

The important product proof is that the already validated demo command works
from the installed console script, outside the source checkout and without
`PYTHONPATH`.
