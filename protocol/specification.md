# GUI Instrumentation Protocol (GIP) v1.0
## Language-Independent GUI Automation Protocol

**Status:** Specification
**Version:** 1.0.0
**Date:** 2026-02-02

---

## Overview

The GUI Instrumentation Protocol (GIP) is a **language-independent**, **framework-agnostic** protocol for automating GUI applications. It defines a standard way to:

- Connect to instrumented applications
- Inspect UI element hierarchies
- Interact with UI elements (click, type, etc.)
- Query application state

### Design Principles

1. **Language Independence**: Can be implemented in Python, C++, JavaScript, etc.
2. **Framework Agnostic**: Works with Qt, Electron, Web, WPF, etc.
3. **Transport Neutral**: Works over Unix sockets, WebSockets, named pipes, etc.
4. **Simple**: Based on JSON-RPC 2.0
5. **Extensible**: Easy to add new methods

### Relationship to JSON-RPC 2.0

This protocol builds on JSON-RPC 2.0, inheriting its:
- Request/response model
- ID matching for async operations
- Error handling conventions

Reference: https://www.jsonrpc.org/specification

---

## Transport Layer

### Transport Independence

The protocol does NOT mandate a specific transport. Implementations choose the best transport for their framework:

| Framework | Recommended Transport | Reason |
|-----------|----------------------|--------|
| PyQt6/Qt | Unix domain sockets | Native QLocalServer support |
| Electron | WebSocket or IPC | Node.js native support |
| Web/Browser | WebSocket | Chrome DevTools Protocol |
| WPF/Windows | Named pipes | Windows native support |

### Message Format

All messages are **UTF-8 encoded JSON**.

**No framing required**: Each message is a complete JSON object. Implementations may:
- Use newline delimiters (`\n`)
- Use length prefixes (4-byte header)
- Parse incrementally until valid JSON

**Example (Unix socket):**
```
Client → Server: {"jsonrpc":"2.0","method":"ping","id":1}\n
Server → Client: {"jsonrpc":"2.0","result":{"status":"ok"},"id":1}\n
```

---

## Core Concepts

### Widget Reference (Ref)

A **ref** is a hierarchical path uniquely identifying a UI element.

**Format:** `"root/path/to/element"`

**Strategies:**
1. **By Object Name**: `"root/submit_button"` (if element has unique name/ID)
2. **By Type and Index**: `"root/QPushButton[2]"` (third QPushButton under root)
3. **Mixed**: `"root/dialog/QLineEdit[0]"` (first QLineEdit in dialog)

**Examples:**
```
"root"                              # Root window
"root/text_input"                   # Element with objectName="text_input"
"root/QWidget[0]/QPushButton[1]"   # Second button in first widget
"root/main_panel/submit_btn"        # Nested by name
```

**Requirements:**
- Must be unique within the UI tree
- Must be deterministic (same element = same ref on repeated snapshots)
- Case-sensitive

### Widget Node

A **Widget Node** represents a UI element in the hierarchy.

**Schema:**
```typescript
interface WidgetNode {
  ref: string;                    // Unique reference path
  type: string;                   // Element type (QPushButton, button, etc.)
  objectName: string | null;      // Element ID/name (if any)
  visible: boolean;               // Is element visible?
  enabled: boolean;               // Is element enabled/interactive?
  geometry: {                     // Position and size
    x: number;
    y: number;
    width: number;
    height: number;
  };
  properties: Record<string, any>; // Framework-specific properties
  children: WidgetNode[];          // Child elements
}
```

**Common Properties** (in `properties` field):
- `text`: Button/label text
- `checked`: Checkbox/radio state
- `value`: Input value
- `placeholder`: Placeholder text
- `selected`: Selection state
- `focused`: Focus state

---

## Protocol Methods

### Method: connect

**Purpose:** Establish connection to instrumented application

**Direction:** Client → Server

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "connect",
  "params": {
    "target": "string"  // Connection target (server name, URL, etc.)
  },
  "id": 1
}
```

**Parameters:**
- `target` (string, required): Connection identifier
  - PyQt6: Server name (e.g., "qt_instrument")
  - Electron: WebSocket URL (e.g., "ws://localhost:9222")
  - Web: Browser CDP URL

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "app_info": {
      "framework": "string",      // Framework name
      "version": "string",        // Framework version
      "transport": "string",      // Transport type
      "pid": number,              // Process ID (optional)
      "title": "string"           // App title (optional)
    }
  },
  "id": 1
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Connection failed: target not found",
    "data": {
      "target": "qt_instrument"
    }
  },
  "id": 1
}
```

---

### Method: disconnect

**Purpose:** Close connection to application

**Direction:** Client → Server

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "disconnect",
  "params": {},
  "id": 2
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true
  },
  "id": 2
}
```

---

### Method: snapshot

**Purpose:** Get complete UI element tree

**Direction:** Client → Server

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "snapshot",
  "params": {},
  "id": 3
}
```

**Parameters:** None

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "ref": "root",
    "type": "MainWindow",
    "objectName": "main_window",
    "visible": true,
    "enabled": true,
    "geometry": {"x": 100, "y": 100, "width": 800, "height": 600},
    "properties": {
      "title": "My Application"
    },
    "children": [
      {
        "ref": "root/text_input",
        "type": "QLineEdit",
        "objectName": "text_input",
        "visible": true,
        "enabled": true,
        "geometry": {"x": 10, "y": 10, "width": 200, "height": 30},
        "properties": {
          "text": "Hello",
          "placeholder": "Enter text..."
        },
        "children": []
      }
    ]
  },
  "id": 3
}
```

**Notes:**
- Returns the entire UI tree from root
- May be large (thousands of elements for complex UIs)
- Future: Add filtering parameters (depth limit, type filter, etc.)

---

### Method: click

**Purpose:** Click a UI element

**Direction:** Client → Server

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "click",
  "params": {
    "ref": "root/submit_button",
    "button": "left",               // Optional, default "left"
    "modifiers": ["ctrl", "shift"]  // Optional, default []
  },
  "id": 4
}
```

**Parameters:**
- `ref` (string, required): Element reference
- `button` (string, optional): Mouse button
  - `"left"` (default)
  - `"right"`
  - `"middle"`
- `modifiers` (array, optional): Keyboard modifiers
  - `"ctrl"` / `"cmd"` / `"meta"`
  - `"shift"`
  - `"alt"`

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true
  },
  "id": 4
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": 1,
    "message": "Widget not found: root/submit_button",
    "data": {
      "ref": "root/submit_button",
      "similar": ["root/submit_btn", "root/cancel_button"]
    }
  },
  "id": 4
}
```

---

### Method: type

**Purpose:** Type text into a UI element

**Direction:** Client → Server

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "type",
  "params": {
    "ref": "root/text_input",
    "text": "Hello World",
    "submit": false,     // Optional, default false
    "clear": false       // Optional, default false
  },
  "id": 5
}
```

**Parameters:**
- `ref` (string, required): Element reference
- `text` (string, required): Text to type
- `submit` (boolean, optional): Press Enter after typing (default: false)
- `clear` (boolean, optional): Clear existing text first (default: false)

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true
  },
  "id": 5
}
```

**Error Codes:**
- `1`: Element not found
- `2`: Element not visible
- `3`: Element not enabled
- `4`: Element not focusable/editable

---

### Method: select

**Purpose:** Select an option from a dropdown/combobox

**Direction:** Client → Server

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "select",
  "params": {
    "ref": "root/country_selector",
    "value": "USA",              // Option 1: By value
    "index": 2,                  // Option 2: By index
    "text": "United States"      // Option 3: By display text
  },
  "id": 6
}
```

**Parameters:**
- `ref` (string, required): Element reference
- One of:
  - `value` (string): Option value
  - `index` (number): Option index (0-based)
  - `text` (string): Option display text

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "selected": {
      "value": "USA",
      "index": 2,
      "text": "United States"
    }
  },
  "id": 6
}
```

---

### Method: ping

**Purpose:** Check if connection is alive

**Direction:** Client → Server

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "ping",
  "params": {},
  "id": 7
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "ok",
    "timestamp": 1704234567,
    "uptime": 12345  // Seconds since connection (optional)
  },
  "id": 7
}
```

---

## Error Handling

### Standard Error Codes

Based on JSON-RPC 2.0 with extensions:

**JSON-RPC Standard Errors:**
- `-32700`: Parse error (invalid JSON)
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

**Protocol-Specific Errors:**
- `1`: Element/widget not found
- `2`: Element not visible
- `3`: Element not enabled
- `4`: Not connected to application
- `5`: Operation timeout
- `6`: Element not focusable
- `7`: Element not editable

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": number,
    "message": "string",
    "data": {
      // Context-specific error data
      "ref": "root/element",
      "reason": "Element is not visible",
      "suggestions": ["Check if element is hidden", "Try waiting for visibility"]
    }
  },
  "id": number | null
}
```

### Error Handling Best Practices

**For Implementers:**
1. Include actionable error messages
2. Provide `data` field with context
3. Suggest fixes when possible
4. Log errors on server side

**For Clients:**
1. Handle all error codes gracefully
2. Retry transient errors (timeout, connection)
3. Report permanent errors (element not found)
4. Use `data` field for debugging

---

## Implementation Guidelines

### For Adapter Developers

**Requirements:**
1. Implement all methods in this specification
2. Return responses in exact format specified
3. Use framework-native APIs for interactions
4. Choose optimal transport for framework
5. Handle errors according to error codes

**Recommendations:**
1. Log all requests/responses for debugging
2. Validate params before processing
3. Use async/await for non-blocking I/O
4. Implement connection pooling if needed
5. Add framework-specific extensions carefully

### Extending the Protocol

**Adding New Methods:**
1. Propose new method in GIP issues
2. Get community feedback
3. Update specification
4. Implement in reference adapter
5. Document in changelog

**Framework-Specific Extensions:**
- Prefix with framework name: `"qt_custom_method"`
- Document clearly as non-standard
- Don't break standard methods

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "qt_select_tab",  // Qt-specific extension
  "params": {"ref": "root/tabs", "index": 2},
  "id": 8
}
```

---

## Version History

### v1.0.0 (2026-02-02)
- Initial protocol specification
- Core methods: connect, disconnect, snapshot, click, type, select, ping
- Error handling specification
- Transport-neutral design

---

## References

- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [JSON Schema](https://json-schema.org/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [WebDriver W3C Standard](https://www.w3.org/TR/webdriver/)

---

## License

This specification is released under MIT License.

Implementations may use any license.
