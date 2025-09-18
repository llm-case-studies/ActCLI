from __future__ import annotations

import os
from typing import Dict, List, Optional

import httpx

from ..git.local import LocalGit


class GitMCPClient:
    """Client for the Git-MCP service with a safe LocalGit fallback.

    If ACTCLI_GIT_MCP_URL is set, HTTP requests are used; otherwise LocalGit.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or os.environ.get("ACTCLI_GIT_MCP_URL")
        self.local = LocalGit()

    def _post(self, op: str, params: Dict) -> Dict:
        if not self.base_url:
            raise RuntimeError("No MCP URL configured")
        with httpx.Client(timeout=10) as client:
            r = client.post(self.base_url, json={"op": op, "params": params})
            r.raise_for_status()
            return r.json()

    # High-level operations with fallback
    def repo_detect(self) -> Dict:
        if self.base_url:
            try:
                return self._post("repo_detect", {})
            except Exception:
                pass
        info = self.local.detect()
        return {
            "is_repo": info.is_repo,
            "root": info.root,
            "branch": info.branch,
            "default_branch": info.default_branch,
            "remotes": info.remotes,
        }

    def ensure_gitignore(self, entries: List[str]) -> None:
        if self.base_url:
            try:
                self._post("ensure_gitignore", {"entries": entries})
                return
            except Exception:
                pass
        self.local.ensure_gitignore(entries)

    def branch_ensure(self, name: str) -> None:
        info = self.local.detect()
        if info.branch != name:
            # Try switch; if fails, create
            try:
                self.local.branch_switch(name)
            except Exception:
                self.local.branch_create(name)

    def add(self, paths: List[str]) -> None:
        if self.base_url:
            try:
                self._post("add", {"paths": paths})
                return
            except Exception:
                pass
        self.local.add(paths)

    def commit(self, message: str, signoff: bool = False, allow_empty: bool = False) -> str:
        if self.base_url:
            try:
                res = self._post("commit", {"message": message, "signoff": signoff, "allow_empty": allow_empty})
                if res.get("ok") and res.get("data", {}).get("hash"):
                    return res["data"]["hash"]
            except Exception:
                pass
        return self.local.commit(message, signoff=signoff, allow_empty=allow_empty)

    def push(self, remote: str, branch: str) -> None:
        if self.base_url:
            try:
                self._post("push", {"remote": remote, "branch": branch, "set_upstream": True})
                return
            except Exception:
                pass
        self.local.push(remote, branch, set_upstream=True)

    def pr_link(self, remote: str, target: Optional[str], title: str, body: str) -> Optional[str]:
        info = self.local.detect()
        remote_url = info.remotes.get(remote) if info.remotes else None
        branch = info.branch or ""
        target_branch = target or info.default_branch
        if self.base_url:
            try:
                res = self._post("pr_link", {"remote": remote, "target": target_branch, "branch": branch, "title": title, "body": body})
                if res.get("ok") and res.get("data", {}).get("url"):
                    return res["data"]["url"]
            except Exception:
                pass
        if remote_url:
            return self.local.pr_url(remote_url, target_branch, branch, title=title, body=body)
        return None

