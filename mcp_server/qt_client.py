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
        import tempfile
        import os

        temp_dir = tempfile.gettempdir()
        socket_path = os.path.join(temp_dir, server_name)

        logger.info(f"Attempting to connect to Qt IPC server at: {socket_path}")
        logger.info(f"Temp directory: {temp_dir}")

        # Check if socket exists
        if not os.path.exists(socket_path):
            logger.error(f"Socket file does not exist: {socket_path}")
            logger.error("Make sure the Qt application is running with instrumentation enabled")
            logger.error("The app should call: enable_instrumentation(app)")
            return False

        logger.info(f"Socket file found: {socket_path}")

        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            logger.debug("Created Unix socket")

            # Run blocking connect in executor to avoid blocking event loop
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.connect, socket_path
            )

            self.connected = True
            logger.info(f"✓ Successfully connected to Qt app at {socket_path}")
            return True

        except FileNotFoundError as e:
            logger.error(f"Socket file not found: {socket_path}")
            logger.error(f"Error details: {e}")
            self.connected = False
            return False
        except PermissionError as e:
            logger.error(f"Permission denied accessing socket: {socket_path}")
            logger.error(f"Error details: {e}")
            self.connected = False
            return False
        except ConnectionRefusedError as e:
            logger.error(f"Connection refused by Qt application at: {socket_path}")
            logger.error("The Qt application may not be listening on this socket")
            logger.error(f"Error details: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Qt app at {socket_path}: {e}", exc_info=True)
            self.connected = False
            return False

    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the Qt application and wait for response."""
        if not self.connected or self.socket is None:
            logger.error("Attempted to send request while not connected")
            raise RuntimeError("Not connected to Qt application")

        self.request_id += 1
        request = {"id": self.request_id, "method": method, "params": params}

        try:
            # Send request
            request_json = json.dumps(request)
            logger.debug(f"Sending request: {method} (id={self.request_id})")
            logger.debug(f"Request data: {request_json}")
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.sendall, request_json.encode("utf-8")
            )
            logger.debug("Request sent, waiting for response")

            # Receive response (simple read until we get valid JSON)
            # For PoC, we'll read in chunks until we get a complete JSON
            response_data = b""
            while True:
                chunk = await asyncio.get_event_loop().run_in_executor(
                    None, self.socket.recv, 4096
                )
                if not chunk:
                    logger.error("Connection closed by Qt application while waiting for response")
                    raise ConnectionError("Connection closed by Qt application")

                response_data += chunk
                logger.debug(f"Received chunk: {len(chunk)} bytes (total: {len(response_data)})")

                # Try to parse as JSON
                try:
                    response = json.loads(response_data.decode("utf-8"))
                    logger.debug(f"Parsed complete response: {response}")
                    break
                except json.JSONDecodeError as e:
                    # Not complete yet, keep reading
                    logger.debug(f"Incomplete JSON, continuing to read: {e}")
                    continue

            logger.info(f"Request {method} completed successfully")
            return response.get("result", {})

        except Exception as e:
            logger.error(f"Error sending request {method}: {e}", exc_info=True)
            self.connected = False
            raise

    def disconnect(self):
        """Disconnect from Qt application."""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False
