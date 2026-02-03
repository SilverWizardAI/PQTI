# Adding PQTI Test Automation to Flet Apps

**Complete Guide for Claude Code**

This document contains everything needed to add PQTI test automation to Flet applications. Give this entire document to Claude Code working on your Flet app.

---

## 🎯 Mission

Enable automated testing of Flet applications through Claude Code using the PQTI framework.

**Current State:** PQTI has PyQt6 support (working)
**Goal:** Add Flet support using the same architecture
**Time Required:** ~4 hours to build adapter, then 5 minutes to use

---

## 📋 What You'll Build

### 1. Flet Instrumentation Library
**File:** `flet_instrument/core.py`
**Purpose:** Add to Flet apps to make them testable
**Size:** ~150 lines

### 2. Flet Adapter
**Files:** `mcp_server/adapters/flet/adapter.py`, `transport.py`
**Purpose:** Translate PQTI protocol to Flet APIs
**Size:** ~200 lines total

### 3. MCP Integration
**File:** Update `mcp_server/server.py`
**Purpose:** Register Flet adapter with PQTI
**Size:** ~10 lines

---

## 🏗️ Architecture You're Implementing

```
Claude Code
    ↓ (MCP Protocol)
PQTI MCP Server ✅ Already exists
    ↓ (Uses)
App Controller ✅ Already exists
    ↓ (Dispatches to)
Flet Adapter 🔨 YOU BUILD THIS
    ↓ (HTTP/WebSocket)
Flet App with Instrumentation 🔨 YOU BUILD THIS
```

**Good News:** The hard parts (protocol, MCP server, app controller) are done!
**Your Job:** Build the Flet-specific pieces

---

## 📖 Background: How PQTI Works

### The Pattern (Already Proven with PyQt6)

**Step 1:** Add instrumentation to app
```python
# PyQt6 example:
from qt_instrument import enable_instrumentation
app = QApplication(sys.argv)
enable_instrumentation(app)  # ← Makes app testable
```

**Step 2:** Adapter translates commands
```python
# When Claude says "click button X"
# PyQt6Adapter translates to: QTest.mouseClick(button)
# FletAdapter will translate to: button.on_click(event)
```

**Step 3:** Claude Code tests the app
```
qt_connect → qt_snapshot → qt_click → qt_type
```

### Flet-Specific Approach

**Transport:** HTTP/WebSocket (Flet apps are web-based)
**Commands:** Direct manipulation of Flet controls
**Finding Elements:** Use `data` attribute for IDs

---

## 🛠️ Implementation Guide

### Phase 1: Create Flet Instrumentation Library

**Create file:** `flet_instrument/__init__.py`
```python
"""PQTI instrumentation for Flet applications."""

from .core import enable_instrumentation

__all__ = ["enable_instrumentation"]
```

**Create file:** `flet_instrument/core.py`

```python
"""
Flet instrumentation core.

Adds HTTP endpoint to Flet app for receiving PQTI commands.
"""

import flet as ft
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging

logger = logging.getLogger(__name__)


class InstrumentationHandler(BaseHTTPRequestHandler):
    """HTTP handler for PQTI instrumentation commands."""

    def log_message(self, format, *args):
        """Suppress HTTP server logs."""
        pass

    def do_POST(self):
        """Handle PQTI command requests."""
        try:
            # Read request
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            request = json.loads(body.decode('utf-8'))

            method = request.get('method')
            params = request.get('params', {})
            request_id = request.get('id')

            logger.info(f"Received PQTI command: {method}")

            # Route to handler
            if method == 'ping':
                result = {'status': 'ok'}
            elif method == 'snapshot':
                result = self._create_snapshot()
            elif method == 'click':
                result = self._click_control(params.get('ref'))
            elif method == 'type':
                result = self._type_text(params.get('ref'), params.get('text'))
            else:
                result = {'error': f'Unknown method: {method}'}

            # Send response
            response = {'id': request_id, 'result': result}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            error_response = {'error': str(e)}
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def _create_snapshot(self):
        """Create snapshot of Flet control tree."""
        page = self.server.flet_page
        return self._traverse_control(page, "root")

    def _traverse_control(self, control, ref):
        """Recursively traverse Flet controls."""
        snapshot = {
            "ref": ref,
            "type": type(control).__name__,
            "visible": getattr(control, 'visible', True),
            "disabled": getattr(control, 'disabled', False),
            "properties": self._extract_properties(control),
            "children": []
        }

        # Traverse children
        if hasattr(control, 'controls'):
            for i, child in enumerate(control.controls):
                # Use data attribute if available, otherwise use index
                child_ref = getattr(child, 'data', None)
                if child_ref:
                    child_ref = f"{ref}/{child_ref}"
                else:
                    child_ref = f"{ref}/{type(child).__name__}[{i}]"

                snapshot["children"].append(
                    self._traverse_control(child, child_ref)
                )

        return snapshot

    def _extract_properties(self, control):
        """Extract control properties."""
        props = {}

        # Common properties
        if hasattr(control, 'value'):
            props['value'] = str(control.value)
        if hasattr(control, 'text'):
            props['text'] = str(control.text)
        if hasattr(control, 'data'):
            props['data'] = str(control.data)
        if hasattr(control, 'label'):
            props['label'] = str(control.label)

        return props

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

                # Try indexed reference: TypeName[index] or TypeName[content]
                if '[' in part:
                    type_name = part.split('[')[0]
                    index_str = part.split('[')[1].rstrip(']')

                    # Handle [content] as index 0
                    if index_str == 'content':
                        index = 0
                    else:
                        index = int(index_str)

                    # Use overall index, then verify type matches
                    # (Snapshot uses overall index: Container[11] = 11th child overall)
                    if index < len(current.controls):
                        control = current.controls[index]
                        if type(control).__name__ == type_name:
                            current = control
                            continue
                        else:
                            return None  # Type mismatch
                    else:
                        return None  # Index out of range
                else:
                    return None
            else:
                return None

        return current

    def _click_control(self, ref):
        """Simulate click on control."""
        control = self._find_control_by_ref(ref)

        if not control:
            return {'success': False, 'error': f'Control not found: {ref}'}

        if not hasattr(control, 'on_click'):
            return {'success': False, 'error': f'Control not clickable: {ref}'}

        # Trigger the click handler
        if control.on_click:
            try:
                # Call handler with None event (Flet doesn't require real event)
                control.on_click(None)
                return {'success': True}
            except Exception as e:
                return {'success': False, 'error': f'Click failed: {str(e)}'}
        else:
            return {'success': False, 'error': 'No click handler attached'}

    def _type_text(self, ref, text):
        """Type text into control."""
        control = self._find_control_by_ref(ref)

        if not control:
            return {'success': False, 'error': f'Control not found: {ref}'}

        if not hasattr(control, 'value'):
            return {'success': False, 'error': f'Control not editable: {ref}'}

        try:
            control.value = text
            # Trigger update
            if hasattr(control, 'update'):
                control.update()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': f'Type failed: {str(e)}'}


def enable_instrumentation(page: ft.Page, port: int = 8551):
    """
    Enable PQTI instrumentation for Flet app.

    Args:
        page: Flet Page instance
        port: Port for instrumentation server (default: 8551)

    Usage:
        def main(page: ft.Page):
            enable_instrumentation(page)  # Add this line!

            # Your Flet app code...
            page.add(ft.Text("Hello!"))

        ft.app(target=main)
    """
    logger.info(f"Enabling PQTI instrumentation on port {port}")

    # Create HTTP server
    server = HTTPServer(('localhost', port), InstrumentationHandler)
    server.flet_page = page

    # Run in background thread
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    logger.info(f"PQTI instrumentation enabled at http://localhost:{port}")
    print(f"✓ PQTI instrumentation ready on http://localhost:{port}")
```

**Create file:** `flet_instrument/py.typed`
```
# Marker file for type checking
```

### Phase 2: Create Flet Adapter

**Create directory:** `mcp_server/adapters/flet/`

**Create file:** `mcp_server/adapters/flet/__init__.py`
```python
"""Flet framework adapter for PQTI."""

from .adapter import FletAdapter

__all__ = ["FletAdapter"]
```

**Create file:** `mcp_server/adapters/flet/transport.py`
```python
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
```

**Create file:** `mcp_server/adapters/flet/adapter.py`
```python
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
```

### Phase 3: Register Flet Adapter with PQTI

**Edit file:** `mcp_server/server.py`

**Add import at top:**
```python
from .adapters.flet import FletAdapter
```

**In `main()` function, after registering PyQt6Adapter:**
```python
# Register adapters
controller.register_adapter(PyQt6Adapter())
controller.register_adapter(FletAdapter())  # ← Add this line
logger.info(f"Registered adapters: {controller.list_adapters()}")
```

**Add MCP tool for Flet (in `create_tools()` function):**
```python
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
),
```

**Add handler in `handle_tool_call()` function:**
```python
if name == "flet_connect":
    url = arguments.get("url", "http://localhost:8551")
    logger.info(f"Attempting to connect via Flet adapter: {url}")

    result = await controller.connect(framework="flet", target=url)

    if result.get("success"):
        logger.info(f"Successfully connected to Flet application: {url}")
        return [
            TextContent(
                type="text",
                text=f"✓ Connected to Flet application (url: {url})",
            )
        ]
    else:
        error = result.get("error", "Unknown error")
        logger.warning(f"Failed to connect to Flet application: {error}")
        return [
            TextContent(
                type="text",
                text=f"✗ Failed to connect: {error}",
            )
        ]
```

### Phase 4: Add Dependencies

**Edit:** `pyproject.toml`

Add to `dependencies`:
```toml
[project]
dependencies = [
    "pyqt6>=6.0.0",
    "mcp>=1.0.0",
    "flet>=0.21.0",  # ← Add this
    "aiohttp>=3.9.0"  # ← Add this
]
```

Install dependencies:
```bash
pip install flet aiohttp
```

---

## 🧪 Testing Your Implementation

### Create Test Flet App

**Create file:** `examples/simple_flet_app.py`

```python
import flet as ft
from flet_instrument import enable_instrumentation


def main(page: ft.Page):
    # Enable PQTI instrumentation
    enable_instrumentation(page)

    page.title = "PQTI Flet Test App"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # Counter state
    counter = ft.Text("0", size=30, data="counter_display")

    def increment_counter(e):
        current = int(counter.value)
        counter.value = str(current + 1)
        page.update()

    # Text input and result
    text_input = ft.TextField(
        label="Enter text",
        data="text_input"  # Important: data attribute for PQTI reference
    )

    result_text = ft.Text("", data="result_text")

    def copy_text(e):
        result_text.value = f"You entered: {text_input.value}"
        page.update()

    # Build UI
    page.add(
        ft.Text("PQTI Flet Test App", size=24, weight=ft.FontWeight.BOLD),
        text_input,
        ft.ElevatedButton(
            "Copy to Label",
            on_click=copy_text,
            data="copy_button"  # Important: data attribute
        ),
        result_text,
        ft.ElevatedButton(
            "Click me!",
            on_click=increment_counter,
            data="counter_button"  # Important: data attribute
        ),
        counter,
    )


# Run app
ft.app(target=main)
```

### Test Manually

**Terminal 1 - Start test app:**
```bash
python examples/simple_flet_app.py
```

**Terminal 2 - Test HTTP endpoint:**
```bash
curl -X POST http://localhost:8551/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"ping","params":{},"id":1}'

# Should return: {"id":1,"result":{"status":"ok"}}
```

### Test with Claude Code

**In Claude Code, test the MCP tools:**

```
1. Start your Flet test app
2. Connect: flet_connect(url="http://localhost:8551")
3. Snapshot: Use appropriate MCP snapshot tool
4. Click: Click the counter button
5. Type: Type text into input
6. Verify: Take another snapshot to confirm changes
```

---

## 📝 Adding PQTI to YOUR Flet App

Once the adapter is built and tested, add PQTI to your actual Flet app:

### Step 1: Import and Enable

```python
# At the top of your Flet app
from flet_instrument import enable_instrumentation

def main(page: ft.Page):
    # Add this as first line in your main function
    enable_instrumentation(page)

    # Rest of your app code...
    page.add(...)
```

### Step 2: Add Data Attributes

Add `data` attributes to controls you want to test:

```python
# Before:
username_field = ft.TextField(label="Username")

# After (with data attribute for PQTI):
username_field = ft.TextField(label="Username", data="username_input")
```

### Step 3: Test with Claude Code

Tell Claude Code:

```
"Test my Flet app using PQTI.

The app is at: [your app path]
Run it with: flet run main.py

Test these workflows:
1. [Your workflow 1]
2. [Your workflow 2]
3. [Your workflow 3]"
```

---

## 🎯 Key Flet-Specific Notes

### Control References

**By data attribute (recommended):**
```python
ft.Button("Submit", data="submit_btn")
# Reference: "root/submit_btn"
```

**By type and index:**
```python
ft.Button("First")  # No data
ft.Button("Second")  # No data
# References: "root/ElevatedButton[0]", "root/ElevatedButton[1]"
```

### Event Handling

Flet uses event handlers:
```python
def on_click_handler(e):
    # Your code

button = ft.Button("Click", on_click=on_click_handler)
```

PQTI calls `on_click_handler(None)` directly.

### Threading

Flet is single-threaded, but PQTI runs HTTP server in background thread.
Use `page.update()` for thread-safe UI updates.

---

## ✅ Validation Checklist

Before considering the implementation complete:

- [ ] `flet_instrument/core.py` created
- [ ] `mcp_server/adapters/flet/` directory created
- [ ] `adapter.py` and `transport.py` implemented
- [ ] FletAdapter registered in `server.py`
- [ ] `flet_connect` MCP tool added
- [ ] Dependencies installed (flet, aiohttp)
- [ ] Test app created and runs
- [ ] HTTP endpoint responds to ping
- [ ] MCP tools connect successfully
- [ ] Can get snapshot of control tree
- [ ] Can click buttons (counter increments)
- [ ] Can type text (text appears)
- [ ] Added to actual Flet app
- [ ] Data attributes added to key controls
- [ ] End-to-end test with Claude Code successful

---

## 🚀 Expected Timeline

- **Phase 1:** Flet instrumentation library (1-1.5 hours)
- **Phase 2:** Flet adapter (1-1.5 hours)
- **Phase 3:** MCP integration (30 minutes)
- **Phase 4:** Testing (30-60 minutes)

**Total: ~4 hours** to full Flet support

---

## 📚 Reference Materials

**PQTI Architecture:**
- Technical Spec: `../TECH_SPEC.md`
- Protocol Spec: `../protocol/specification.md`
- PyQt6 Adapter (reference): `../mcp_server/adapters/pyqt6/`

**Flet Documentation:**
- Flet Docs: https://flet.dev
- Flet Controls: https://flet.dev/docs/controls
- Flet Events: https://flet.dev/docs/guides/python/event-handling

---

## 🎉 Success Criteria

You'll know it's working when:

1. ✅ Test Flet app starts with "PQTI instrumentation ready" message
2. ✅ `curl` to HTTP endpoint returns ping response
3. ✅ Claude Code connects with `flet_connect`
4. ✅ Snapshot shows your control tree
5. ✅ Clicks trigger button handlers
6. ✅ Text typing updates controls
7. ✅ Your actual Flet app works the same way

---

## 💡 Troubleshooting

**Problem:** Can't connect to Flet app
- Check app shows "PQTI instrumentation ready" message
- Verify port 8551 not in use: `lsof -i :8551`
- Check firewall not blocking localhost:8551

**Problem:** Control not found
- Take snapshot to see actual control refs
- Ensure control has `data` attribute
- Check control is actually in the page

**Problem:** Click doesn't work
- Verify control has `on_click` handler
- Check handler is not None
- Look for errors in Flet app console

---

## 📞 Getting Help

If you get stuck:

1. Check PyQt6 adapter for reference implementation
2. Review protocol specification
3. Test HTTP endpoint directly with curl
4. Add debug logging to see what's happening

---

**This document contains everything you need. Start with Phase 1 and work through sequentially. Good luck!** 🚀

---

**Full Path to This Document:**
`/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/PQTI/Product/ADDING_PQTI_TO_FLET_APPS.md`

**Last Updated:** 2026-02-02
**Status:** Ready for Implementation
