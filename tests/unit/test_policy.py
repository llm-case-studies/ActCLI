from __future__ import annotations

from pathlib import Path

from actcli.policy import Policy


def test_policy_allow_deny_and_checks(tmp_path: Path) -> None:
    p = Policy()
    root = tmp_path
    (root / "out").mkdir()
    f_read = root / "data.txt"
    f_read.write_text("ok", encoding="utf-8")
    f_write = root / "out" / "file.txt"

    assert p.can_read(f_read, root=root)
    assert p.can_write(f_write, root=root)

    p.deny("write", "./out/**")
    assert not p.can_write(f_write, root=root)

    p.allow_write("./out/**")
    assert p.can_write(f_write, root=root)

