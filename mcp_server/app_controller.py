"""
Framework-agnostic Application Controller.

Routes commands to appropriate framework adapters.
Implements the core business logic without knowing about Qt, Electron, or
any specific framework.
"""

import logging
from typing import Dict, Any, Optional
from .adapters.base import FrameworkAdapter

logger = logging.getLogger(__name__)


class AppController:
    """
    Framework-agnostic application controller.

    The controller:
    - Registers framework adapters (PyQt6, Electron, Playwright, etc.)
    - Routes commands to the appropriate adapter
    - Manages connection lifecycle
    - Validates protocol compliance

    This class knows WHAT to do, not HOW to do it. The "HOW" is delegated
    to framework-specific adapters.

    Usage:
        controller = AppController()
        controller.register_adapter(PyQt6Adapter())
        controller.register_adapter(ElectronAdapter())

        await controller.connect(framework="pyqt6", target="qt_instrument")
        snapshot = await controller.execute("snapshot", {})
        await controller.execute("click", {"ref": "root/button", "button": "left"})
    """

    def __init__(self):
        """Initialize the app controller."""
        self.adapters: Dict[str, FrameworkAdapter] = {}
        self.current_adapter: Optional[FrameworkAdapter] = None
        logger.info("AppController initialized")

    def register_adapter(self, adapter: FrameworkAdapter) -> None:
        """
        Register a framework adapter.

        Args:
            adapter: Framework adapter instance

        Raises:
            ValueError: If adapter with same name already registered
        """
        framework_name = adapter.framework_name

        if framework_name in self.adapters:
            logger.warning(f"Adapter '{framework_name}' already registered, replacing")

        self.adapters[framework_name] = adapter
        logger.info(f"Registered adapter: {framework_name}")
        logger.debug(f"Available adapters: {list(self.adapters.keys())}")

    def get_adapter(self, framework_name: str) -> Optional[FrameworkAdapter]:
        """
        Get a registered adapter by name.

        Args:
            framework_name: Framework identifier (e.g., "pyqt6", "electron")

        Returns:
            FrameworkAdapter instance or None if not found
        """
        return self.adapters.get(framework_name)

    def list_adapters(self) -> list[str]:
        """
        List all registered adapter names.

        Returns:
            List of framework names
        """
        return list(self.adapters.keys())

    async def connect(self, framework: str, target: str) -> Dict[str, Any]:
        """
        Connect to an application using specified framework adapter.

        Args:
            framework: Framework name (e.g., "pyqt6", "electron")
            target: Connection target (server name, URL, etc.)

        Returns:
            {
                "success": bool,
                "error": str | None,
                "app_info": {...}
            }
        """
        logger.info(f"AppController connecting: framework={framework}, target={target}")

        # Find adapter
        adapter = self.adapters.get(framework)
        if not adapter:
            available = list(self.adapters.keys())
            error_msg = f"Unknown framework: {framework}. Available: {available}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "available_frameworks": available
            }

        # Attempt connection
        try:
            result = await adapter.connect(target)

            if result.get("success"):
                self.current_adapter = adapter
                logger.info(f"AppController connected successfully via {framework}")
            else:
                logger.warning(f"AppController connection failed via {framework}: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"AppController connection error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def disconnect(self) -> Dict[str, Any]:
        """
        Disconnect from current application.

        Returns:
            {"success": bool}
        """
        if not self.current_adapter:
            logger.warning("AppController disconnect called but not connected")
            return {"success": True}  # Already disconnected

        try:
            await self.current_adapter.disconnect()
            framework_name = self.current_adapter.framework_name
            self.current_adapter = None
            logger.info(f"AppController disconnected from {framework_name}")
            return {"success": True}

        except Exception as e:
            logger.error(f"AppController disconnect error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def execute(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command on the current adapter.

        Args:
            method: Method name (e.g., "snapshot", "click", "type")
            params: Method parameters

        Returns:
            Method result (format depends on method)

        Raises:
            RuntimeError: If not connected to an application
        """
        # Check connection
        if not self.current_adapter:
            error_msg = "Not connected to any application. Use connect() first."
            logger.error(f"AppController execute failed: {error_msg}")
            return {"error": error_msg}

        # Validate method exists
        handler = getattr(self.current_adapter, method, None)
        if not handler or not callable(handler):
            error_msg = f"Unknown method: {method}"
            logger.error(f"AppController execute failed: {error_msg}")
            return {"error": error_msg}

        # Execute method
        try:
            logger.debug(f"AppController executing: {method} with params: {params}")
            result = await handler(**params)
            logger.debug(f"AppController execute result: {type(result)}")
            return result

        except TypeError as e:
            # Likely parameter mismatch
            error_msg = f"Invalid parameters for {method}: {e}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}

        except Exception as e:
            error_msg = f"Error executing {method}: {e}"
            logger.error(error_msg, exc_info=True)
            return {"error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """
        Get controller status.

        Returns:
            {
                "connected": bool,
                "framework": str | None,
                "available_adapters": list[str]
            }
        """
        return {
            "connected": self.current_adapter is not None,
            "framework": self.current_adapter.framework_name if self.current_adapter else None,
            "available_adapters": self.list_adapters()
        }
