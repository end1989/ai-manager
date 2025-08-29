"""Web dashboard components for task monitoring."""

from .dashboard import DashboardManager
from .websocket import WebSocketManager

__all__ = ["DashboardManager", "WebSocketManager"]