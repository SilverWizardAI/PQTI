#!/usr/bin/env python3
"""
MCP Server for PyQt6 Instrumentation

This server provides tools for Claude Code to interact with PyQt6 applications.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Framework-agnostic app controller
from .app_controller import AppController
from .adapters.pyqt6 import PyQt6Adapter

# Configure logging to stderr (stdout is for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Global controller instance
controller: Optional[AppController] = None


def create_tools() -> list[Tool]:
    """Define MCP tools for Qt instrumentation."""
    return [
        Tool(
            name="qt_connect",
            description="Connect to a running PyQt6 application with instrumentation enabled",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_name": {
                        "type": "string",
                        "description": "Name of the Qt instrument server (default: qt_instrument)",
                        "default": "qt_instrument",
                    }
                },
            },
        ),
        Tool(
            name="qt_snapshot",
            description="Get a snapshot of the Qt widget tree - shows all widgets, their properties, and hierarchy",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="qt_click",
            description="Click a Qt widget by its reference path",
            inputSchema={
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "description": "Widget reference path (e.g., 'root/copy_button' or 'root/QPushButton[0]')",
                    },
                    "button": {
                        "type": "string",
                        "description": "Mouse button to click (left, right, middle)",
                        "default": "left",
                        "enum": ["left", "right", "middle"],
                    },
                },
                "required": ["ref"],
            },
        ),
        Tool(
            name="qt_type",
            description="Type text into a Qt widget (text input, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "description": "Widget reference path",
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type into the widget",
                    },
                    "submit": {
                        "type": "boolean",
                        "description": "Whether to press Enter after typing",
                        "default": False,
                    },
                },
                "required": ["ref", "text"],
            },
        ),
        Tool(
            name="qt_ping",
            description="Check if connection to Qt application is alive",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


async def handle_tool_call(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls from Claude Code (now framework-agnostic!)."""
    global controller

    logger.info(f"Tool call: {name} with args: {arguments}")

    try:
        if name == "qt_connect":
            server_name = arguments.get("server_name", "qt_instrument")
            logger.info(f"Attempting to connect via PyQt6 adapter: {server_name}")

            # Use controller to connect (framework-agnostic!)
            result = await controller.connect(framework="pyqt6", target=server_name)

            if result.get("success"):
                logger.info(f"Successfully connected to application: {server_name}")
                return [
                    TextContent(
                        type="text",
                        text=f"✓ Connected to Qt application (server: {server_name})",
                    )
                ]
            else:
                error = result.get("error", "Unknown error")
                logger.warning(f"Failed to connect to application: {error}")
                return [
                    TextContent(
                        type="text",
                        text=f"✗ Failed to connect: {error}",
                    )
                ]

        # All other commands require an active connection
        if controller.current_adapter is None:
            logger.warning(f"Tool {name} called without active connection")
            return [
                TextContent(
                    type="text",
                    text="✗ Not connected to Qt application. Use qt_connect first.",
                )
            ]

        if name == "qt_snapshot":
            logger.info("Getting widget snapshot via controller")
            result = await controller.execute("snapshot", {})

            if "error" in result:
                logger.error(f"Snapshot failed: {result['error']}")
                return [TextContent(type="text", text=f"✗ Error: {result['error']}")]

            logger.info(f"Snapshot received with {len(str(result))} bytes")
            snapshot_json = json.dumps(result, indent=2)
            return [TextContent(type="text", text=f"Widget Tree:\n```json\n{snapshot_json}\n```")]

        elif name == "qt_click":
            ref = arguments["ref"]
            button = arguments.get("button", "left")
            logger.info(f"Clicking widget {ref} with button {button}")

            result = await controller.execute("click", {"ref": ref, "button": button})

            if result.get("success"):
                logger.info(f"Successfully clicked widget: {ref}")
                return [TextContent(type="text", text=f"✓ Clicked widget: {ref}")]
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"Failed to click widget {ref}: {error}")
                return [TextContent(type="text", text=f"✗ Failed to click widget: {error}")]

        elif name == "qt_type":
            ref = arguments["ref"]
            text = arguments["text"]
            submit = arguments.get("submit", False)
            logger.info(f"Typing into widget {ref}: '{text}' (submit={submit})")

            result = await controller.execute("type_text", {
                "ref": ref,
                "text": text,
                "submit": submit
            })

            if result.get("success"):
                logger.info(f"Successfully typed into widget: {ref}")
                return [TextContent(type="text", text=f"✓ Typed '{text}' into widget: {ref}")]
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"Failed to type into widget {ref}: {error}")
                return [TextContent(type="text", text=f"✗ Failed to type text: {error}")]

        elif name == "qt_ping":
            logger.debug("Pinging application via controller")
            result = await controller.execute("ping", {})

            if result.get("status") == "ok":
                logger.debug("Ping successful")
                return [TextContent(type="text", text="✓ Connection alive")]
            else:
                logger.warning("Ping failed")
                return [TextContent(type="text", text="✗ Connection issue")]

        else:
            logger.error(f"Unknown tool requested: {name}")
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error handling tool call: {e}", exc_info=True)
        return [TextContent(type="text", text=f"✗ Error: {str(e)}")]


async def main():
    """Main entry point for MCP server."""
    global controller

    logger.info("Starting PyQt Instrument MCP Server")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {sys.path[0]}")

    # Initialize controller and register adapters
    controller = AppController()
    controller.register_adapter(PyQt6Adapter())
    logger.info(f"Registered adapters: {controller.list_adapters()}")

    try:
        server = Server("pyqt-instrument")

        @server.list_tools()
        async def list_tools() -> list[Tool]:
            logger.debug("Tools list requested")
            tools = create_tools()
            logger.info(f"Returning {len(tools)} tools")
            return tools

        @server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            return await handle_tool_call(name, arguments)

        logger.info("Server initialized, starting stdio loop")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Stdio streams ready, running server")
            await server.run(read_stream, write_stream, server.create_initialization_options())

    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down")
    except Exception as e:
        logger.error(f"Fatal error in MCP server: {e}", exc_info=True)
        raise
    finally:
        logger.info("PyQt Instrument MCP Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}", exc_info=True)
        sys.exit(1)
