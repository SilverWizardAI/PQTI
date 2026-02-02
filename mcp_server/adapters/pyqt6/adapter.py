"""
PyQt6 Adapter - Implements GIP for PyQt6 applications.

This adapter translates the framework-agnostic GUI Instrumentation Protocol
into PyQt6-specific operations using QTest and Unix sockets.
"""

import logging
from typing import Dict, Any
from ..base import FrameworkAdapter
from .transport import QtTransport

logger = logging.getLogger(__name__)


class PyQt6Adapter(FrameworkAdapter):
    """
    PyQt6 framework adapter.

    Implements the GUI Instrumentation Protocol for PyQt6 applications using:
    - Transport: Unix domain sockets (QLocalSocket)
    - Interactions: QTest (mouseClick, keyClicks, etc.)
    - Element inspection: QWidget APIs

    Usage:
        adapter = PyQt6Adapter()
        await adapter.connect("qt_instrument")
        snapshot = await adapter.snapshot()
        await adapter.click("root/submit_button")
    """

    def __init__(self):
        """Initialize PyQt6 adapter with transport layer."""
        self.transport = QtTransport()
        self._connected = False
        logger.debug("PyQt6Adapter initialized")

    @property
    def framework_name(self) -> str:
        """Return framework identifier."""
        return "pyqt6"

    async def connect(self, target: str) -> Dict[str, Any]:
        """
        Connect to PyQt6 application via Unix socket.

        Args:
            target: QLocalServer name (e.g., "qt_instrument")

        Returns:
            {
                "success": bool,
                "app_info": {
                    "framework": "pyqt6",
                    "transport": "unix_socket",
                    "target": str
                }
            }
        """
        logger.info(f"PyQt6Adapter connecting to: {target}")
        success = await self.transport.connect(target)
        self._connected = success

        if success:
            logger.info(f"PyQt6Adapter connected successfully to: {target}")
        else:
            logger.warning(f"PyQt6Adapter failed to connect to: {target}")

        return {
            "success": success,
            "app_info": {
                "framework": "pyqt6",
                "transport": "unix_socket",
                "target": target
            }
        }

    async def disconnect(self) -> None:
        """Disconnect from PyQt6 application."""
        logger.info("PyQt6Adapter disconnecting")
        self.transport.disconnect()
        self._connected = False
        logger.debug("PyQt6Adapter disconnected")

    async def snapshot(self) -> Dict[str, Any]:
        """
        Get widget tree from PyQt6 application.

        Returns:
            WidgetNode tree (root element with recursive children)
        """
        logger.debug("PyQt6Adapter getting snapshot")
        result = await self.transport.send_request("snapshot", {})
        logger.debug(f"PyQt6Adapter snapshot received: {len(str(result))} bytes")
        return result

    async def click(self, ref: str, button: str = "left") -> Dict[str, Any]:
        """
        Click a PyQt6 widget.

        Args:
            ref: Widget reference (e.g., "root/submit_button")
            button: Mouse button ("left", "right", "middle")

        Returns:
            {"success": bool, "error": str | None}
        """
        logger.debug(f"PyQt6Adapter clicking: {ref} with button: {button}")
        result = await self.transport.send_request("click", {
            "ref": ref,
            "button": button
        })
        logger.debug(f"PyQt6Adapter click result: {result}")
        return result

    async def type_text(self, ref: str, text: str, submit: bool = False) -> Dict[str, Any]:
        """
        Type text into PyQt6 widget.

        Args:
            ref: Widget reference
            text: Text to type
            submit: Press Enter after typing

        Returns:
            {"success": bool, "error": str | None}
        """
        logger.debug(f"PyQt6Adapter typing into: {ref}, text length: {len(text)}, submit: {submit}")
        result = await self.transport.send_request("type", {
            "ref": ref,
            "text": text,
            "submit": submit
        })
        logger.debug(f"PyQt6Adapter type result: {result}")
        return result

    async def ping(self) -> Dict[str, Any]:
        """
        Ping PyQt6 application.

        Returns:
            {"status": "ok" | "error"}
        """
        logger.debug("PyQt6Adapter pinging")
        result = await self.transport.send_request("ping", {})
        logger.debug(f"PyQt6Adapter ping result: {result}")
        return result
