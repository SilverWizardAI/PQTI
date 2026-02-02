"""
HTTP transport for Flet applications.

Communicates with Flet apps via HTTP (instrumentation endpoint).
"""

import aiohttp
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FletTransport:
    """HTTP transport for Flet instrumentation."""

    def __init__(self):
        self.base_url = None
        self.session = None
        self.connected = False

    async def connect(self, url: str) -> bool:
        """
        Connect to Flet app instrumentation endpoint.

        Args:
            url: HTTP URL (e.g., "http://localhost:8551")

        Returns:
            True if connected successfully
        """
        self.base_url = url.rstrip('/')
        self.session = aiohttp.ClientSession()

        try:
            # Test connection with ping
            result = await self.send_request("ping", {})
            if result.get('status') == 'ok':
                self.connected = True
                logger.info(f"Connected to Flet app at {url}")
                return True
            else:
                logger.error(f"Ping failed: {result}")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to {url}: {e}")
            if self.session:
                await self.session.close()
            return False

    async def disconnect(self) -> None:
        """Close connection to Flet app."""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("Disconnected from Flet app")

    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send request to Flet app instrumentation server.

        Args:
            method: Command method (ping, snapshot, click, type)
            params: Method parameters

        Returns:
            Result dictionary

        Raises:
            RuntimeError: If not connected
        """
        if not self.connected and method != "ping":
            raise RuntimeError("Not connected to Flet app")

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }

        try:
            async with self.session.post(
                f"{self.base_url}/",
                json=request,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('result', {})
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP {response.status}: {error_text}")
                    return {'error': f'HTTP {response.status}'}

        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return {'error': str(e)}
