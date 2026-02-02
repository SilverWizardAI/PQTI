# Quick Start - PyQt Instrument PoC

## What We Built

Standalone instrumentation library for PyQt6 apps that Claude Code can interact with through MCP.

**Architecture:**
```
Claude Code <--MCP--> PyQt Instrument MCP Server <--IPC--> Your PyQt6 App
```

## Components

1. **qt_instrument/** - Python library (IPC server, widget inspection, actions)
2. **mcp_server/** - MCP server for Claude Code integration
3. **examples/simple_app.py** - Test application
4. **venv/** - Python 3.12 virtual environment

## Test the PoC

### Step 1: Run the test app

```bash
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/PQTI
source venv/bin/activate
python examples/simple_app.py
```

You should see: `"Instrumentation enabled - MCP server can now connect"`

### Step 2: Configure Claude Code MCP

Add to `~/.claude/mcp_config.json`:

```json
{
  "mcpServers": {
    "pyqt-instrument": {
      "command": "/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/PQTI/venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/PQTI"
    }
  }
}
```

### Step 3: Restart Claude Code

The MCP server will now be available.

### Step 4: Test from Claude Code

With the simple app running:

```
Use the qt_connect tool to connect to the app
Use qt_snapshot to see the widget tree
Use qt_click with ref="root/copy_button" to click the button
Use qt_type with ref="root/text_input" and text="Hello" to type text
```

## Available MCP Tools

- `qt_connect` - Connect to running PyQt6 app (default: qt_instrument)
- `qt_snapshot` - Get complete widget tree as JSON
- `qt_click` - Click widget by reference (ref, button)
- `qt_type` - Type text into widget (ref, text, submit)
- `qt_ping` - Check connection status

## Widget References

From the snapshot, widgets can be referenced:
- By objectName: `root/text_input`, `root/copy_button`
- By type/index: `root/QLineEdit[0]`, `root/QPushButton[1]`

## Next Steps

1. **Test basic interaction**: Connect, snapshot, click, type
2. **Add to C3**: Use this library to test C3 itself
3. **Add recording**: Record actions → generate pytest files
4. **Windows support**: Adapt IPC for Windows named pipes
5. **Auto-launch**: MCP server launches app automatically

## Status

✅ Core library with IPC server
✅ Widget inspection and snapshot
✅ Basic actions (click, type)
✅ MCP server integration
✅ Example test app

⏳ Test recording
⏳ pytest generation
⏳ Windows support
⏳ Auto-launch capability
