"""Application service for asynchronous pairs backtest job execution."""

from __future__ import annotations

import logging
import os
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Event, RLock
from typing import Any
from uuid import uuid4

from src.bitcoin_martingale.application.pairs_trading import (
    PairsExecutionCancelledError,
    PairsTradingService,
)
from src.bitcoin_martingale.infrastructure.persistence import LocalPairsBacktestJobsRepository

logger = logging.getLogger(__name__)

ACTIVE_JOB_STATUSES = {"queued", "running"}
TERMINAL_JOB_STATUSES = {"completed", "failed", "cancelled"}


class PairsBacktestJobCancelledError(RuntimeError):
    """Raised when an async pairs backtest job is cancelled before completion."""


class PairsBacktestJobService:
    """Run persisted pairs backtests in the background with observable job status."""

    def __init__(
        self,
        *,
        pairs_service: PairsTradingService | None = None,
        jobs_repository: LocalPairsBacktestJobsRepository | None = None,
        max_workers: int = 2,
        resume_interrupted_jobs: bool = True,
        execution_mode: str = "inline",
        autostart: bool = True,
    ) -> None:
        self.pairs_service = pairs_service or PairsTradingService()
        self.jobs_repository = jobs_repository or LocalPairsBacktestJobsRepository()
        self.max_workers = max_workers
        if execution_mode not in {"inline", "detached"}:
            raise ValueError("execution_mode must be 'inline' or 'detached'")
        self.execution_mode = execution_mode
        self._autostart = autostart
        self._inline_worker_id = f"pairs-inline-worker-{os.getpid()}"
        self._executor = (
            ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix="pairs-job",
            )
            if execution_mode == "inline" and autostart
            else None
        )
        self._futures: dict[str, Future[None]] = {}
        self._cancel_events: dict[str, Event] = {}
        self._lock = RLock()
        self._resume_interrupted_jobs = resume_interrupted_jobs
        self._recover_interrupted_jobs()

    def create_job(
        self,
        request: dict[str, Any] | object,
        *,
        batch_mode: bool = False,
    ) -> dict[str, Any]:
        """Persist and enqueue a new async pairs backtest job."""
        payload = self._to_payload(request)
        now = datetime.now(UTC).isoformat()
        job_id = self._build_job_id()
        job = {
            "job_id": job_id,
            "job_type": "pairs_backtest",
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "finished_at": None,
            "attempt_count": 1,
            "cancel_requested": False,
            "request_payload": payload,
            "batch_mode": batch_mode,
            "preset_id": payload.get("preset_id"),
            "requested_tickers": payload.get("tickers", []),
            "progress": self._build_progress(
                phase="queued",
                message="Pairs job queued for execution.",
                percent=0.0,
                updated_at=now,
            ),
            "worker_id": None,
            "pairs_backtest_id": None,
            "result_available": False,
            "error": None,
            "events": [
                self._build_event(
                    phase="queued",
                    message="Pairs job queued for execution.",
                    timestamp=now,
                    percent=0.0,
                )
            ],
        }
        with self._lock:
            self.jobs_repository.persist_job(job)
            if self._should_autostart():
                self._enqueue_job(job_id)
        logger.info("Queued async pairs backtest job %s", job_id)
        return self.jobs_repository.get_job(job_id)

    def list_jobs(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return persisted pairs jobs ordered from newest to oldest."""
        jobs = self.jobs_repository.list_jobs()
        if status:
            jobs = [job for job in jobs if str(job.get("status")) == status]
        if limit is not None:
            jobs = jobs[:limit]
        return jobs

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Fetch one persisted pairs job manifest."""
        return self.jobs_repository.get_job(job_id)

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        """Request cancellation for a queued or running pairs job."""
        with self._lock:
            job = self.jobs_repository.get_job(job_id)
            status = str(job.get("status", ""))
            if status in TERMINAL_JOB_STATUSES:
                return job

            cancel_event = self._cancel_events.setdefault(job_id, Event())
            cancel_event.set()
            future = self._futures.get(job_id)
            if future is not None:
                future.cancel()

            now = datetime.now(UTC).isoformat()
            job["cancel_requested"] = True
            job["updated_at"] = now
            if status == "queued":
                job["status"] = "cancelled"
                job["finished_at"] = now
                job["progress"] = self._build_progress(
                    phase="cancelled",
                    message="Pairs job cancelled before execution started.",
                    percent=0.0,
                    updated_at=now,
                )
                job["events"] = self._append_event(
                    job,
                    self._build_event(
                        phase="cancelled",
                        message="Pairs job cancelled before execution started.",
                        timestamp=now,
                        percent=0.0,
                    ),
                )
            else:
                job["progress"] = self._build_progress(
                    phase="cancelling",
                    message="Cancellation requested. Waiting for the current step to finish.",
                    percent=float(job["progress"].get("percent", 0.0)),
                    updated_at=now,
                    current_step=job["progress"].get("current_step"),
                    total_steps=job["progress"].get("total_steps"),
                )
                job["events"] = self._append_event(
                    job,
                    self._build_event(
                        phase="cancelling",
                        message="Cancellation requested.",
                        timestamp=now,
                        percent=float(job["progress"].get("percent", 0.0)),
                    ),
                )
            self.jobs_repository.persist_job(job)

        logger.info("Cancellation requested for async pairs backtest job %s", job_id)
        return self.jobs_repository.get_job(job_id)

    def resume_job(self, job_id: str) -> dict[str, Any]:
        """Requeue a failed or cancelled pairs job."""
        with self._lock:
            job = self.jobs_repository.get_job(job_id)
            status = str(job.get("status", ""))
            if status not in {"failed", "cancelled"}:
                return job

            now = datetime.now(UTC).isoformat()
            job.update(
                {
                    "status": "queued",
                    "updated_at": now,
                    "started_at": None,
                    "finished_at": None,
                    "attempt_count": int(job.get("attempt_count", 1)) + 1,
                    "cancel_requested": False,
                    "worker_id": None,
                    "pairs_backtest_id": None,
                    "result_available": False,
                    "error": None,
                    "progress": self._build_progress(
                        phase="queued",
                        message="Pairs job resumed and queued again.",
                        percent=0.0,
                        updated_at=now,
                    ),
                }
            )
            job["events"] = self._append_event(
                job,
                self._build_event(
                    phase="queued",
                    message="Pairs job resumed and queued again.",
                    timestamp=now,
                    percent=0.0,
                ),
            )
            self.jobs_repository.persist_job(job)
            if self._should_autostart():
                self._enqueue_job(job_id)

        logger.info("Resumed async pairs backtest job %s", job_id)
        return self.jobs_repository.get_job(job_id)

    def get_job_response(self, job_id: str) -> dict[str, Any]:
        """Load the persisted pairs response for a completed job."""
        job = self.jobs_repository.get_job(job_id)
        if str(job.get("status")) != "completed" or not job.get("pairs_backtest_id"):
            raise ValueError(f"Pairs job '{job_id}' does not have a completed result yet")
        return self.pairs_service.get_results(str(job["pairs_backtest_id"]))

    def get_job_counts(self) -> dict[str, int]:
        """Summarize persisted pairs jobs by status."""
        counts = {
            "queued": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
        for job in self.jobs_repository.list_jobs():
            status = str(job.get("status", ""))
            if status in counts:
                counts[status] += 1
        return counts

    def latest_job_id(self) -> str | None:
        """Return the newest persisted pairs job id, if any."""
        jobs = self.jobs_repository.list_jobs()
        if not jobs:
            return None
        return str(jobs[0]["job_id"])

    def get_runtime_summary(self) -> dict[str, Any]:
        """Return a lightweight in-memory summary for active workers."""
        with self._lock:
            active_futures = sum(1 for future in self._futures.values() if not future.done())
        return {
            "execution_mode": self.execution_mode,
            "max_workers": self.max_workers,
            "active_futures": active_futures,
        }

    def shutdown(self, *, wait: bool = True, cancel_running: bool = False) -> None:
        """Shut down the inline executor and mark pending futures for cleanup."""
        with self._lock:
            executor = self._executor
            futures = list(self._futures.values())
            if cancel_running:
                for cancel_event in self._cancel_events.values():
                    cancel_event.set()
                for future in futures:
                    future.cancel()
            self._executor = None

        if executor is not None:
            executor.shutdown(wait=wait, cancel_futures=cancel_running)

    def process_next_queued_job(self, *, worker_id: str | None = None) -> dict[str, Any] | None:
        """Claim and process the oldest queued pairs job in the current process."""
        resolved_worker_id = worker_id or self._build_worker_id()
        jobs = sorted(
            self.jobs_repository.list_jobs(),
            key=lambda item: str(item.get("created_at", "")),
        )
        for job in jobs:
            if str(job.get("status")) != "queued":
                continue

            job_id = str(job["job_id"])
            if not self.jobs_repository.acquire_execution_lock(job_id, resolved_worker_id):
                continue

            lock_transferred = False
            try:
                current_job = self.jobs_repository.get_job(job_id)
                if str(current_job.get("status")) != "queued":
                    continue
                lock_transferred = True
                self._execute_job(
                    job_id,
                    worker_id=resolved_worker_id,
                    lock_acquired=True,
                )
                return self.jobs_repository.get_job(job_id)
            finally:
                if not lock_transferred:
                    self.jobs_repository.release_execution_lock(job_id)
        return None

    def run_worker_loop(
        self,
        *,
        worker_id: str | None = None,
        once: bool = False,
        poll_interval_seconds: float = 2.0,
        max_jobs: int | None = None,
    ) -> dict[str, Any]:
        """Process queued pairs jobs in the foreground until the stop condition is met."""
        resolved_worker_id = worker_id or self._build_worker_id()
        processed_jobs = 0
        logger.info(
            "Starting async pairs worker %s in %s mode",
            resolved_worker_id,
            self.execution_mode,
        )
        while True:
            job = self.process_next_queued_job(worker_id=resolved_worker_id)
            if job is not None:
                processed_jobs += 1
                if once or (max_jobs is not None and processed_jobs >= max_jobs):
                    break
                continue

            if once:
                break

            time.sleep(poll_interval_seconds)
        return {
            "worker_id": resolved_worker_id,
            "processed_jobs": processed_jobs,
            "execution_mode": self.execution_mode,
        }

    def _enqueue_job(self, job_id: str) -> None:
        if self._executor is None:
            raise RuntimeError("Inline executor is not available in detached job mode")
        if not self.jobs_repository.acquire_execution_lock(job_id, self._inline_worker_id):
            logger.info(
                "Skipped inline enqueue for %s because another worker already claimed it",
                job_id,
            )
            return
        self._cancel_events[job_id] = Event()
        self._futures[job_id] = self._executor.submit(
            self._execute_job,
            job_id,
            worker_id=self._inline_worker_id,
            lock_acquired=True,
        )

    def _execute_job(
        self,
        job_id: str,
        *,
        worker_id: str | None = None,
        lock_acquired: bool = False,
    ) -> None:
        resolved_worker_id = worker_id or self._inline_worker_id
        try:
            self._start_job(
                job_id,
                worker_id=resolved_worker_id,
                lock_acquired=lock_acquired,
            )
            job = self.jobs_repository.get_job(job_id)
            request_payload = dict(job.get("request_payload", {}))
            batch_mode = bool(job.get("batch_mode", False))
            runner = self.pairs_service.run_batch if batch_mode else self.pairs_service.run_backtest
            response = runner(
                **request_payload,
                progress_callback=lambda payload: self._update_progress(job_id, payload),
                should_cancel=lambda: self._is_cancel_requested(job_id),
            )
            result_id = (
                str(response["pairs_backtest_id"])
                if isinstance(response, dict) and response.get("pairs_backtest_id")
                else None
            )
            self._finish_job(
                job_id,
                status="completed",
                message="Pairs backtest job completed successfully.",
                percent=100.0,
                result_id=result_id,
            )
            logger.info("Async pairs backtest job %s completed with result %s", job_id, result_id)
        except (PairsBacktestJobCancelledError, PairsExecutionCancelledError):
            self._finish_job(
                job_id,
                status="cancelled",
                message="Pairs backtest job cancelled.",
                percent=self._current_progress_percent(job_id),
            )
            logger.info("Async pairs backtest job %s cancelled", job_id)
        except Exception as exc:  # pragma: no cover - defensive logging path
            logger.exception("Async pairs backtest job %s failed", job_id)
            self._finish_job(
                job_id,
                status="failed",
                message="Pairs backtest job failed.",
                percent=self._current_progress_percent(job_id),
                error=str(exc),
            )
        finally:
            with self._lock:
                self._futures.pop(job_id, None)
                self._cancel_events.pop(job_id, None)
            self.jobs_repository.release_execution_lock(job_id)

    def _start_job(
        self,
        job_id: str,
        *,
        worker_id: str,
        lock_acquired: bool = False,
    ) -> None:
        if not lock_acquired and not self.jobs_repository.acquire_execution_lock(job_id, worker_id):
            raise RuntimeError(f"Pairs job '{job_id}' is already claimed by another worker")
        with self._lock:
            job = self.jobs_repository.get_job(job_id)
            if str(job.get("status")) == "cancelled" or bool(job.get("cancel_requested")):
                raise PairsBacktestJobCancelledError(
                    "Pairs job was cancelled before execution started"
                )

            now = datetime.now(UTC).isoformat()
            job["status"] = "running"
            job["started_at"] = now
            job["updated_at"] = now
            job["worker_id"] = worker_id
            job["progress"] = self._build_progress(
                phase="booting",
                message="Preparing pairs execution context.",
                percent=2.0,
                updated_at=now,
            )
            job["events"] = self._append_event(
                job,
                self._build_event(
                    phase="booting",
                    message="Pairs job execution started.",
                    timestamp=now,
                    percent=2.0,
                ),
            )
            self.jobs_repository.persist_job(job)

    def _update_progress(self, job_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            job = self.jobs_repository.get_job(job_id)
            if str(job.get("status")) in TERMINAL_JOB_STATUSES:
                return

            if bool(job.get("cancel_requested")):
                raise PairsBacktestJobCancelledError("Pairs job cancellation requested")

            now = datetime.now(UTC).isoformat()
            phase = str(payload.get("phase", "running"))
            message = str(payload.get("message", "Pairs backtest job running."))
            percent = float(payload.get("percent", job["progress"].get("percent", 0.0)))
            current_step = payload.get("current_step")
            total_steps = payload.get("total_steps")
            job["updated_at"] = now
            job["progress"] = self._build_progress(
                phase=phase,
                message=message,
                percent=percent,
                updated_at=now,
                current_step=current_step,
                total_steps=total_steps,
            )
            job["events"] = self._append_event(
                job,
                self._build_event(
                    phase=phase,
                    message=message,
                    timestamp=now,
                    percent=percent,
                ),
            )
            self.jobs_repository.persist_job(job)

    def _finish_job(
        self,
        job_id: str,
        *,
        status: str,
        message: str,
        percent: float,
        result_id: str | None = None,
        error: str | None = None,
    ) -> None:
        with self._lock:
            job = self.jobs_repository.get_job(job_id)
            now = datetime.now(UTC).isoformat()
            job["status"] = status
            job["updated_at"] = now
            job["finished_at"] = now
            job["pairs_backtest_id"] = result_id
            job["result_available"] = bool(result_id) and status == "completed"
            job["error"] = error
            job["progress"] = self._build_progress(
                phase=status,
                message=message,
                percent=percent,
                updated_at=now,
                current_step=job["progress"].get("current_step"),
                total_steps=job["progress"].get("total_steps"),
            )
            job["events"] = self._append_event(
                job,
                self._build_event(
                    phase=status,
                    message=message if error is None else f"{message} {error}",
                    timestamp=now,
                    percent=percent,
                ),
            )
            self.jobs_repository.persist_job(job)

    def _recover_interrupted_jobs(self) -> None:
        recovered_job_ids: list[str] = []
        for job in self.jobs_repository.list_jobs():
            if str(job.get("status")) not in ACTIVE_JOB_STATUSES:
                continue

            self.jobs_repository.release_execution_lock(str(job["job_id"]))
            now = datetime.now(UTC).isoformat()
            job["status"] = "queued" if self._resume_interrupted_jobs else "failed"
            job["updated_at"] = now
            job["started_at"] = None
            job["finished_at"] = None if self._resume_interrupted_jobs else now
            job["attempt_count"] = int(job.get("attempt_count", 1)) + 1
            job["cancel_requested"] = False
            job["worker_id"] = None
            job["pairs_backtest_id"] = None
            job["result_available"] = False
            job["error"] = (
                None
                if self._resume_interrupted_jobs
                else (
                    "Pairs job interrupted by process restart before completion. "
                    "Resume to rerun it."
                )
            )
            job["progress"] = self._build_progress(
                phase="queued" if self._resume_interrupted_jobs else "failed",
                message=(
                    "Pairs job recovered after process restart and queued again."
                    if self._resume_interrupted_jobs
                    else "Pairs job interrupted by process restart before completion."
                ),
                percent=float(job.get("progress", {}).get("percent", 0.0)),
                updated_at=now,
                current_step=job.get("progress", {}).get("current_step"),
                total_steps=job.get("progress", {}).get("total_steps"),
            )
            job["events"] = self._append_event(
                job,
                self._build_event(
                    phase="queued" if self._resume_interrupted_jobs else "failed",
                    message=(
                        "Pairs job recovered after process restart and queued again."
                        if self._resume_interrupted_jobs
                        else "Pairs job interrupted by process restart before completion."
                    ),
                    timestamp=now,
                    percent=float(job.get("progress", {}).get("percent", 0.0)),
                ),
            )
            self.jobs_repository.persist_job(job)
            if self._resume_interrupted_jobs and self._should_autostart():
                recovered_job_ids.append(str(job["job_id"]))

        for job_id in recovered_job_ids:
            logger.info("Recovered interrupted async pairs job %s after process restart", job_id)
            self._enqueue_job(job_id)

    def _is_cancel_requested(self, job_id: str) -> bool:
        cancel_event = self._cancel_events.get(job_id)
        if cancel_event is not None and cancel_event.is_set():
            return True
        try:
            job = self.jobs_repository.get_job(job_id)
        except FileNotFoundError:
            return False
        return bool(job.get("cancel_requested"))

    def _current_progress_percent(self, job_id: str) -> float:
        try:
            job = self.jobs_repository.get_job(job_id)
        except FileNotFoundError:
            return 0.0
        return float(job.get("progress", {}).get("percent", 0.0))

    def _build_job_id(self) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"pairs_job_{timestamp}_{uuid4().hex[:8]}"

    def _build_worker_id(self) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"pairs_worker_{timestamp}_{uuid4().hex[:6]}"

    def _should_autostart(self) -> bool:
        return self.execution_mode == "inline" and self._autostart

    def _build_progress(
        self,
        *,
        phase: str,
        message: str,
        percent: float,
        updated_at: str,
        current_step: Any = None,
        total_steps: Any = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "phase": phase,
            "message": message,
            "percent": round(percent, 2),
            "updated_at": updated_at,
        }
        if current_step is not None:
            payload["current_step"] = int(current_step)
        if total_steps is not None:
            payload["total_steps"] = int(total_steps)
        return payload

    def _build_event(
        self,
        *,
        phase: str,
        message: str,
        timestamp: str,
        percent: float,
        level: str = "info",
    ) -> dict[str, Any]:
        return {
            "timestamp": timestamp,
            "level": level,
            "phase": phase,
            "message": message,
            "percent": round(percent, 2),
        }

    def _append_event(self, job: dict[str, Any], event: dict[str, Any]) -> list[dict[str, Any]]:
        events = list(job.get("events", []))
        if (
            events
            and events[-1]["phase"] == event["phase"]
            and events[-1]["message"] == event["message"]
        ):
            events[-1] = event
            return events[-50:]
        events.append(event)
        return events[-50:]

    def _to_payload(self, request: dict[str, Any] | object) -> dict[str, Any]:
        if isinstance(request, dict):
            return dict(request)

        model_dump = getattr(request, "model_dump", None)
        if callable(model_dump):
            payload = model_dump()
            if isinstance(payload, dict):
                return payload

        raise TypeError("Unsupported pairs backtest job payload")
