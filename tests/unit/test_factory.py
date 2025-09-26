from __future__ import annotations

from typing import Optional

from actcli.seminar.factory import AdapterFactory, BoundAdapter, BoundParams
from actcli.models.participant import ParticipantSpec


class _DummyAdapter:
    def __init__(self) -> None:
        self.name = "dummy"
        self.is_local = True
        self.model_version = "0"
        self.last = {}

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        seed: Optional[int] = None,
        timeout_s: int = 30,
        round_index: int = 1,
        context_snippets: Optional[str] = None,
    ) -> str:  # noqa: E501
        self.last = {
            "prompt": prompt,
            "system": system,
            "seed": seed,
            "timeout_s": timeout_s,
        }
        return "ok"


def test_bound_adapter_overrides_params() -> None:
    base = _DummyAdapter()
    bound = BoundAdapter(
        base, alias="alias1", params=BoundParams(seed=7, system="sys", timeout_s=5)
    )
    out = bound.generate("q", system="ignored", seed=1, timeout_s=30)
    assert out == "ok"
    assert base.last["seed"] == 7
    assert base.last["system"] == "sys"
    assert base.last["timeout_s"] == 5
    assert bound.name == "alias1"


def test_factory_builds_echo_when_cloud_blocked() -> None:
    spec = ParticipantSpec(alias="gpt4o", provider="openai", model_id="gpt-4o")
    a = AdapterFactory.from_spec(spec, allow_cloud=False)
    # When cloud is blocked, should return EchoAdapter with cloud-blocked in base name
    assert hasattr(a, "_base") and hasattr(a._base, "name")
    assert "cloud-blocked" in a._base.name
