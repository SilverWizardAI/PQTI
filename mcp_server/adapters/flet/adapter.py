"""
Flet Adapter - Implements PQTI protocol for Flet applications.

This adapter translates the framework-agnostic PQTI protocol into
Flet-specific operations.
"""

import logging
from typing import Dict, Any
from ..base import FrameworkAdapter
from .transport import FletTransport

logger = logging.getLogger(__name__)


class FletAdapter(FrameworkAdapter):
    """
    Flet framework adapter.

    Implements the GUI Instrumentation Protocol for Flet applications using:
    - Transport: HTTP (Flet runs web server internally)
    - Interactions: Direct control manipulation via HTTP endpoint
    - Element inspection: Flet control tree traversal

    Usage:
        adapter = FletAdapter()
        await adapter.connect("http://localhost:8551")
        snapshot = await adapter.snapshot()
        await adapter.click("root/submit_button")
    """

    def __init__(self):
        """Initialize Flet adapter with HTTP transport."""
        self.transport = FletTransport()
        self._connected = False
        logger.debug("FletAdapter initialized")

    @property
    def framework_name(self) -> str:
        """Return framework identifier."""
        return "flet"

    async def connect(self, target: str) -> Dict[str, Any]:
        """
        Connect to Flet application via HTTP.

        Args:
            target: HTTP URL (e.g., "http://localhost:8551")

        Returns:
            {
                "success": bool,
                "app_info": {
                    "framework": "flet",
                    "transport": "http",
                    "target": str
                }
            }
        """
        logger.info(f"FletAdapter connecting to: {target}")
        success = await self.transport.connect(target)
        self._connected = success

        if success:
            logger.info(f"FletAdapter connected successfully to: {target}")
        else:
            logger.warning(f"FletAdapter failed to connect to: {target}")

        return {
            "success": success,
            "app_info": {
                "framework": "flet",
                "transport": "http",
                "target": target
            }
        }

    async def disconnect(self) -> None:
        """Disconnect from Flet application."""
        logger.info("FletAdapter disconnecting")
        await self.transport.disconnect()
        self._connected = False
        logger.debug("FletAdapter disconnected")

    async def snapshot(self) -> Dict[str, Any]:
        """
        Get control tree from Flet application.

        Returns:
            ControlNode tree (root control with recursive children)
        """
        logger.debug("FletAdapter getting snapshot")
        result = await self.transport.send_request("snapshot", {})
        logger.debug(f"FletAdapter snapshot received: {len(str(result))} bytes")
        return result

    async def click(self, ref: str, button: str = "left") -> Dict[str, Any]:
        """
        Click a Flet control.

        Args:
            ref: Control reference (e.g., "root/submit_button")
            button: Mouse button (ignored for Flet - always left)

        Returns:
            {"success": bool, "error": str | None}
        """
        logger.debug(f"FletAdapter clicking: {ref}")
        result = await self.transport.send_request("click", {"ref": ref})
        logger.debug(f"FletAdapter click result: {result}")
        return result

    async def type_text(self, ref: str, text: str, submit: bool = False) -> Dict[str, Any]:
        """
        Type text into Flet control.

        Args:
            ref: Control reference
            text: Text to type
            submit: Press Enter after typing (not implemented for Flet)

        Returns:
            {"success": bool, "error": str | None}
        """
        logger.debug(f"FletAdapter typing into: {ref}, text length: {len(text)}")
        result = await self.transport.send_request("type", {
            "ref": ref,
            "text": text,
            "submit": submit
        })
        logger.debug(f"FletAdapter type result: {result}")
        return result

    async def ping(self) -> Dict[str, Any]:
        """
        Ping Flet application.

        Returns:
            {"status": "ok" | "error"}
        """
        logger.debug("FletAdapter pinging")
        result = await self.transport.send_request("ping", {})
        logger.debug(f"FletAdapter ping result: {result}")
        return result
