from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from platformdirs import user_config_dir

try:
    import tomllib as toml  # py311+
except Exception:  # pragma: no cover
    import tomli as toml  # type: ignore


TRUST_DIR = Path(user_config_dir("actcli", "actcli")) / "trust.d"
TRUST_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TrustRecord:
    path: str
    scope: str  # persist|once
    read: List[str]
    write: List[str]
    cloud_share: bool = False


def _fingerprint(path: Path) -> str:
    p = str(path.resolve())
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


def _record_path(root: Path) -> Path:
    return TRUST_DIR / f"{_fingerprint(root)}.toml"


def get_trust(root: Optional[Path] = None) -> Optional[TrustRecord]:
    root = root or Path.cwd()
    path = _record_path(root)
    if not path.exists():
        return None
    data = toml.loads(path.read_text(encoding="utf-8"))
    return TrustRecord(
        path=data.get("path", str(root)),
        scope=data.get("scope", "persist"),
        read=list(data.get("read", ["./**"])),
        write=list(data.get("write", ["./out/**"])),
        cloud_share=bool(data.get("cloud_share", False)),
    )


def set_trust(root: Optional[Path], scope: str, read: List[str], write: List[str], cloud_share: bool) -> Path:
    root = root or Path.cwd()
    path = _record_path(root)
    content = [
        f"path = \"{str(root)}\"",
        f"scope = \"{scope}\"",
        "read = [" + ", ".join(f"\"{g}\"" for g in read) + "]",
        "write = [" + ", ".join(f"\"{g}\"" for g in write) + "]",
        f"cloud_share = {str(cloud_share).lower()}",
    ]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def revoke_trust(root: Optional[Path] = None) -> None:
    root = root or Path.cwd()
    path = _record_path(root)
    if path.exists():
        path.unlink()

