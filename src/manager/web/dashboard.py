"""Web dashboard for task monitoring and management."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from manager.store.models import DatabaseManager


class TaskStats(BaseModel):
    """Task statistics model."""
    total_tasks: int
    completed_tasks: int
    running_tasks: int
    failed_tasks: int
    pending_tasks: int
    completion_rate: float
    avg_execution_time: float


class SystemMetrics(BaseModel):
    """System metrics model."""
    uptime: str
    active_connections: int
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    queue_depth: int


class DashboardData(BaseModel):
    """Complete dashboard data model."""
    task_stats: TaskStats
    system_metrics: SystemMetrics
    recent_tasks: List[Dict[str, Any]]
    performance_chart: Dict[str, Any]  # Mixed types for chart data
    alert_count: int


class DashboardManager:
    """Manages dashboard data and real-time updates."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.start_time = datetime.utcnow()
        
    def get_dashboard_data(self) -> DashboardData:
        """Get complete dashboard data."""
        
        # Get task statistics
        task_stats = self._get_task_stats()
        
        # Get system metrics
        system_metrics = self._get_system_metrics()
        
        # Get recent tasks
        recent_tasks = self._get_recent_tasks()
        
        # Get performance chart data
        performance_chart = self._get_performance_chart()
        
        # Get alert count
        alert_count = self._get_alert_count()
        
        return DashboardData(
            task_stats=task_stats,
            system_metrics=system_metrics,
            recent_tasks=recent_tasks,
            performance_chart=performance_chart,
            alert_count=alert_count
        )
    
    def _get_task_stats(self) -> TaskStats:
        """Calculate task statistics."""
        
        try:
            # Get all tasks from database
            all_tasks = self.db.list_tasks()
            
            total = len(all_tasks)
            completed = len([t for t in all_tasks if t.status == "completed"])
            running = len([t for t in all_tasks if t.status == "running"])
            failed = len([t for t in all_tasks if t.status == "failed"])
            pending = len([t for t in all_tasks if t.status == "pending"])
            
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            # Calculate average execution time for completed tasks
            # Note: Tasks don't have completed_at, so we'll use a default avg time
            # In future, we could join with runs table for actual execution times
            avg_time = 2.5  # Default average time in minutes
            
            return TaskStats(
                total_tasks=total,
                completed_tasks=completed,
                running_tasks=running,
                failed_tasks=failed,
                pending_tasks=pending,
                completion_rate=round(completion_rate, 1),
                avg_execution_time=round(avg_time, 2)
            )
            
        except Exception as e:
            print(f"Error getting task stats: {e}")
            return TaskStats(
                total_tasks=0,
                completed_tasks=0,
                running_tasks=0,
                failed_tasks=0,
                pending_tasks=0,
                completion_rate=0.0,
                avg_execution_time=0.0
            )
    
    def _get_system_metrics(self) -> SystemMetrics:
        """Get system performance metrics."""
        
        try:
            import psutil
            
            uptime = str(datetime.utcnow() - self.start_time).split('.')[0]
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            # Get queue depth from database
            running_tasks = len([t for t in self.db.list_tasks() if t.status == "running"])
            pending_tasks = len([t for t in self.db.list_tasks() if t.status == "pending"])
            queue_depth = running_tasks + pending_tasks
            
            return SystemMetrics(
                uptime=uptime,
                active_connections=0,  # Will be updated by WebSocket manager
                memory_usage=round(memory.percent, 1),
                cpu_usage=round(cpu, 1),
                disk_usage=round(disk.percent, 1),
                queue_depth=queue_depth
            )
            
        except ImportError:
            # Fallback if psutil not available
            uptime = str(datetime.utcnow() - self.start_time).split('.')[0]
            return SystemMetrics(
                uptime=uptime,
                active_connections=0,
                memory_usage=0.0,
                cpu_usage=0.0,
                disk_usage=0.0,
                queue_depth=0
            )
    
    def _get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tasks for dashboard display."""
        
        try:
            tasks = self.db.list_tasks(limit=limit)
            
            recent = []
            for task in tasks[:limit]:
                # Calculate duration (simplified since tasks don't have completed_at)
                duration = "0m"
                if task.created_at:
                    start = task.created_at
                    if isinstance(start, str):
                        start = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
                    
                    if task.status == "completed":
                        # Estimate completed duration
                        duration = "2m"
                    else:
                        # Calculate running duration
                        duration_mins = int((datetime.utcnow() - start).total_seconds() / 60)
                        duration = f"{duration_mins}m"
                
                recent.append({
                    "task_id": task.task_id,
                    "title": task.title[:50] + "..." if len(task.title) > 50 else task.title,
                    "status": task.status,
                    "duration": duration,
                    "created_at": task.created_at or "Unknown"
                })
            
            return recent
            
        except Exception as e:
            print(f"Error getting recent tasks: {e}")
            return []
    
    def _get_performance_chart(self) -> Dict[str, List[float]]:
        """Get performance chart data for the last 24 hours."""
        
        try:
            # Get tasks from last 24 hours
            now = datetime.utcnow()
            hours = []
            completed_counts = []
            failed_counts = []
            
            # Generate hourly buckets for last 24 hours
            for i in range(24):
                hour_start = now - timedelta(hours=23-i)
                hour_end = hour_start + timedelta(hours=1)
                
                # Count completed and failed tasks in this hour
                all_tasks = self.db.list_tasks()
                completed_in_hour = 0
                failed_in_hour = 0
                
                for task in all_tasks:
                    # Since tasks don't have completed_at, use updated_at for completed/failed tasks
                    if task.status in ["completed", "failed"] and task.updated_at:
                        updated_time = task.updated_at
                        if isinstance(updated_time, str):
                            updated_time = datetime.fromisoformat(str(updated_time).replace("Z", "+00:00"))
                        if hour_start <= updated_time < hour_end:
                            if task.status == "completed":
                                completed_in_hour += 1
                            elif task.status == "failed":
                                failed_in_hour += 1
                
                hours.append(hour_start.strftime("%H:00"))
                completed_counts.append(completed_in_hour)
                failed_counts.append(failed_in_hour)
            
            return {
                "hours": hours,
                "completed": completed_counts,
                "failed": failed_counts
            }
            
        except Exception as e:
            print(f"Error getting performance chart: {e}")
            # Return dummy data
            hours = [f"{i:02d}:00" for i in range(24)]
            return {
                "hours": hours,
                "completed": [0] * 24,
                "failed": [0] * 24
            }
    
    def _get_alert_count(self) -> int:
        """Get count of active alerts."""
        
        try:
            # Count failed tasks in last hour as alerts
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            
            all_tasks = self.db.list_tasks()
            alerts = 0
            
            for task in all_tasks:
                if task.status == "failed" and task.updated_at:
                    updated_time = task.updated_at
                    if isinstance(updated_time, str):
                        updated_time = datetime.fromisoformat(str(updated_time).replace("Z", "+00:00"))
                    if updated_time >= hour_ago:
                        alerts += 1
            
            return alerts
            
        except Exception as e:
            print(f"Error getting alert count: {e}")
            return 0