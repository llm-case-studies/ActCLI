from __future__ import annotations

from pathlib import Path

from actcli import trust as trust_mod


def test_set_get_revoke_trust(tmp_path: Path, monkeypatch) -> None:
    # Redirect trust dir to tmp
    tdir = tmp_path / "trust.d"
    tdir.mkdir(parents=True)
    monkeypatch.setattr(trust_mod, "TRUST_DIR", tdir, raising=True)

    root = tmp_path / "proj"
    root.mkdir()

    rec_path = trust_mod.set_trust(root, scope="persist", read=["./**"], write=["./out/**"], cloud_share=True)
    assert rec_path.exists()

    rec = trust_mod.get_trust(root)
    assert rec is not None
    assert rec.path == str(root)
    assert rec.scope == "persist"
    assert rec.cloud_share is True

    trust_mod.revoke_trust(root)
    assert not rec_path.exists()

