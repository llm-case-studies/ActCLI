from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from actcli.models.participant import ParticipantSpec, parse_participant_spec
from actcli.seminar.factory import AdapterFactory, BoundAdapter
from actcli.seminar.adapters.echo import EchoAdapter
from actcli.seminar.rounds import RoundOrchestrator

from ..deps import get_settings
from ..schemas.participants import BoundParams, ParticipantIn, ParticipantOut
from ..schemas.sessions import RoundRecordOut, SessionSnapshot


def _to_spec(pi: ParticipantIn) -> ParticipantSpec:
    if pi.spec:
        st = get_settings()
        return parse_participant_spec(pi.spec, default_ollama_host=st.ollama_host)
    params: dict = {}
    if pi.bound_params is not None:
        params = {
            k: v for k, v in pi.bound_params.model_dump(exclude_none=True).items()
        }
    return ParticipantSpec(
        alias=pi.alias,
        provider=str(pi.provider or "echo"),
        model_id=pi.model_id,
        host=pi.host,
        params=params,
    )


def build_adapters(
    participants: List[ParticipantIn], *, allow_cloud: bool
) -> Tuple[Dict[str, object], List[ParticipantOut]]:
    adapters: Dict[str, object] = {}
    outs: List[ParticipantOut] = []
    for pi in participants:
        spec = _to_spec(pi)
        adapter = AdapterFactory.from_spec(spec, allow_cloud=allow_cloud)
        alias = (
            spec.alias
            or getattr(adapter, "name", None)
            or spec.model_id
            or spec.provider
        )
        # Enforce cloud gating for CLI-backed too when allow_cloud is False
        if not allow_cloud and spec.provider not in ("ollama", "echo"):
            adapter = BoundAdapter(
                EchoAdapter(name=f"{alias}(cloud-blocked)"), alias=str(alias)
            )
        adapters[str(alias)] = adapter
        bound = BoundParams(**spec.params) if spec.params else None
        outs.append(
            ParticipantOut(
                alias=str(alias),
                provider=spec.provider,
                model_id=spec.model_id,
                bound_params=bound,
            )
        )
    return adapters, outs


class SessionWrapper:
    def __init__(
        self,
        *,
        adapters: Dict[str, object],
        window_k: int,
        max_rounds: Optional[int],
        participants_meta: List[ParticipantOut],
    ) -> None:
        self.orchestrator = RoundOrchestrator(window_k=window_k, max_rounds=max_rounds)
        self.orchestrator.set_participants(adapters)
        self._participants_meta: Dict[str, ParticipantOut] = {
            p.alias: p for p in participants_meta
        }

    def set_participants(
        self,
        adapters: Dict[str, object],
        participants_meta: Optional[List[ParticipantOut]] = None,
    ) -> None:
        self.orchestrator.set_participants(adapters)
        if participants_meta is not None:
            self._participants_meta = {p.alias: p for p in participants_meta}

    def to_snapshot(self) -> SessionSnapshot:
        st = self.orchestrator.state
        # Convert history
        history = [RoundRecordOut.from_round(rr) for rr in (st.history or [])]
        return SessionSnapshot(
            id=st.id,
            created_at=st.started_at,
            round_idx=st.round_idx,
            window_k=st.window_k,
            max_rounds=st.max_rounds,
            participants=list(self._participants_meta.values()),
            history=history,
        )


class OrchestratorRegistry:
    def __init__(self) -> None:
        self._by_id: Dict[str, SessionWrapper] = {}

    def create(
        self, *, adapters: Dict[str, object], window_k: int, max_rounds: Optional[int]
    ) -> SessionWrapper:
        # Build a minimal participants meta from adapters only when build_adapters isn't used
        parts_meta = [
            ParticipantOut(
                alias=a, provider="unknown", model_id=None, bound_params=None
            )
            for a in adapters.keys()
        ]
        wrapper = SessionWrapper(
            adapters=adapters,
            window_k=window_k,
            max_rounds=max_rounds,
            participants_meta=parts_meta,
        )
        self._by_id[wrapper.orchestrator.state.id] = wrapper
        return wrapper

    def create_with_meta(
        self,
        *,
        adapters: Dict[str, object],
        participants_meta: List[ParticipantOut],
        window_k: int,
        max_rounds: Optional[int],
    ) -> SessionWrapper:
        wrapper = SessionWrapper(
            adapters=adapters,
            window_k=window_k,
            max_rounds=max_rounds,
            participants_meta=participants_meta,
        )
        self._by_id[wrapper.orchestrator.state.id] = wrapper
        return wrapper

    def get(self, session_id: str) -> Optional[SessionWrapper]:
        return self._by_id.get(session_id)
