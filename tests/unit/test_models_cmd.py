from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional


from actcli.commands import models as models_cmd


class _FakeResp:
    def __init__(self, json_data: Dict | None = None, status_code: int = 200, lines: Optional[List[str]] = None) -> None:
        self._json = json_data or {}
        self.status_code = status_code
        self._lines = lines or []
        self.text = json.dumps(self._json)

    def json(self) -> Dict:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code // 100 != 2:
            raise AssertionError(f"status {self.status_code}")

    # Streaming context manager API
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def iter_lines(self) -> Iterable[str]:
        for ln in self._lines:
            yield ln


class _FakeClient:
    def __init__(self, *, tags_json: Dict, pull_lines: Optional[List[str]] = None) -> None:
        self._tags_json = tags_json
        self._pull_lines = pull_lines or []

    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url: str):
        assert url.endswith("/api/tags")
        return _FakeResp(self._tags_json, 200)

    def stream(self, method: str, url: str, json: Dict[str, Any]):
        assert method == "POST" and url.endswith("/api/pull")
        return _FakeResp({}, 200, self._pull_lines)


def test_list_models_prints_table(monkeypatch, capsys) -> None:
    fake_client = _FakeClient(
        tags_json={"models": [{"name": "llama3:8b", "modified_at": "y", "size": 1}]}
    )
    monkeypatch.setattr(models_cmd.httpx, "Client", lambda **kw: fake_client)
    models_cmd.list_models("http://host")
    out = capsys.readouterr().out
    assert "llama3:8b" in out


def test_pull_models_stream_progress(monkeypatch, capsys) -> None:
    lines = [
        json.dumps({"status": "pulling"}),
        json.dumps({"total": 100, "completed": 50}),
        json.dumps({"status": "success"}),
    ]
    fake_client = _FakeClient(tags_json={}, pull_lines=lines)
    monkeypatch.setattr(models_cmd.httpx, "Client", lambda **kw: fake_client)
    models_cmd.pull_models("http://host", ["llama3:8b"], use_default=False)
    out = capsys.readouterr().out
    assert "Pulling" in out

