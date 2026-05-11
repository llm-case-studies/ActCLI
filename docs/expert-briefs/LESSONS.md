# Cross-Initiative Lessons

Append reusable lessons here when a sprint teaches something future ActCLI
sessions should not rediscover.

## 2026-05-08

- The product adoption question is not only "how do we package ActCLI?"
  It is "how does a Pricing R&D actuary safely try it in 10 minutes without
  proprietary data, API keys, or repo knowledge?"
- A product-evaluation sprint should validate an actual evaluator command
  before packaging work. `actcli demo pricing-rnd` now serves as the
  install/demo smoke for future PyPI, Homebrew, binary, and landing-page
  work.
- Validation probes should print enough context before assertions. A probe
  that only asserts can pass while leaving an empty evidence file.
- Package dry-runs should install the built wheel into a fresh venv outside the
  checkout and run the console script with `PYTHONPATH` unset. This catches
  repo-layout assumptions that editable installs hide.
