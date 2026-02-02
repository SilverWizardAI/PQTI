"""
Abstract base class for framework adapters.

Each adapter implements the GUI Instrumentation Protocol for a specific
framework (PyQt6, Electron, Playwright, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class FrameworkAdapter(ABC):
    """
    Abstract base class for framework adapters.

    Adapters implement the GUI Instrumentation Protocol (GIP) for specific
    GUI frameworks. Each adapter:
    - Chooses optimal transport (Unix socket, WebSocket, etc.)
    - Translates protocol methods to framework-specific APIs
    - Returns responses in standardized format

    Example implementations:
    - PyQt6Adapter: Uses Unix sockets + QTest
    - ElectronAdapter: Uses WebSocket + Electron IPC
    - PlaywrightAdapter: Uses CDP WebSocket + Playwright APIs
    """

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """
        Return framework identifier.

        Examples: "pyqt6", "electron", "playwright", "wpf"

        Returns:
            Framework name (lowercase, alphanumeric)
        """
        pass

    @abstractmethod
    async def connect(self, target: str) -> Dict[str, Any]:
        """
        Connect to instrumented application.

        Args:
            target: Connection target (server name, URL, etc.)
                   - PyQt6: "qt_instrument" (server name)
                   - Electron: "ws://localhost:9222" (WebSocket URL)
                   - Playwright: "http://localhost:9222" (CDP URL)

        Returns:
            {
                "success": bool,
                "app_info": {
                    "framework": str,    # Framework name
                    "version": str,      # Framework version
                    "transport": str,    # Transport type
                    "pid": int,          # Process ID (optional)
                    "title": str         # App title (optional)
                }
            }
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from application.

        Clean up resources:
        - Close sockets/connections
        - Clear state
        - Release handles
        """
        pass

    @abstractmethod
    async def snapshot(self) -> Dict[str, Any]:
        """
        Get snapshot of UI element tree.

        Returns:
            WidgetNode (root element with recursive children)
            {
                "ref": "root",
                "type": "MainWindow",
                "objectName": "main_window" | null,
                "visible": bool,
                "enabled": bool,
                "geometry": {"x": int, "y": int, "width": int, "height": int},
                "properties": {...},  # Framework-specific properties
                "children": [...]     # Recursive WidgetNode list
            }
        """
        pass

    @abstractmethod
    async def click(self, ref: str, button: str = "left") -> Dict[str, Any]:
        """
        Click a UI element.

        Args:
            ref: Element reference (e.g., "root/submit_button")
            button: Mouse button ("left", "right", "middle")

        Returns:
            {"success": bool, "error": str | None}
        """
        pass

    @abstractmethod
    async def type_text(self, ref: str, text: str, submit: bool = False) -> Dict[str, Any]:
        """
        Type text into a UI element.

        Args:
            ref: Element reference
            text: Text to type
            submit: Press Enter after typing

        Returns:
            {"success": bool, "error": str | None}
        """
        pass

    @abstractmethod
    async def ping(self) -> Dict[str, Any]:
        """
        Check if connection is alive.

        Returns:
            {
                "status": "ok" | "error",
                "timestamp": int,      # Unix timestamp (optional)
                "uptime": int          # Seconds since connection (optional)
            }
        """
        pass

    # Optional methods (can be overridden for framework-specific features)

    async def select(self, ref: str, value: str = None, index: int = None,
                     text: str = None) -> Dict[str, Any]:
        """
        Select option from dropdown/combobox (optional).

        Args:
            ref: Element reference
            value: Option value
            index: Option index (0-based)
            text: Option display text

        Returns:
            {
                "success": bool,
                "selected": {"value": str, "index": int, "text": str}
            }
        """
        return {
            "success": False,
            "error": f"select() not implemented for {self.framework_name}"
        }

    async def wait_for(self, ref: str, condition: str = "visible",
                       timeout: int = 5000) -> Dict[str, Any]:
        """
        Wait for element condition (optional).

        Args:
            ref: Element reference
            condition: "visible", "hidden", "enabled", "disabled"
            timeout: Timeout in milliseconds

        Returns:
            {"success": bool, "error": str | None}
        """
        return {
            "success": False,
            "error": f"wait_for() not implemented for {self.framework_name}"
        }
