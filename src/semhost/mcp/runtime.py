from __future__ import annotations

import time
import secrets
from typing import Dict, Optional


class JobRecord:
    def __init__(self, tool: str, params: dict) -> None:
        self.id = f"J-{secrets.token_hex(4)}"
        self.tool = tool
        self.params = params
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.ok: Optional[bool] = None
        self.error: Optional[str] = None
        # Cooperative cancel flag; workers should poll between phases
        self.cancel_requested: bool = False


class JobManager:
    """Minimal in-process job registry.

    MVP: this is a placeholder; excel.inspect worker will plug in here later.
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}

    def create(self, tool: str, params: dict) -> JobRecord:
        jr = JobRecord(tool, params)
        self._jobs[jr.id] = jr
        return jr

    def get(self, job_id: str) -> Optional[JobRecord]:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        jr = self._jobs.get(job_id)
        if not jr:
            return False
        jr.cancel_requested = True
        return True

    def is_cancelled(self, job_id: str) -> bool:
        jr = self._jobs.get(job_id)
        return bool(jr and jr.cancel_requested)


JOB_MANAGER = JobManager()
