from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Scaffold: unlimited rounds REPL and persistence to be implemented")
def test_unlimited_rounds_basic_flow(tmp_path) -> None:
    # Expect: /round start, /round next, /round stop drive the index and produce files later
    assert tmp_path.exists()

