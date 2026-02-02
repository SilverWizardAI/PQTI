"""
Qt IPC Client for communicating with instrumented PyQt6 applications.

Uses QLocalSocket protocol to connect to the Qt application's IPC server.
"""

import asyncio
import json
import logging
import socket
import struct
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class QtInstrumentClient:
    """Client for communicating with Qt instrumentation server."""

    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.request_id = 0

    async def connect(self, server_name: str = "qt_instrument") -> bool:
        """
        Connect to Qt application's IPC server.

        On Unix/macOS, QLocalServer creates a Unix domain socket.
        """
        try:
            # On macOS, QLocalServer creates socket in system temp directory
            # Try common locations
            import tempfile
            import os

            temp_dir = tempfile.gettempdir()
            socket_path = os.path.join(temp_dir, server_name)

            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            # Run blocking connect in executor to avoid blocking event loop
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.connect, socket_path
            )

            self.connected = True
            logger.info(f"Connected to Qt app at {socket_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Qt app: {e}")
            self.connected = False
            return False

    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the Qt application and wait for response."""
        if not self.connected or self.socket is None:
            raise RuntimeError("Not connected to Qt application")

        self.request_id += 1
        request = {"id": self.request_id, "method": method, "params": params}

        try:
            # Send request
            request_json = json.dumps(request)
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.sendall, request_json.encode("utf-8")
            )

            # Receive response (simple read until we get valid JSON)
            # For PoC, we'll read in chunks until we get a complete JSON
            response_data = b""
            while True:
                chunk = await asyncio.get_event_loop().run_in_executor(
                    None, self.socket.recv, 4096
                )
                if not chunk:
                    raise ConnectionError("Connection closed by Qt application")

                response_data += chunk

                # Try to parse as JSON
                try:
                    response = json.loads(response_data.decode("utf-8"))
                    break
                except json.JSONDecodeError:
                    # Not complete yet, keep reading
                    continue

            logger.info(f"Received response: {response}")
            return response.get("result", {})

        except Exception as e:
            logger.error(f"Error sending request: {e}", exc_info=True)
            self.connected = False
            raise

    def disconnect(self):
        """Disconnect from Qt application."""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False
