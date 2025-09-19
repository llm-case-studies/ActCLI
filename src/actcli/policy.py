from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .trust import TrustRecord, get_trust
from .config import Config, load_config


@dataclass
class Policy:
    read: List[str] = field(default_factory=lambda: ["./**"])  # globs relative to project root
    write: List[str] = field(default_factory=lambda: ["./out/**"])  # globs relative to project root
    cloud_share: bool = False

    def allow_read(self, glob: str) -> None:
        if glob not in self.read:
            self.read.append(glob)

    def allow_write(self, glob: str) -> None:
        if glob not in self.write:
            self.write.append(glob)

    def deny(self, kind: str, glob: str) -> None:
        if kind == "read" and glob in self.read:
            self.read.remove(glob)
        if kind == "write" and glob in self.write:
            self.write.remove(glob)

    def can_read(self, path: Path, root: Path | None = None) -> bool:
        root = root or Path.cwd()
        rel = "./" + str(Path(path).resolve().relative_to(root))
        return any(fnmatch.fnmatch(rel, g) for g in self.read)

    def can_write(self, path: Path, root: Path | None = None) -> bool:
        root = root or Path.cwd()
        rel = "./" + str(Path(path).resolve().relative_to(root))
        return any(fnmatch.fnmatch(rel, g) for g in self.write)


def merge_policy() -> Policy:
    cfg, _ = load_config()
    trust = get_trust()
    p = Policy()
    # From config defaults (future: allow explicit policy in config)
    # From trust store
    if trust:
        p.read = trust.read[:]
        p.write = trust.write[:]
        p.cloud_share = trust.cloud_share
    return p

