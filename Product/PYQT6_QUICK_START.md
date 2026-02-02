# PyQt6 Quick Start with PQTI

**5-Minute Setup Guide**

## What You Need

PQTI has FULL PyQt6 support - everything is ready!

## Step 1: Add One Line to Your App

Find where you create QApplication and add:

```python
from qt_instrument import enable_instrumentation

app = QApplication(sys.argv)
enable_instrumentation(app)  # ADD THIS LINE
window = MainWindow()
window.show()
app.exec()
```

## Step 2: Install PQTI

Navigate to your app folder and run:
- With pip: `pip install -e /path/to/PQTI`
- With UV: `uv pip install -e /path/to/PQTI`

## Step 3: Create .mcp.json

Create this file in your app's root directory:

```json
{
  "mcpServers": {
    "pyqt-instrument": {
      "command": "/path/to/PQTI/.venv/bin/python",
      "args": ["-m", "mcp_server.server"]
    }
  }
}
```

## Step 4: Test It

Start your app - you should see:
"Instrumentation enabled - MCP server can now connect"

## Step 5: Tell Claude Code

Open Claude Code in your app directory and say:

```
Test my PyQt6 app with PQTI.

Run with: [your command]

Test these workflows:
- [Workflow 1]
- [Workflow 2]
```

Claude will:
1. Start your app
2. Connect via PQTI
3. Explore the UI
4. Test your workflows
5. Create test files

## MCP Tools Available

- `qt_connect` - Connect to app
- `qt_snapshot` - See all widgets
- `qt_click(ref)` - Click widgets
- `qt_type(ref, text)` - Type text
- `qt_ping` - Check connection

## Best Practice: Set Object Names

```python
button = QPushButton("Submit")
button.setObjectName("submit_button")  # DO THIS!
```

Makes testing easier with stable references.

## That's It!

PyQt6 support is complete and working. Just add the line and start testing.

Full Path: /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/PQTI/Product/PYQT6_QUICK_START.md
