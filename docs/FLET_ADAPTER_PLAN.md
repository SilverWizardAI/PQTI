# Flet Adapter Implementation Plan

## Overview

Create a Flet adapter for PQTI to enable testing Flet applications through Claude Code.

## Flet Architecture Understanding

**What is Flet?**
- Python framework for building Flutter apps
- Runs as web app (default), desktop, or mobile
- Uses Flet controls (Button, TextField, etc.)
- Has a control tree (similar to widget tree)
- Internally runs a web server (usually on localhost:8550)

**How Flet Works:**
```
Python Code → Flet Controls → Flutter Engine → Web/Desktop/Mobile
```

**Key Insight:** Flet apps are essentially web apps with a Python API!

## Implementation Strategy

### Option 1: WebSocket/HTTP Communication (Recommended)

Since Flet apps run a web server, we can:
1. Add instrumentation endpoint to Flet app
2. FletAdapter connects via HTTP/WebSocket
3. Send commands, receive control tree

**Advantages:**
- Clean separation (no need to modify Flet internals)
- Works across all Flet platforms (web, desktop, mobile)
- Standard web protocols

### Option 2: Direct Python API

Since Flet is Python, we could:
1. Inject instrumentation code directly into Flet app
2. Use Flet's internal APIs to inspect/manipulate controls
3. Communicate via Unix socket (like PyQt6)

**Advantages:**
- Direct access to Flet controls
- No HTTP overhead

**We'll use Option 1** (WebSocket) as it's cleaner and more aligned with Flet's architecture.

## File Structure

```
mcp_server/adapters/flet/
├── __init__.py
├── adapter.py           # FletAdapter(FrameworkAdapter)
└── transport.py         # WebSocket/HTTP transport

flet_instrument/
├── __init__.py
└── core.py             # Flet instrumentation code
```

## Flet Instrumentation Library

### Core Functionality Needed

```python
# flet_instrument/core.py

import flet as ft
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class InstrumentationHandler(BaseHTTPRequestHandler):
    """HTTP handler for instrumentation requests."""

    def do_POST(self):
        """Handle instrumentation commands."""
        length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(length))

        method = data.get('method')
        params = data.get('params', {})

        if method == 'snapshot':
            result = self._create_snapshot()
        elif method == 'click':
            result = self._click_control(params['ref'])
        elif method == 'type':
            result = self._type_text(params['ref'], params['text'])
        # ... etc

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _create_snapshot(self):
        """Create snapshot of Flet control tree."""
        # Access the Flet page
        page = self.server.flet_page
        return self._traverse_controls(page)

    def _traverse_controls(self, control, path="root"):
        """Recursively traverse Flet controls."""
        return {
            "ref": path,
            "type": type(control).__name__,
            "visible": control.visible if hasattr(control, 'visible') else True,
            "disabled": control.disabled if hasattr(control, 'disabled') else False,
            "properties": self._extract_properties(control),
            "children": [
                self._traverse_controls(child, f"{path}/{i}")
                for i, child in enumerate(getattr(control, 'controls', []))
            ]
        }

    def _extract_properties(self, control):
        """Extract control-specific properties."""
        props = {}
        if hasattr(control, 'value'):
            props['value'] = control.value
        if hasattr(control, 'text'):
            props['text'] = control.text
        if hasattr(control, 'data'):
            props['data'] = control.data
        return props

    def _click_control(self, ref):
        """Simulate click on control."""
        control = self._find_control_by_ref(ref)
        if control and hasattr(control, 'on_click'):
            # Trigger the click handler
            if control.on_click:
                control.on_click(None)  # Call with dummy event
            return {"success": True}
        return {"success": False, "error": "Control not found or not clickable"}

    def _type_text(self, ref, text):
        """Type text into control."""
        control = self._find_control_by_ref(ref)
        if control and hasattr(control, 'value'):
            control.value = text
            control.update()  # Trigger Flet update
            return {"success": True}
        return {"success": False, "error": "Control not found or not editable"}

    def _find_control_by_ref(self, ref):
        """Find control by reference path."""
        if not ref or ref == "root":
            return self.server.flet_page

        parts = ref.split('/')[1:]  # Skip 'root'
        current = self.server.flet_page

        for part in parts:
            if not current:
                return None

            # Try to find by data attribute first
            if hasattr(current, 'controls'):
                found = False
                for control in current.controls:
                    if getattr(control, 'data', None) == part:
                        current = control
                        found = True
                        break

                if found:
                    continue

                # Try indexed reference: TypeName[index]
                if '[' in part:
                    type_name = part.split('[')[0]
                    index = int(part.split('[')[1].rstrip(']'))

                    matching = [
                        c for c in current.controls
                        if type(c).__name__ == type_name
                    ]

                    if index < len(matching):
                        current = matching[index]
                        continue  # Continue to next part of path
                    else:
                        return None
                else:
                    return None
            else:
                return None

        return current


def enable_instrumentation(page: ft.Page, port: int = 8551):
    """
    Enable PQTI instrumentation for a Flet app.

    Args:
        page: Flet page instance
        port: Port for instrumentation server (default: 8551)

    Usage:
        def main(page: ft.Page):
            enable_instrumentation(page)  # Add this line!

            # Your Flet app code...
            page.add(ft.Text("Hello!"))
    """
    # Create HTTP server in background thread
    server = HTTPServer(('localhost', port), InstrumentationHandler)
    server.flet_page = page

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print(f"PQTI instrumentation enabled on http://localhost:{port}")
```

## Flet Adapter Implementation

```python
# mcp_server/adapters/flet/adapter.py

import logging
from typing import Dict, Any
from ..base import FrameworkAdapter
from .transport import FletTransport

logger = logging.getLogger(__name__)


class FletAdapter(FrameworkAdapter):
    """Adapter for Flet applications."""

    def __init__(self):
        self.transport = FletTransport()
        self._connected = False

    @property
    def framework_name(self) -> str:
        return "flet"

    async def connect(self, target: str) -> Dict[str, Any]:
        """
        Connect to Flet application.

        Args:
            target: HTTP URL (e.g., "http://localhost:8551")
        """
        success = await self.transport.connect(target)
        self._connected = success

        return {
            "success": success,
            "app_info": {
                "framework": "flet",
                "transport": "http",
                "target": target
            }
        }

    async def disconnect(self) -> None:
        await self.transport.disconnect()
        self._connected = False

    async def snapshot(self) -> Dict[str, Any]:
        return await self.transport.send_request("snapshot", {})

    async def click(self, ref: str, button: str = "left") -> Dict[str, Any]:
        return await self.transport.send_request("click", {
            "ref": ref,
            "button": button
        })

    async def type_text(self, ref: str, text: str, submit: bool = False) -> Dict[str, Any]:
        return await self.transport.send_request("type", {
            "ref": ref,
            "text": text,
            "submit": submit
        })

    async def ping(self) -> Dict[str, Any]:
        return await self.transport.send_request("ping", {})
```

```python
# mcp_server/adapters/flet/transport.py

import aiohttp
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FletTransport:
    """HTTP transport for Flet applications."""

    def __init__(self):
        self.base_url = None
        self.session = None
        self.connected = False

    async def connect(self, url: str) -> bool:
        """Connect to Flet app instrumentation endpoint."""
        self.base_url = url
        self.session = aiohttp.ClientSession()

        try:
            # Test connection with ping
            async with self.session.post(
                f"{self.base_url}/instrument",
                json={"method": "ping", "params": {}}
            ) as response:
                if response.status == 200:
                    self.connected = True
                    logger.info(f"Connected to Flet app at {url}")
                    return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            if self.session:
                await self.session.close()
            return False

        return False

    async def disconnect(self) -> None:
        if self.session:
            await self.session.close()
        self.connected = False

    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to Flet app."""
        if not self.connected:
            raise RuntimeError("Not connected to Flet app")

        request = {
            "method": method,
            "params": params,
            "id": 1
        }

        async with self.session.post(
            f"{self.base_url}/instrument",
            json=request
        ) as response:
            result = await response.json()
            return result
```

## MCP Tool for Flet

```python
# mcp_server/server.py - Add Flet tool

Tool(
    name="flet_connect",
    description="Connect to Flet application with instrumentation enabled",
    inputSchema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Instrumentation URL (default: http://localhost:8551)",
                "default": "http://localhost:8551"
            }
        }
    }
)

# In main():
controller.register_adapter(FletAdapter())
```

## Testing Plan

### 1. Create Simple Flet Test App

```python
# examples/simple_flet_app.py

import flet as ft
from flet_instrument import enable_instrumentation


def main(page: ft.Page):
    # Enable instrumentation
    enable_instrumentation(page)

    page.title = "PQTI Flet Test App"

    # Counter
    counter = ft.Text("0", size=30)

    def increment(e):
        counter.value = str(int(counter.value) + 1)
        page.update()

    # Text input
    text_input = ft.TextField(
        label="Enter text",
        data="text_input"  # Reference ID
    )

    result_text = ft.Text("", data="result_text")

    def copy_text(e):
        result_text.value = f"You entered: {text_input.value}"
        page.update()

    page.add(
        ft.Text("PQTI Flet Test App", size=20, weight="bold"),
        text_input,
        ft.ElevatedButton("Copy to Label", on_click=copy_text, data="copy_button"),
        result_text,
        ft.ElevatedButton("Click me!", on_click=increment, data="counter_button"),
        counter,
    )


ft.app(target=main)
```

### 2. Test with Claude Code

```python
# Test sequence
await controller.connect(framework="flet", target="http://localhost:8551")
snapshot = await controller.snapshot()
await controller.type("root/0/text_input", "Hello Flet!")
await controller.click("root/1/copy_button")
await controller.click("root/4/counter_button")
```

## Implementation Timeline

1. **Phase 1** (1 hour): Create flet_instrument library
2. **Phase 2** (1 hour): Create FletAdapter + transport
3. **Phase 3** (30 min): Register adapter, add MCP tool
4. **Phase 4** (30 min): Test with simple Flet app
5. **Phase 5** (1 hour): Test with real Flet app

**Total:** ~4 hours to full Flet support!

## Challenges & Solutions

### Challenge 1: Finding Controls

**Problem:** Flet doesn't have objectName like Qt

**Solution:** Use `data` attribute for IDs:
```python
ft.TextField(data="username_input")  # Reference as root/.../username_input
```

### Challenge 2: Event Simulation

**Problem:** Can't use QTest-like event simulation

**Solution:** Call event handlers directly:
```python
if control.on_click:
    control.on_click(None)  # Trigger directly
```

### Challenge 3: Thread Safety

**Problem:** Flet runs in main thread, instrumentation in background

**Solution:** Use Flet's `page.update()` for thread-safe updates

## Benefits

Once implemented:
- ✅ Test Flet apps alongside PyQt6 apps
- ✅ Same PQTI protocol for both
- ✅ Same MCP tools in Claude Code
- ✅ One testing framework for all your apps!

## Next Steps

After dogfooding with your apps:
1. Refine Flet instrumentation based on real usage
2. Add more Flet-specific features (scroll, hover, etc.)
3. Document Flet-specific patterns
4. Contribute back to PQTI repo
