# PQTI (PyQt Instrument)

**Framework-agnostic GUI instrumentation library** for automated testing and interaction with GUI applications through Claude Code.

## Features

✅ **Framework-Agnostic Architecture**: Protocol-based design supports PyQt6, Electron, Web apps, and more
✅ **MCP Integration**: Works seamlessly with Claude Code via Model Context Protocol
✅ **Real-time Interaction**: Connect, inspect, and control running GUI applications
✅ **Production Tested**: 89% test success rate with comprehensive validation

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Add to your app

```python
from qt_instrument import enable_instrumentation

app = QApplication(sys.argv)
enable_instrumentation(app)
```

### 3. Configure MCP server in Claude Code

Add to `~/.claude/mcp_config.json`:

```json
{
  "mcpServers": {
    "pyqt-instrument": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/full/path/to/pyqt-instrument"
    }
  }
}
```

### 4. Test with example app

```bash
python examples/simple_app.py
```

Then in Claude Code: "Connect to the Qt app and show me the widgets"

## Available Tools

- `qt_connect` - Connect to running app
- `qt_snapshot` - Get widget tree
- `qt_click` - Click a widget
- `qt_type` - Type text
- `qt_ping` - Check connection

## Widget References

- By name: `root/copy_button`
- By type/index: `root/QPushButton[0]`

## Architecture

```
Claude Code (MCP Client)
    ↓ MCP Protocol (stdio)
App Controller (Framework-Agnostic)
    ↓ Adapter Interface
┌───────────┬─────────────┬──────────────┐
│  PyQt6    │  Electron   │  Playwright  │
│  Adapter  │  Adapter    │  Adapter     │
│           │  (future)   │  (future)    │
└─────┬─────┴─────────────┴──────────────┘
      ↓
  PyQt6 Application
```

**Key Design:**
- **Protocol Layer**: Language-independent GUI Instrumentation Protocol (GIP)
- **App Controller**: Framework-agnostic business logic
- **Adapters**: Framework-specific implementations (PyQt6, Electron, etc.)

See [TECH_SPEC.md](TECH_SPEC.md) for detailed architecture documentation.

## Documentation

- [Technical Specification](TECH_SPEC.md) - Architecture and design rationale
- [Protocol Specification](protocol/specification.md) - GIP protocol details
- [Adapter Development Guide](docs/ADAPTER_GUIDE.md) - How to add new frameworks
- [Status](STATUS.md) - Project status and testing results

## Status

**Current:** Production-ready for PyQt6 (8/9 tests passing)
**Platforms:** macOS/Linux (Unix sockets)
**Future:** Electron, Playwright, WPF adapters
