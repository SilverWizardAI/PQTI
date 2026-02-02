# Adapter Development Guide
## How to Add Support for New Frameworks

This guide explains how to implement a new framework adapter for the GUI Instrumentation Protocol.

---

## Overview

A **framework adapter** implements the GIP protocol for a specific GUI framework (PyQt6, Electron, Playwright, etc.). Each adapter:

1. **Chooses optimal transport** (Unix sockets, WebSocket, etc.)
2. **Translates protocol methods** to framework-specific APIs
3. **Returns standardized responses** defined in the protocol

---

## Quick Start

### 1. Create Adapter Directory

```bash
mkdir -p mcp_server/adapters/myframework
touch mcp_server/adapters/myframework/__init__.py
touch mcp_server/adapters/myframework/adapter.py
touch mcp_server/adapters/myframework/transport.py
```

### 2. Implement FrameworkAdapter

```python
# mcp_server/adapters/myframework/adapter.py

from ..base import FrameworkAdapter
from .transport import MyFrameworkTransport

class MyFrameworkAdapter(FrameworkAdapter):
    """Adapter for MyFramework applications."""

    def __init__(self):
        self.transport = MyFrameworkTransport()
        self._connected = False

    @property
    def framework_name(self) -> str:
        return "myframework"

    async def connect(self, target: str) -> dict:
        success = await self.transport.connect(target)
        self._connected = success
        return {
            "success": success,
            "app_info": {
                "framework": "myframework",
                "transport": "websocket",  # or whatever you use
                "target": target
            }
        }

    async def disconnect(self) -> None:
        await self.transport.disconnect()
        self._connected = False

    async def snapshot(self) -> dict:
        return await self.transport.send_request("snapshot", {})

    async def click(self, ref: str, button: str = "left") -> dict:
        return await self.transport.send_request("click", {
            "ref": ref,
            "button": button
        })

    async def type_text(self, ref: str, text: str, submit: bool = False) -> dict:
        return await self.transport.send_request("type", {
            "ref": ref,
            "text": text,
            "submit": submit
        })

    async def ping(self) -> dict:
        return await self.transport.send_request("ping", {})
```

### 3. Implement Transport Layer

The transport layer is framework-specific and handles low-level communication.

**Example: WebSocket Transport**

```python
# mcp_server/adapters/myframework/transport.py

import asyncio
import json
import websockets

class MyFrameworkTransport:
    """WebSocket transport for MyFramework."""

    def __init__(self):
        self.websocket = None
        self.connected = False

    async def connect(self, target: str) -> bool:
        """Connect to MyFramework app via WebSocket."""
        try:
            self.websocket = await websockets.connect(target)
            self.connected = True
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
        self.connected = False

    async def send_request(self, method: str, params: dict) -> dict:
        """Send JSON-RPC request over WebSocket."""
        if not self.connected:
            raise RuntimeError("Not connected")

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }

        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        return json.loads(response)["result"]
```

### 4. Register Adapter

```python
# mcp_server/server.py

from .adapters.myframework import MyFrameworkAdapter

# In main():
controller = AppController()
controller.register_adapter(PyQt6Adapter())
controller.register_adapter(MyFrameworkAdapter())  # Add your adapter!
```

### 5. Add MCP Tool (Optional)

If you want a framework-specific connection tool:

```python
# mcp_server/server.py

Tool(
    name="myframework_connect",
    description="Connect to MyFramework application",
    inputSchema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "WebSocket URL (e.g., ws://localhost:9222)"
            }
        }
    }
)

# In handle_tool_call:
if name == "myframework_connect":
    url = arguments.get("url", "ws://localhost:9222")
    result = await controller.connect(framework="myframework", target=url)
    # ...
```

---

## Protocol Requirements

Your adapter **must** return responses in the exact format specified in the protocol.

### Snapshot Response

```python
{
  "ref": "root",
  "type": "Window",
  "objectName": "main_window" | null,
  "visible": True,
  "enabled": True,
  "geometry": {"x": 0, "y": 0, "width": 800, "height": 600},
  "properties": {},  # Framework-specific
  "children": [...]  # Recursive
}
```

### Click Response

```python
{"success": True, "error": None}
# or
{"success": False, "error": "Element not found"}
```

### Type Response

```python
{"success": True, "error": None}
```

### Ping Response

```python
{"status": "ok", "timestamp": 1704234567}
```

---

## Best Practices

### 1. Separate Transport from Logic

✅ **Good:**
```
adapter.py        # High-level protocol implementation
transport.py      # Low-level communication
```

❌ **Bad:**
```
adapter.py        # Everything mixed together
```

### 2. Use Async/Await

All adapter methods are async. Use `async def` and `await`.

### 3. Handle Errors Gracefully

```python
async def click(self, ref: str, button: str = "left") -> dict:
    try:
        result = await self.transport.send_request("click", {...})
        return result
    except ElementNotFound:
        return {"success": False, "error": f"Element not found: {ref}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 4. Log Everything

```python
import logging
logger = logging.getLogger(__name__)

async def connect(self, target: str) -> dict:
    logger.info(f"Connecting to {target}")
    # ...
    logger.info("Connected successfully")
```

### 5. Follow Protocol Exactly

Don't add extra fields or change response formats. If you need extensions, prefix them:

```python
{
  "success": True,
  "myframework_specific_data": {...}  # OK (prefixed)
}
```

---

## Framework-Specific Examples

### Example 1: Electron Adapter (WebSocket)

```python
class ElectronAdapter(FrameworkAdapter):
    @property
    def framework_name(self) -> str:
        return "electron"

    async def connect(self, target: str) -> dict:
        # target = "ws://localhost:9222"
        # Connect via Electron's remote debugging port
        ...
```

### Example 2: Playwright Adapter (CDP)

```python
class PlaywrightAdapter(FrameworkAdapter):
    @property
    def framework_name(self) -> str:
        return "playwright"

    async def snapshot(self) -> dict:
        # Use Playwright's page.evaluate() to get DOM tree
        elements = await self.page.evaluate("""
            // JavaScript to traverse DOM
        """)
        return self._convert_to_widget_node(elements)
```

### Example 3: WPF Adapter (Named Pipes)

```python
class WpfAdapter(FrameworkAdapter):
    @property
    def framework_name(self) -> str:
        return "wpf"

    async def connect(self, target: str) -> dict:
        # target = "\\\\.\\pipe\\wpf_instrument"
        # Connect via Windows named pipes
        ...
```

---

## Testing Your Adapter

### 1. Unit Tests

```python
import pytest
from mcp_server.adapters.myframework import MyFrameworkAdapter

@pytest.mark.asyncio
async def test_adapter_connect():
    adapter = MyFrameworkAdapter()
    result = await adapter.connect("ws://localhost:9222")
    assert result["success"] == True
    assert result["app_info"]["framework"] == "myframework"
```

### 2. Integration Tests

Test with a real application:

```bash
# Start your app with instrumentation
python examples/my_app.py &

# Test adapter
python -c "
import asyncio
from mcp_server.adapters.myframework import MyFrameworkAdapter

async def test():
    adapter = MyFrameworkAdapter()
    await adapter.connect('ws://localhost:9222')
    snapshot = await adapter.snapshot()
    print(snapshot)

asyncio.run(test())
"
```

---

## Checklist

Before submitting your adapter:

- [ ] Implements all required methods (connect, disconnect, snapshot, click, type_text, ping)
- [ ] Returns responses in protocol format
- [ ] Uses async/await throughout
- [ ] Has proper error handling
- [ ] Includes logging
- [ ] Has transport layer separated
- [ ] Follows naming conventions
- [ ] Includes `__init__.py` with exports
- [ ] Has basic tests
- [ ] Documentation updated

---

## Resources

- [Protocol Specification](../protocol/specification.md)
- [JSON Schema](../protocol/schema.json)
- [PyQt6 Adapter Reference](../mcp_server/adapters/pyqt6/)
- [Tech Spec](../TECH_SPEC.md)

---

## Getting Help

- Check existing adapters in `mcp_server/adapters/`
- Read the protocol specification
- Open an issue on GitHub
- Review the PyQt6 adapter as a reference implementation

Happy adapter development! 🚀
