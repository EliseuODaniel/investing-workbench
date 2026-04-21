"""Persistence for asynchronous backtest job manifests."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class LocalBacktestJobsRepository:
    """Store async backtest job manifests on local disk."""

    def __init__(self, base_dir: Path | str = "runs/jobs") -> None:
        self.base_dir = Path(base_dir)

    def persist_job(self, job_payload: dict[str, Any]) -> dict[str, Any]:
        """Persist or replace one job manifest."""
        job_id = str(job_payload["job_id"])
        artifact_dir = self.base_dir / job_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = artifact_dir / "manifest.json"
        tmp_path = manifest_path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(job_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(manifest_path)
        return job_payload

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Load one persisted backtest job manifest."""
        manifest_path = self.base_dir / job_id / "manifest.json"
        last_error: Exception | None = None
        for _ in range(5):
            try:
                if not manifest_path.exists():
                    raise FileNotFoundError(f"Backtest job not found: {job_id}")
                return json.loads(manifest_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError) as exc:
                last_error = exc
                time.sleep(0.01)

        if last_error is None:
            raise FileNotFoundError(f"Backtest job not found: {job_id}")
        raise last_error

    def list_jobs(self) -> list[dict[str, Any]]:
        """List persisted jobs from newest to oldest."""
        if not self.base_dir.exists():
            return []

        manifests: list[dict[str, Any]] = []
        for manifest_path in sorted(self.base_dir.glob("*/manifest.json"), reverse=True):
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))

        manifests.sort(key=lambda manifest: str(manifest.get("created_at", "")), reverse=True)
        return manifests

    def acquire_execution_lock(self, job_id: str, worker_id: str) -> bool:
        """Try to acquire an exclusive execution lock for one job."""
        lock_path = self._lock_path(job_id)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "worker_id": worker_id,
            "acquired_at": datetime.now(UTC).isoformat(),
        }
        try:
            with lock_path.open("x", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
        except FileExistsError:
            return False
        return True

    def release_execution_lock(self, job_id: str) -> None:
        """Release the exclusive execution lock for one job."""
        lock_path = self._lock_path(job_id)
        if lock_path.exists():
            lock_path.unlink()

    def _lock_path(self, job_id: str) -> Path:
        return self.base_dir / job_id / ".execution.lock"
