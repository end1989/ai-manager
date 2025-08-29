"""WebSocket manager for real-time dashboard updates."""

import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

from manager.web.dashboard import DashboardManager


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.dashboard = DashboardManager()
        self.update_task = None
        self.update_interval = 5  # seconds
        
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Start update task if this is the first connection
        if len(self.active_connections) == 1:
            self.update_task = asyncio.create_task(self._periodic_updates())
        
        # Send initial data
        await self._send_dashboard_data(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Stop update task if no connections
        if len(self.active_connections) == 0 and self.update_task:
            self.update_task.cancel()
            self.update_task = None
    
    async def broadcast_update(self, message: Dict[str, Any]):
        """Broadcast update to all connected clients."""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message, default=str)
        
        # Send to all connections, remove failed ones
        failed_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                failed_connections.append(connection)
        
        # Clean up failed connections
        for failed in failed_connections:
            self.disconnect(failed)
    
    async def _periodic_updates(self):
        """Periodically send dashboard updates to all clients."""
        while True:
            try:
                await asyncio.sleep(self.update_interval)
                
                if self.active_connections:
                    dashboard_data = self.dashboard.get_dashboard_data()
                    
                    update_message = {
                        "type": "dashboard_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": dashboard_data.model_dump()
                    }
                    
                    await self.broadcast_update(update_message)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in periodic updates: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _send_dashboard_data(self, websocket: WebSocket):
        """Send current dashboard data to a specific websocket."""
        try:
            dashboard_data = self.dashboard.get_dashboard_data()
            
            message = {
                "type": "dashboard_init",
                "timestamp": datetime.utcnow().isoformat(),
                "data": dashboard_data.model_dump()
            }
            
            await websocket.send_text(json.dumps(message, default=str))
            
        except Exception as e:
            print(f"Error sending dashboard data: {e}")
    
    async def send_task_update(self, task_id: str, status: str, details: Dict[str, Any] = None):
        """Send task-specific update to all clients."""
        update_message = {
            "type": "task_update",
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "status": status,
            "details": details or {}
        }
        
        await self.broadcast_update(update_message)
    
    async def send_system_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Send system alert to all clients."""
        alert_message = {
            "type": "system_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": alert_type,
            "message": message,
            "severity": severity
        }
        
        await self.broadcast_update(alert_message)
    
    def get_connection_count(self) -> int:
        """Get number of active WebSocket connections."""
        return len(self.active_connections)