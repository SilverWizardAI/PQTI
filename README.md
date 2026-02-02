# PyQt Instrument

Runtime instrumentation and testing library for PyQt6 applications.

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

## Status

PoC - macOS/Linux only, manual app launch
