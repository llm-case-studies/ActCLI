from __future__ import annotations

import json
import shutil
import subprocess
from typing import Dict


def try_run(cmd, timeout=8):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"ok": p.returncode == 0, "stdout": p.stdout.strip(), "stderr": p.stderr.strip(), "rc": p.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "timeout", "rc": -1}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "rc": -2}


def main():
    if not shutil.which("codex"):
        print(json.dumps({"error": "codex binary not found", "hint": "npm i -g @openai/codex"}, indent=2))
        return

    report: Dict[str, object] = {"version": try_run(["codex", "--version"]) }
    prompt = "ping"

    # Attempt forms
    forms = {
        "exec_with_model": ["codex", "exec", "--model", "gpt-4o-mini", prompt],
        "top_with_model": ["codex", "--model", "gpt-4o-mini", prompt],
        "set_model_then_exec": [["codex", "/model", "gpt-4o-mini"], ["codex", "exec", prompt]],
    }

    results: Dict[str, object] = {}
    # 1) exec --model
    results["exec_with_model"] = try_run(forms["exec_with_model"])  # type: ignore[arg-type]
    if not results["exec_with_model"]["ok"]:
        # 2) codex --model prompt
        results["top_with_model"] = try_run(forms["top_with_model"])  # type: ignore[arg-type]
    # 3) pre-switch + exec
    if not results.get("top_with_model", {"ok": False})["ok"] and not results.get("exec_with_model", {"ok": False})["ok"]:
        pre = try_run(forms["set_model_then_exec"][0])  # type: ignore[index]
        ex = try_run(forms["set_model_then_exec"][1])  # type: ignore[index]
        results["set_model_then_exec"] = {"pre": pre, "exec": ex}

    report["results"] = results
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

