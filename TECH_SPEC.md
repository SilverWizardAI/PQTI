# PQTI Technical Specification
## Framework-Agnostic GUI Instrumentation Architecture

**Version:** 2.0
**Date:** 2026-02-02
**Status:** Design Approved - Ready for Implementation
**Author:** PQTI Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Problem Statement](#problem-statement)
4. [Proposed Architecture](#proposed-architecture)
5. [Design Rationale](#design-rationale)
6. [Protocol Specification](#protocol-specification)
7. [Implementation Plan](#implementation-plan)
8. [Migration Strategy](#migration-strategy)
9. [Testing Strategy](#testing-strategy)
10. [Future Extensions](#future-extensions)

---

## Executive Summary

### What We're Building

A **framework-agnostic GUI instrumentation system** that allows Claude Code to interact with GUI applications built in any framework (PyQt6, Electron, Web, WPF, etc.) through a unified protocol.

### Why This Matters

**Current limitation:** The system is tightly coupled to PyQt6, making it difficult to:
- Add support for other frameworks (Electron, web apps, WPF)
- Port components to other languages (C++, JavaScript, Rust)
- Reuse the protocol for different use cases

**Solution:** Separate the protocol (WHAT to do) from implementation (HOW to do it) through a clean adapter architecture.

### Key Outcomes

1. **Language Independence**: Protocol specification can be implemented in any language
2. **Framework Portability**: Add new frameworks without modifying core logic
3. **Transport Flexibility**: Each framework can use optimal IPC mechanism
4. **Future-Proof**: Enables web automation, mobile apps, and more

---

## Current State Analysis

### What We Have (Validated via Testing)

✅ **Fully Tested MCP Stack** (8/9 tests passed):
- `qt_connect`: Connects to PyQt6 app via Unix socket
- `qt_snapshot`: Returns widget tree with properties (tested 5x)
- `qt_type`: Types text into widgets
- `qt_click`: Clicks buttons, triggers event handlers
- `qt_ping`: Connection health check
- Error handling for invalid widget references

**Test Results:** 89% success rate, production-ready for PyQt6

### Current Architecture

```
┌─────────────┐
│ Claude Code │
└──────┬──────┘
       │ MCP (stdio)
       ↓
┌─────────────────────┐
│  MCP Server         │ ← Python-specific
│  (server.py)        │ ← Qt-aware (imports QtInstrumentClient)
│  Line 116:          │
│  qt_client =        │
│    QtInstrumentClient()
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│  QtInstrumentClient │ ← Python-specific
│  (qt_client.py)     │ ← Qt-specific (Unix sockets hardcoded)
│                     │ ← Transport + Protocol mixed
└──────┬──────────────┘
       │ Unix Socket IPC
       ↓
┌─────────────────────┐
│  Qt Instrumentation │ ← Python + PyQt6 specific
│  (qt_instrument)    │ ← QTest, QWidget APIs
└─────────────────────┘
```

### Current File Structure

```
PQTI/
├── mcp_server/
│   ├── server.py         # MCP server (Qt-aware)
│   └── qt_client.py      # Qt IPC client (Unix sockets)
├── qt_instrument/
│   └── core.py           # PyQt6 instrumentation
└── examples/
    └── simple_app.py     # Test application
```

### Problems with Current Architecture

1. **Tight Coupling**: MCP server directly instantiates `QtInstrumentClient`
2. **No Abstraction**: Protocol logic mixed with PyQt6-specific implementation
3. **Transport Hardcoded**: Unix sockets are PyQt6-specific (won't work for web/Electron)
4. **Single Framework**: Can't add Electron without major refactoring
5. **Language Lock-in**: Can't port to C++ or JavaScript without rewriting everything

---

## Problem Statement

### Strategic Question

**"How do we support Electron apps, web apps, and other frameworks without duplicating the entire stack?"**

### Technical Challenge

The current architecture conflates three concerns:

1. **Protocol** (WHAT): "Get widget tree", "Click element"
2. **Transport** (HOW): Unix sockets, WebSockets, named pipes
3. **Implementation** (DETAILS): QTest, Playwright, Electron IPC

**Example Problem:**
- To add Electron support, we'd need to:
  - Duplicate MCP server logic
  - Reimplement connection handling
  - Copy protocol definitions
  - Maintain two separate codebases

### Desired End State

**"Write the protocol once, implement adapters for each framework, reuse everything else."**

Similar to how Selenium WebDriver works across browsers.

---

## Proposed Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                      Claude Code                         │
└───────────────────────┬─────────────────────────────────┘
                        │ MCP Protocol (stdio)
                        ↓
┌─────────────────────────────────────────────────────────┐
│              MCP Server (server.py)                      │
│              - Handles MCP protocol only                 │
│              - Framework-agnostic                        │
│              - Translates MCP → Protocol commands        │
└───────────────────────┬─────────────────────────────────┘
                        │ Uses
                        ↓
┌─────────────────────────────────────────────────────────┐
│         App Controller (app_controller.py)               │
│         ┌──────────────────────────────────────┐        │
│         │ • Protocol definition (JSON-RPC)     │        │
│         │ • Adapter registry                   │        │
│         │ • Command routing                    │        │
│         │ • Framework-agnostic business logic  │        │
│         └──────────────────────────────────────┘        │
└───────────────────────┬─────────────────────────────────┘
                        │ Dispatches to
                        ↓
┌─────────────────────────────────────────────────────────┐
│              Adapter Interface (ABC)                     │
│                                                          │
│  ┌──────────────┬─────────────────┬─────────────────┐  │
│  │ PyQt6        │ Electron        │ Playwright      │  │
│  │ Adapter      │ Adapter         │ Adapter         │  │
│  │              │                 │                 │  │
│  │ Unix Socket  │ WebSocket/IPC   │ CDP WebSocket   │  │
│  │ + QTest      │ + Electron APIs │ + Browser APIs  │  │
│  └──────┬───────┴────────┬────────┴────────┬────────┘  │
└─────────┼────────────────┼─────────────────┼───────────┘
          │                │                 │
          ↓                ↓                 ↓
     ┌─────────┐      ┌──────────┐     ┌──────────┐
     │ PyQt6   │      │ Electron │     │  Web     │
     │ App     │      │ App      │     │  App     │
     └─────────┘      └──────────┘     └──────────┘
```

### Proposed File Structure

```
PQTI/
├── protocol/
│   ├── __init__.py
│   ├── schema.json              # JSON Schema protocol definition
│   └── specification.md         # Human-readable protocol docs
│
├── mcp_server/
│   ├── __init__.py
│   ├── server.py                # MCP server (framework-agnostic!)
│   ├── app_controller.py        # NEW: Core controller logic
│   │
│   └── adapters/
│       ├── __init__.py
│       ├── base.py              # NEW: FrameworkAdapter ABC
│       │
│       ├── pyqt6/
│       │   ├── __init__.py
│       │   ├── adapter.py       # NEW: PyQt6Adapter
│       │   └── transport.py     # MOVED: qt_client.py
│       │
│       ├── electron/            # FUTURE
│       │   ├── adapter.py
│       │   └── transport.py
│       │
│       └── playwright/          # FUTURE
│           ├── adapter.py
│           └── transport.py
│
├── qt_instrument/               # UNCHANGED
│   ├── __init__.py
│   └── core.py                  # PyQt6-specific (stays as-is)
│
├── examples/
│   └── simple_app.py
│
└── docs/
    ├── TECH_SPEC.md             # This document
    ├── PROTOCOL.md              # Protocol specification
    └── ADAPTER_GUIDE.md         # How to write adapters
```

### Component Responsibilities

#### 1. Protocol Layer (`protocol/`)

**Responsibility:** Define the contract (language-independent)

**Contents:**
- `schema.json`: JSON Schema defining request/response formats
- `specification.md`: Human-readable protocol documentation

**Key Point:** This is pure specification, no code. Can be implemented in any language.

#### 2. App Controller (`app_controller.py`)

**Responsibility:** Framework-agnostic business logic

**Functions:**
- Register framework adapters
- Route commands to appropriate adapter
- Handle connection lifecycle
- Validate protocol compliance

**Key Point:** Knows WHAT to do, not HOW to do it.

#### 3. Adapter Interface (`adapters/base.py`)

**Responsibility:** Define the contract that all adapters must implement

**Interface:**
```python
class FrameworkAdapter(ABC):
    @property
    @abstractmethod
    def framework_name(self) -> str: ...

    @abstractmethod
    async def connect(self, target: str) -> Dict: ...

    @abstractmethod
    async def snapshot(self) -> Dict: ...

    @abstractmethod
    async def click(self, ref: str, button: str) -> Dict: ...

    @abstractmethod
    async def type_text(self, ref: str, text: str, submit: bool) -> Dict: ...

    @abstractmethod
    async def ping(self) -> Dict: ...
```

**Key Point:** Each method returns standardized dict format.

#### 4. PyQt6 Adapter (`adapters/pyqt6/`)

**Responsibility:** Implement the interface for PyQt6 apps

**Components:**
- `adapter.py`: Implements `FrameworkAdapter` for PyQt6
- `transport.py`: Unix socket IPC (moved from `qt_client.py`)

**Key Point:** All PyQt6-specific code lives here.

#### 5. MCP Server (`server.py`)

**Responsibility:** Handle MCP protocol only

**Changes:**
- Remove direct `QtInstrumentClient` import
- Use `AppController` instead
- Framework-agnostic tool handlers

**Key Point:** Doesn't know about Qt, Electron, or any specific framework.

---

## Design Rationale

### Why Separate Protocol from Implementation?

**Analogy:** HTTP vs Web Servers

- **HTTP**: Protocol specification (language-independent)
- **nginx, Apache, IIS**: Implementations in different languages
- **Result**: Interoperability, multiple implementations, language choice

Similarly:
- **GUI Instrumentation Protocol**: Our specification
- **PyQt6 Adapter, Electron Adapter**: Implementations
- **Result**: Framework choice, language portability, reusability

### Why Use the Adapter Pattern?

**Problem:** Different frameworks have different APIs:
- PyQt6: `QTest.mouseClick(widget, Qt.LeftButton)`
- Playwright: `await page.click(selector)`
- Electron: `webContents.sendInputEvent({type: 'mouseDown'})`

**Solution:** Each adapter translates the standard protocol to framework-specific calls.

**Benefit:** Add new frameworks without changing core logic.

### Why Abstract Transport Layer?

**Problem:** Different frameworks use different IPC:
- PyQt6: Unix domain sockets (QLocalServer)
- Electron: WebSocket or Node.js IPC
- Web: Chrome DevTools Protocol (WebSocket)
- Windows apps: Named pipes

**Solution:** Each adapter chooses optimal transport for its framework.

**Benefit:** No forced compromises (e.g., don't force WebSockets on Qt apps).

### Why Use JSON-RPC 2.0?

**Benefits:**
1. **Standard**: Well-defined, widely implemented
2. **Language-agnostic**: JSON works everywhere
3. **Simple**: Request/response with ID matching
4. **Extensible**: Easy to add new methods

**Format:**
```json
{
  "jsonrpc": "2.0",
  "method": "snapshot",
  "params": {},
  "id": 1
}
```

### Why Keep `qt_instrument/` Unchanged?

**Reason:** It's already framework-specific and working well.

The instrumentation library (`qt_instrument/core.py`) is meant to be PyQt6-specific. It uses:
- `QLocalServer` for IPC
- `QTest` for interactions
- `QWidget` APIs for inspection

**This is correct!** It implements the protocol for PyQt6 apps.

---

## Protocol Specification

### Overview

**Name:** GUI Instrumentation Protocol (GIP) v1.0
**Transport:** Any (WebSocket, Unix socket, named pipes, etc.)
**Format:** JSON-RPC 2.0
**Encoding:** UTF-8

### Core Concepts

#### Widget Reference (Ref)

A **ref** is a string that uniquely identifies a UI element:
- Format: `"root/container/widget_name"` or `"root/WidgetType[index]"`
- Examples:
  - `"root/text_input"` (by object name)
  - `"root/QWidget[0]/QPushButton[1]"` (by type and index)

#### Standard Response Format

All methods return:
```json
{
  "success": true | false,
  "error": "error message" | null,
  "data": { ... }  // Method-specific data
}
```

### Methods

#### 1. connect

**Purpose:** Establish connection to instrumented application

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "connect",
  "params": {
    "target": "qt_instrument"  // Connection target (server name, URL, etc.)
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "app_info": {
      "framework": "pyqt6",
      "version": "6.10.2",
      "transport": "unix_socket",
      "pid": 12345
    }
  },
  "id": 1
}
```

#### 2. snapshot

**Purpose:** Get complete UI element tree

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "snapshot",
  "params": {},
  "id": 2
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "root": {
      "ref": "root",
      "type": "MainWindow",
      "objectName": "main_window",
      "visible": true,
      "enabled": true,
      "geometry": {"x": 100, "y": 100, "width": 800, "height": 600},
      "properties": {},
      "children": [...]
    }
  },
  "id": 2
}
```

**WidgetNode Schema:**
```typescript
interface WidgetNode {
  ref: string;              // Unique reference
  type: string;             // Widget/element type
  objectName: string | null;
  visible: boolean;
  enabled: boolean;
  geometry: {x, y, width, height};
  properties: Record<string, any>;  // text, checked, value, etc.
  children: WidgetNode[];
}
```

#### 3. click

**Purpose:** Click a UI element

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "click",
  "params": {
    "ref": "root/submit_button",
    "button": "left"  // "left" | "right" | "middle"
  },
  "id": 3
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "error": null
  },
  "id": 3
}
```

#### 4. type

**Purpose:** Type text into an element

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "type",
  "params": {
    "ref": "root/text_input",
    "text": "Hello World",
    "submit": false  // Press Enter after typing
  },
  "id": 4
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "error": null
  },
  "id": 4
}
```

#### 5. ping

**Purpose:** Check if connection is alive

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "ping",
  "params": {},
  "id": 5
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "ok",
    "timestamp": 1704234567
  },
  "id": 5
}
```

### Error Handling

**Error Response Format:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Widget not found: root/invalid_widget",
    "data": {
      "ref": "root/invalid_widget",
      "available_refs": ["root/text_input", "root/button"]
    }
  },
  "id": 3
}
```

**Error Codes:**
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `1`: Widget/element not found
- `2`: Widget not visible
- `3`: Widget not enabled
- `4`: Not connected

---

## Implementation Plan

### Phase 1: Create Protocol Specification (1 hour)

**Goal:** Document the protocol formally

**Tasks:**
1. ✅ Create `TECH_SPEC.md` (this document)
2. Create `protocol/specification.md` (detailed protocol docs)
3. Create `protocol/schema.json` (JSON Schema definitions)
4. Document all methods, params, responses

**Validation:** Review protocol spec, ensure it's framework-agnostic

**Artifacts:**
- `TECH_SPEC.md`
- `protocol/specification.md`
- `protocol/schema.json`

### Phase 2: Create Adapter Interface (30 minutes)

**Goal:** Define the contract all adapters must implement

**Tasks:**
1. Create `mcp_server/adapters/base.py`
2. Define `FrameworkAdapter` abstract base class
3. Document each method with type hints and docstrings
4. Add `framework_name` property

**Validation:** Run `python -m py_compile` on base.py

**Artifacts:**
- `mcp_server/adapters/base.py`

### Phase 3: Create PyQt6 Adapter (1 hour)

**Goal:** Refactor existing PyQt6 code into adapter pattern

**Tasks:**
1. Create `mcp_server/adapters/pyqt6/` directory
2. Move `qt_client.py` → `adapters/pyqt6/transport.py`
3. Rename `QtInstrumentClient` → `QtTransport`
4. Create `adapters/pyqt6/adapter.py`
5. Implement `PyQt6Adapter(FrameworkAdapter)`
6. Wire `PyQt6Adapter` to use `QtTransport`

**Validation:**
- Import `PyQt6Adapter` successfully
- All abstract methods implemented
- No circular imports

**Artifacts:**
- `mcp_server/adapters/pyqt6/adapter.py`
- `mcp_server/adapters/pyqt6/transport.py`
- `mcp_server/adapters/pyqt6/__init__.py`

### Phase 4: Create App Controller (1 hour)

**Goal:** Build framework-agnostic controller

**Tasks:**
1. Create `mcp_server/app_controller.py`
2. Implement `AppController` class:
   - Adapter registry
   - `register_adapter(adapter)`
   - `connect(framework, target)`
   - `execute(method, params)`
3. Add logging for all operations
4. Handle errors gracefully

**Validation:**
- Instantiate `AppController`
- Register `PyQt6Adapter`
- Call methods (will fail without app, but code should work)

**Artifacts:**
- `mcp_server/app_controller.py`

### Phase 5: Refactor MCP Server (1 hour)

**Goal:** Make MCP server framework-agnostic

**Tasks:**
1. Update `mcp_server/server.py`:
   - Remove `from .qt_client import QtInstrumentClient`
   - Add `from .app_controller import AppController`
   - Add `from .adapters.pyqt6.adapter import PyQt6Adapter`
   - Replace `qt_client` with `controller`
2. Update tool handlers to use controller
3. Simplify logic (no framework-specific code)

**Validation:**
- MCP server starts without errors
- No direct Qt imports in server.py

**Artifacts:**
- Updated `mcp_server/server.py`

### Phase 6: Integration Testing (1 hour)

**Goal:** Verify refactored code works exactly like before

**Tasks:**
1. Start test app: `.venv/bin/python examples/simple_app.py`
2. Test all MCP tools:
   - `qt_connect`
   - `qt_snapshot`
   - `qt_type`
   - `qt_click`
   - `qt_ping`
3. Verify all 8/9 tests still pass
4. Compare results with previous test run

**Validation:**
- All previous tests still pass
- No regressions
- Same success rate (8/9)

**Artifacts:**
- Test results log
- Comparison with previous results

### Phase 7: Documentation (30 minutes)

**Goal:** Document the new architecture

**Tasks:**
1. Update `README.md` with new architecture diagram
2. Create `docs/ADAPTER_GUIDE.md` (how to write adapters)
3. Update `STATUS.md` with refactoring completion
4. Add inline code documentation

**Validation:**
- Documentation is clear
- Examples are accurate
- Architecture diagrams match code

**Artifacts:**
- Updated `README.md`
- `docs/ADAPTER_GUIDE.md`
- Updated `STATUS.md`

### Phase 8: Commit and Push (15 minutes)

**Goal:** Preserve the refactoring in git history

**Tasks:**
1. Create detailed commit message explaining refactoring
2. List all files changed
3. Explain what changed and why
4. Push to remote

**Validation:**
- Commit message is comprehensive
- All files tracked
- Push successful

**Artifacts:**
- Git commit
- Pushed to remote

---

## Migration Strategy

### Backward Compatibility

**Goal:** No breaking changes to external API

**Strategy:**
- MCP tool names stay the same (`qt_connect`, `qt_snapshot`, etc.)
- Tool parameters unchanged
- Tool responses unchanged
- `qt_instrument/core.py` unchanged

**Result:** Users don't notice the refactoring

### Incremental Validation

**After Each Phase:**
1. Run basic import tests
2. Check for syntax errors
3. Verify no circular imports
4. Run unit tests (if any)

**After Complete Refactoring:**
1. Full integration test suite
2. Compare with previous test results
3. Verify 8/9 tests still pass
4. No performance degradation

### Rollback Plan

**If Issues Found:**
1. Git revert to previous commit
2. Analyze failure
3. Fix issue
4. Re-attempt refactoring

**Safety Net:**
- Git history preserves working version
- Can always revert
- Incremental commits allow partial rollback

---

## Testing Strategy

### Unit Tests (Future)

**Per Component:**
- `AppController`: Test adapter registration, command routing
- `PyQt6Adapter`: Test method implementations (mocked transport)
- Protocol validation: Test JSON Schema compliance

### Integration Tests (Existing)

**Reuse Existing Tests:**
- Run all 8/9 MCP tests that currently pass
- Verify identical behavior
- No regressions

**Test Scenarios:**
1. Connect to PyQt6 app
2. Get widget snapshot
3. Type text into widget
4. Click button
5. Multiple sequential operations
6. Error handling (invalid refs)

### Regression Testing

**Comparison:**
- Before refactoring: 8/9 tests pass
- After refactoring: 8/9 tests pass
- Same known issue: QCheckBox click

**Metrics:**
- Response times (should be similar)
- Error messages (should be same or better)
- Widget tree structure (identical)

---

## Future Extensions

### Phase 9: Electron Adapter (Future)

**Implementation:**
```
adapters/electron/
├── adapter.py           # ElectronAdapter
└── transport.py         # WebSocket/IPC transport
```

**Transport Options:**
- WebSocket (Electron's remote module)
- Node.js IPC (process.send/receive)
- HTTP REST API

**Key Differences from PyQt6:**
- Web-based UI (HTML/CSS/JS)
- Different widget model (DOM elements)
- Different event system

**But same protocol!** Just different adapter implementation.

### Phase 10: Playwright/Web Adapter (Future)

**Implementation:**
```
adapters/playwright/
├── adapter.py           # PlaywrightAdapter
└── transport.py         # Chrome DevTools Protocol
```

**Uses:**
- Playwright's existing browser automation
- Chrome DevTools Protocol (WebSocket)
- DOM element references

**Benefits:**
- Reuse MCP server
- Same tool names
- Web automation capability

### Phase 11: Cross-Language Implementation (Future)

**C++ Qt Adapter:**
```cpp
// adapters/qt_cpp/adapter.cpp
class QtCppAdapter : public FrameworkAdapter {
  QString frameworkName() override { return "qt_cpp"; }
  QVariantMap connect(QString target) override { ... }
  QVariantMap snapshot() override { ... }
  // ...
};
```

**JavaScript Electron Adapter:**
```javascript
// adapters/electron_js/adapter.js
class ElectronAdapter extends FrameworkAdapter {
  get frameworkName() { return 'electron'; }
  async connect(target) { ... }
  async snapshot() { ... }
  // ...
}
```

**Key Point:** Protocol is language-independent, implementations aren't.

---

## Conclusion

### Summary

This refactoring separates concerns into three layers:

1. **Protocol Layer**: Language-independent specification
2. **Controller Layer**: Framework-agnostic business logic
3. **Adapter Layer**: Framework-specific implementations

### Benefits

✅ **Extensibility**: Add frameworks without modifying core
✅ **Portability**: Protocol can be implemented in any language
✅ **Maintainability**: Clear separation of concerns
✅ **Testability**: Each layer can be tested independently
✅ **Future-Proof**: Supports web, mobile, desktop automation

### Risk Mitigation

✅ **No Breaking Changes**: External API stays the same
✅ **Incremental Implementation**: Validate at each step
✅ **Backward Compatibility**: Existing tests verify behavior
✅ **Git History**: Can rollback if needed

### Next Steps

1. Review and approve this tech spec
2. Begin Phase 1: Protocol specification
3. Proceed through phases 2-8
4. Validate with full integration tests
5. Commit and push refactored code

### Estimated Timeline

- **Total Time**: ~6 hours
- **Phases 1-4**: 3.5 hours (protocol + adapters + controller)
- **Phase 5**: 1 hour (MCP server refactoring)
- **Phase 6**: 1 hour (integration testing)
- **Phases 7-8**: 0.5 hours (documentation + commit)

**Ready to proceed with implementation!** 🚀

---

**Document Version History:**
- v2.0 (2026-02-02): Initial comprehensive tech spec
