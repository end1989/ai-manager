"""Artifact management for runs and tasks."""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from manager.config import settings
from manager.store.models import ArtifactModel, DatabaseManager


class ArtifactManager:
    """Manages run directories, logs, and artifacts with retention policy."""

    def __init__(self):
        self.runs_dir = settings.runs_dir
        self.artifacts_dir = settings.artifacts_dir
        self.max_size_bytes = settings.max_artifact_size_mb * 1024 * 1024
        self.db = DatabaseManager()

    def create_run_directory(self, run_id: str) -> Path:
        """Create isolated run directory."""
        run_path = self.runs_dir / run_id
        run_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (run_path / "workdir").mkdir(exist_ok=True)
        (run_path / "logs").mkdir(exist_ok=True)
        (run_path / "artifacts").mkdir(exist_ok=True)
        
        return run_path

    def write_task_spec(self, run_id: str, task_spec: Dict[str, Any]) -> Path:
        """Write task spec JSON to run directory."""
        run_path = self.runs_dir / run_id
        spec_path = run_path / "task_spec.json"
        
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(task_spec, f, indent=2, default=str)
        
        return spec_path

    def read_task_spec(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Read task spec from run directory."""
        spec_path = self.runs_dir / run_id / "task_spec.json"
        
        if not spec_path.exists():
            return None
            
        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def write_worker_report(self, run_id: str, report: Dict[str, Any]) -> Path:
        """Write worker task report to run directory."""
        run_path = self.runs_dir / run_id
        report_path = run_path / "worker_report.json"
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        
        return report_path

    def read_worker_report(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Read worker report from run directory."""
        report_path = self.runs_dir / run_id / "worker_report.json"
        
        if not report_path.exists():
            return None
            
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def write_pr_proposal(self, run_id: str, proposal: Dict[str, Any]) -> Path:
        """Write PR proposal to run directory."""
        run_path = self.runs_dir / run_id
        proposal_path = run_path / "pr_proposal.json"
        
        with open(proposal_path, "w", encoding="utf-8") as f:
            json.dump(proposal, f, indent=2, default=str)
        
        return proposal_path

    def read_pr_proposal(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Read PR proposal from run directory.""" 
        proposal_path = self.runs_dir / run_id / "pr_proposal.json"
        
        if not proposal_path.exists():
            return None
            
        try:
            with open(proposal_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def write_log_file(self, run_id: str, log_name: str, content: str) -> Path:
        """Write log file to run directory."""
        log_path = self.runs_dir / run_id / "logs" / f"{log_name}.log"
        
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return log_path

    def read_log_file(self, run_id: str, log_name: str) -> Optional[str]:
        """Read log file from run directory."""
        log_path = self.runs_dir / run_id / "logs" / f"{log_name}.log"
        
        if not log_path.exists():
            return None
            
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                return f.read()
        except IOError:
            return None

    def store_artifact(self, run_id: str, artifact_name: str, content: bytes) -> Optional[Path]:
        """Store artifact with size validation."""
        if len(content) > self.max_size_bytes:
            return None  # Artifact too large
        
        artifact_path = self.runs_dir / run_id / "artifacts" / artifact_name
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(artifact_path, "wb") as f:
            f.write(content)
        
        # Log artifact in database
        artifact_model = ArtifactModel(
            run_id=run_id,
            artifact_type="file",
            name=artifact_name,
            path=str(artifact_path),
            size_bytes=len(content),
        )
        
        with self.db.get_session() as session:
            session.add(artifact_model)
            session.commit()
        
        return artifact_path

    def get_run_artifacts(self, run_id: str) -> List[Dict[str, Any]]:
        """Get list of artifacts for a run."""
        artifacts_path = self.runs_dir / run_id / "artifacts"
        
        if not artifacts_path.exists():
            return []
        
        artifacts = []
        for artifact_file in artifacts_path.iterdir():
            if artifact_file.is_file():
                stat = artifact_file.stat()
                artifacts.append({
                    "name": artifact_file.name,
                    "path": str(artifact_file),
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                })
        
        return artifacts

    def cleanup_old_runs(self) -> Dict[str, int]:
        """Clean up old run directories based on retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.artifact_retention_days)
        
        cleaned_runs = 0
        total_size_freed = 0
        
        if not self.runs_dir.exists():
            return {"runs_cleaned": 0, "bytes_freed": 0}
        
        for run_dir in self.runs_dir.iterdir():
            if run_dir.is_dir():
                # Check creation time
                stat = run_dir.stat()
                created_time = datetime.fromtimestamp(stat.st_ctime)
                
                if created_time < cutoff_date:
                    # Calculate size before deletion
                    size = self._get_directory_size(run_dir)
                    
                    # Remove directory
                    shutil.rmtree(run_dir, ignore_errors=True)
                    
                    cleaned_runs += 1
                    total_size_freed += size
        
        return {
            "runs_cleaned": cleaned_runs,
            "bytes_freed": total_size_freed,
        }

    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of run artifacts."""
        run_path = self.runs_dir / run_id
        
        if not run_path.exists():
            return {"error": "Run directory not found"}
        
        summary = {
            "run_id": run_id,
            "run_path": str(run_path),
            "created_at": datetime.fromtimestamp(run_path.stat().st_ctime),
            "size_bytes": self._get_directory_size(run_path),
            "has_task_spec": (run_path / "task_spec.json").exists(),
            "has_worker_report": (run_path / "worker_report.json").exists(), 
            "has_pr_proposal": (run_path / "pr_proposal.json").exists(),
            "artifacts": self.get_run_artifacts(run_id),
            "log_files": [],
        }
        
        # List log files
        logs_path = run_path / "logs"
        if logs_path.exists():
            for log_file in logs_path.iterdir():
                if log_file.is_file() and log_file.suffix == ".log":
                    stat = log_file.stat()
                    summary["log_files"].append({
                        "name": log_file.stem,
                        "path": str(log_file),
                        "size_bytes": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime),
                    })
        
        return summary

    def _get_directory_size(self, path: Path) -> int:
        """Calculate total size of directory."""
        total_size = 0
        
        if path.is_file():
            return path.stat().st_size
        
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except (OSError, PermissionError):
                    pass  # Skip files we can't access
        
        return total_size

    def export_run_archive(self, run_id: str, archive_path: Optional[Path] = None) -> Optional[Path]:
        """Create archive of run directory."""
        run_path = self.runs_dir / run_id
        
        if not run_path.exists():
            return None
        
        if archive_path is None:
            archive_path = self.artifacts_dir / f"{run_id}.tar.gz"
        
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create tar.gz archive
        import tarfile
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(run_path, arcname=run_id)
        
        return archive_path