from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


def _run_git(args: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except FileNotFoundError:
        return 127, "", "git not found"


@dataclass
class RepoInfo:
    is_repo: bool
    root: Optional[str] = None
    branch: Optional[str] = None
    default_branch: str = "main"
    remotes: Dict[str, str] = None


class LocalGit:
    def __init__(self, cwd: Optional[str] = None) -> None:
        self.cwd = cwd or os.getcwd()

    def detect(self) -> RepoInfo:
        code, out, _ = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=self.cwd)
        if code != 0 or out != "true":
            return RepoInfo(is_repo=False, remotes={})
        _, root, _ = _run_git(["rev-parse", "--show-toplevel"], cwd=self.cwd)
        _, branch, _ = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=self.cwd)
        # Default branch
        code, headref, _ = _run_git(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], cwd=self.cwd)
        default_branch = "main"
        if code == 0 and headref:
            # origin/MAIN
            if "/" in headref:
                default_branch = headref.split("/", 1)[1]
        # Remotes
        remotes: Dict[str, str] = {}
        _, lines, _ = _run_git(["remote", "-v"], cwd=self.cwd)
        for line in lines.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                name, url = parts[0], parts[1]
                remotes.setdefault(name, url)
        return RepoInfo(True, root=root, branch=branch, default_branch=default_branch, remotes=remotes)

    def status(self) -> Dict:
        info = self.detect()
        data = {"branch": info.branch, "staged": [], "changed": [], "untracked": []}
        _, out, _ = _run_git(["status", "--porcelain"], cwd=self.cwd)
        for line in out.splitlines():
            if not line:
                continue
            code = line[:2]
            path = line[3:]
            if code[0] != " " and code[0] != "?":
                data["staged"].append(path)
            elif code == "??":
                data["untracked"].append(path)
            else:
                data["changed"].append(path)
        return data

    def add(self, paths: List[str]) -> None:
        if not paths:
            raise ValueError("No paths provided to add")
        _run_git(["add", *paths], cwd=self.cwd)

    def commit(self, message: str, signoff: bool = False, amend: bool = False, allow_empty: bool = False) -> str:
        args = ["commit", "-m", message]
        if signoff:
            args.append("-s")
        if amend:
            args.append("--amend")
        if allow_empty:
            args.append("--allow-empty")
        code, out, err = _run_git(args, cwd=self.cwd)
        if code != 0:
            raise RuntimeError(err or out or "commit failed")
        # Get hash
        _, h, _ = _run_git(["rev-parse", "HEAD"], cwd=self.cwd)
        return h

    def branch_create(self, name: str) -> None:
        code, _, err = _run_git(["checkout", "-b", name], cwd=self.cwd)
        if code != 0:
            raise RuntimeError(err or "branch create failed")

    def branch_switch(self, name: str) -> None:
        code, _, err = _run_git(["checkout", name], cwd=self.cwd)
        if code != 0:
            raise RuntimeError(err or "branch switch failed")

    def push(self, remote: str, branch: str, set_upstream: bool = True) -> None:
        args = ["push", remote, branch]
        if set_upstream:
            args.insert(1, "-u")
        code, _, err = _run_git(args, cwd=self.cwd)
        if code != 0:
            raise RuntimeError(err or "push failed")

    def ensure_gitignore(self, entries: List[str]) -> None:
        info = self.detect()
        if not info.is_repo or not info.root:
            return
        path = os.path.join(info.root, ".gitignore")
        existing: List[str] = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = [ln.rstrip("\n") for ln in f]
        updated = False
        with open(path, "a", encoding="utf-8") as f:
            for e in entries:
                if e not in existing:
                    f.write(e + "\n")
                    updated = True
        if updated:
            # Stage .gitignore silently (optional)
            _run_git(["add", ".gitignore"], cwd=self.cwd)

    @staticmethod
    def pr_url(remote_url: str, target: str, branch: str, title: str = "", body: str = "") -> Optional[str]:
        import urllib.parse as up

        def gh(owner_repo: str) -> str:
            return f"https://github.com/{owner_repo}/compare/{target}...{branch}?expand=1&title={up.quote(title)}&body={up.quote(body)}"

        def gl(owner_repo: str) -> str:
            return (
                f"https://gitlab.com/{owner_repo}/-/merge_requests/new?merge_request[source_branch]={up.quote(branch)}"
                f"&merge_request[target_branch]={up.quote(target)}&merge_request[title]={up.quote(title)}&merge_request[description]={up.quote(body)}"
            )

        def gitea(host: str, owner_repo: str) -> str:
            return f"https://{host}/{owner_repo}/compare/{target}...{branch}?title={up.quote(title)}&body={up.quote(body)}"

        url = remote_url
        if url.startswith("git@") and ":" in url:
            # git@github.com:org/repo.git
            host = url.split("@", 1)[1].split(":", 1)[0]
            owner_repo = url.split(":", 1)[1]
            if owner_repo.endswith(".git"):
                owner_repo = owner_repo[:-4]
            if host.endswith("github.com"):
                return gh(owner_repo)
            # Assume gitea-like
            return gitea(host, owner_repo)
        if url.startswith("http://") or url.startswith("https://"):
            # https://github.com/org/repo.git
            parts = url.split("//", 1)[1]
            host, path = parts.split("/", 1)
            owner_repo = path
            if owner_repo.endswith(".git"):
                owner_repo = owner_repo[:-4]
            if host.endswith("github.com"):
                return gh(owner_repo)
            if host.endswith("gitlab.com"):
                return gl(owner_repo)
            return gitea(host, owner_repo)
        return None

