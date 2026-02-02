# PQTI - AI-Powered GUI Testing for Any Framework

**Stop writing GUI tests. Let Claude Code write them for you.**

Version: 2.0
Status: Production Ready (PyQt6), Adapter Framework Available
License: MIT

---

## The Problem

Testing GUI applications is:
- **Time-consuming** - Hours of manual clicking and checking
- **Error-prone** - Easy to miss edge cases
- **Tedious** - Same workflows over and over
- **Framework-specific** - Different tools for PyQt6, Flet, Electron, etc.
- **Hard to maintain** - Tests break when UI changes

Most developers either skip GUI testing entirely or spend days writing brittle test code.

---

## The Solution

**PQTI (PyQt Instrument)** is a GUI test automation framework that lets Claude Code automatically test your applications.

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│  1. Add One Line to Your App                            │
│     enable_instrumentation(app)                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. Tell Claude Code to Test                            │
│     "Test my app: click login, enter credentials,       │
│      verify dashboard loads"                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. Get Automated Tests                                 │
│     - Claude explores your UI                           │
│     - Tests your workflows                              │
│     - Generates test suite                              │
│     - Reports issues                                    │
└─────────────────────────────────────────────────────────┘
```

**That's it.** No test code to write. No framework to learn. Just describe what to test.

---

## What Makes PQTI Different

### For End Users

❌ **Traditional GUI Testing:**
```python
# Write hundreds of lines of test code
class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.window = LoginWindow()

    def test_login_success(self):
        # Find username field
        username = self.window.findChild(QLineEdit, "username")
        # Type username
        QTest.keyClicks(username, "admin")
        # Find password field
        password = self.window.findChild(QLineEdit, "password")
        # Type password
        QTest.keyClicks(password, "secret")
        # Find login button
        login_btn = self.window.findChild(QPushButton, "login")
        # Click it
        QTest.mouseClick(login_btn, Qt.LeftButton)
        # Assert something...
        self.assertTrue(self.window.isLoggedIn())
```

✅ **With PQTI:**
```python
# Add to your app:
from qt_instrument import enable_instrumentation
app = QApplication(sys.argv)
enable_instrumentation(app)  # ONE LINE!
```

Then tell Claude Code:
> "Test the login workflow: enter 'admin'/'secret', click login, verify dashboard appears"

Claude writes and runs the tests automatically.

### For Framework Developers

PQTI uses a **framework-agnostic architecture**:

```
Your GUI App ←→ PQTI Adapter ←→ PQTI Core ←→ Claude Code
                    ↓                ↓
              (150 lines)    (Framework agnostic)
```

**Want to add PQTI to your framework?**
1. Implement the PQTI protocol (150-200 lines)
2. Ship it with your framework
3. Done - all Claude Code users can now test your framework

---

## Real-World Example

### Before PQTI

Developer has a PyQt6 app with a text editor. To test copy/paste:

```python
# test_editor.py (100+ lines)
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

class TestEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self):
        self.window = EditorWindow()
        self.window.show()
        QTest.qWaitForWindowExposed(self.window)

    def test_copy_paste(self):
        # Find text input
        text_input = self.window.findChild(QTextEdit, "text_input")
        self.assertIsNotNone(text_input, "Text input not found")

        # Type text
        QTest.keyClicks(text_input, "Hello World")

        # Select all
        QTest.keyClick(text_input, Qt.Key_A, Qt.ControlModifier)

        # Copy
        QTest.keyClick(text_input, Qt.Key_C, Qt.ControlModifier)

        # Find result label
        result = self.window.findChild(QLabel, "result")
        self.assertIsNotNone(result, "Result label not found")

        # Click copy button
        copy_btn = self.window.findChild(QPushButton, "copy_button")
        QTest.mouseClick(copy_btn, Qt.LeftButton)

        # Wait for update
        QTest.qWait(100)

        # Verify
        self.assertEqual(result.text(), "Copied: Hello World")

    def tearDown(self):
        self.window.close()

if __name__ == '__main__':
    unittest.main()
```

**Time to write:** 30-60 minutes
**Maintenance:** High (breaks when UI changes)
**Coverage:** Only what you explicitly test

### After PQTI

```python
# app.py (add ONE line)
from qt_instrument import enable_instrumentation

app = QApplication(sys.argv)
enable_instrumentation(app)  # <-- THIS IS ALL YOU ADD
window = EditorWindow()
window.show()
app.exec()
```

Then in Claude Code:
```
> Test the copy/paste workflow in my editor app.
  Run it with: python app.py
  Test: type text, click copy, verify label updates
```

Claude Code:
1. ✅ Starts your app
2. ✅ Explores the UI structure
3. ✅ Types "Hello World" into text field
4. ✅ Clicks copy button
5. ✅ Verifies label shows "Copied: Hello World"
6. ✅ Generates test file for regression testing
7. ✅ Reports any issues found

**Time to test:** 2 minutes (including Claude's exploration)
**Maintenance:** Zero (Claude adapts to UI changes)
**Coverage:** Claude tests edge cases you didn't think of

---

## Framework Support

| Framework | Status | Setup Time | Guide |
|-----------|--------|------------|-------|
| **PyQt6** | ✅ Production | 5 minutes | [Quick Start](PYQT6_QUICK_START.md) |
| **Flet** | 🔨 Build Adapter | 4 hours + 5 min | [Flet Guide](ADDING_PQTI_TO_FLET_APPS.md) |
| **Electron** | 🔮 Build Adapter | ~6 hours | [Adapter Guide](../docs/ADAPTER_GUIDE.md) |
| **Web (Playwright)** | 🔮 Build Adapter | ~4 hours | [Adapter Guide](../docs/ADAPTER_GUIDE.md) |
| **Your Framework** | 🔨 Build Adapter | ~4-8 hours | [Adapter Guide](../docs/ADAPTER_GUIDE.md) |

---

## How to Get Started

### If You Use PyQt6 (Ready Now!)

**Step 1:** Install PQTI
```bash
pip install -e /path/to/PQTI
```

**Step 2:** Add to your app
```python
from qt_instrument import enable_instrumentation
app = QApplication(sys.argv)
enable_instrumentation(app)  # Add this line
```

**Step 3:** Create `.mcp.json` in your app directory
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

**Step 4:** Tell Claude Code to test
```
Test my PyQt6 app.
Run with: python my_app.py
Test these workflows:
- Login flow
- Data entry
- Export functionality
```

**Time to first test:** 5 minutes
**Full guide:** [PYQT6_QUICK_START.md](PYQT6_QUICK_START.md)

### If You Use Flet

Give the [Flet Guide](ADDING_PQTI_TO_FLET_APPS.md) to Claude Code. It will:
1. Build the Flet adapter (~4 hours)
2. Add instrumentation to your app
3. Start testing

**Time to first test:** ~4 hours (one-time adapter build) + 5 minutes

### If You Use Another Framework

Give the [Adapter Guide](../docs/ADAPTER_GUIDE.md) to Claude Code to build an adapter for your framework (~4-8 hours one-time effort).

Or build it yourself - it's just 150-200 lines implementing the PQTI protocol.

---

## Technical Overview

### Architecture

```
┌────────────────────────────────────────┐
│         Claude Code (AI Tester)        │
└───────────────┬────────────────────────┘
                │ MCP Protocol
┌───────────────▼────────────────────────┐
│        PQTI Core (App Controller)      │
│         Framework-Agnostic             │
│  - Routes commands                     │
│  - Manages connections                 │
│  - Standard protocol                   │
└───────────────┬────────────────────────┘
                │ Adapter Interface
┌───────────────▼────────────────────────┐
│         Framework Adapters             │
│  ┌─────────┬─────────┬─────────────┐   │
│  │ PyQt6   │  Flet   │  Electron   │   │
│  │ Adapter │ Adapter │  Adapter    │   │
│  └────┬────┴────┬────┴──────┬──────┘   │
└───────┼─────────┼───────────┼──────────┘
        │         │           │
    ┌───▼───┐ ┌───▼───┐ ┌────▼────┐
    │PyQt6  │ │ Flet  │ │Electron │
    │ App   │ │ App   │ │  App    │
    └───────┘ └───────┘ └─────────┘
```

### Protocol (Language-Independent)

PQTI uses a simple JSON-RPC 2.0 protocol:

**Connect to app:**
```json
{"method": "connect", "params": {"target": "qt_instrument"}}
```

**Get UI snapshot:**
```json
{"method": "snapshot", "params": {}}
```

**Click widget:**
```json
{"method": "click", "params": {"ref": "root/window/button"}}
```

**Type text:**
```json
{"method": "type", "params": {"ref": "root/input", "text": "Hello"}}
```

**Check connection:**
```json
{"method": "ping", "params": {}}
```

That's it. Five methods. Works across all frameworks.

---

## Use Cases

### 1. **Automated Testing**
Stop clicking manually. Let Claude test automatically and generate test suites.

### 2. **Regression Testing**
Claude runs your tests after every change, catching regressions instantly.

### 3. **Cross-Application Workflows**
Test workflows that span multiple apps (desktop + web + mobile).

### 4. **Documentation Generation**
Claude generates user guides by testing your UI and documenting workflows.

### 5. **Accessibility Testing**
Claude verifies keyboard navigation, screen reader support, etc.

### 6. **Performance Testing**
Claude measures UI responsiveness, finds slow interactions.

### 7. **Exploratory Testing**
Claude explores your UI, finding edge cases you didn't think of.

---

## Benefits

### For Developers
- ✅ **Save Time** - No test code to write
- ✅ **Better Coverage** - Claude finds edge cases
- ✅ **Faster Iteration** - Test in minutes, not hours
- ✅ **Easy Maintenance** - Claude adapts to UI changes

### For Teams
- ✅ **Consistent Testing** - Same approach across all frameworks
- ✅ **Knowledge Sharing** - Tests are natural language descriptions
- ✅ **Onboarding** - New developers use Claude to learn the app
- ✅ **Quality Assurance** - Automated regression testing

### For Framework Authors
- ✅ **Better DX** - Give users automatic testing
- ✅ **Competitive Edge** - "Works with Claude Code"
- ✅ **Easy Integration** - Just 150-200 lines of adapter code
- ✅ **Community** - Join the PQTI ecosystem

---

## FAQ

**Q: Do I need to change my app's code?**
A: Just add one line: `enable_instrumentation(app)`

**Q: Does it work with my framework?**
A: PyQt6 works now. For other frameworks, build an adapter (~4-8 hours) or request one.

**Q: Is it secure?**
A: PQTI only works locally on your machine. No data leaves your system.

**Q: Can I use it in CI/CD?**
A: Yes! Claude can generate test files that run in your CI pipeline.

**Q: What if my UI changes?**
A: Claude adapts automatically. No brittle XPath selectors or hard-coded IDs.

**Q: Do I need Claude Code?**
A: PQTI is designed for Claude Code, but the protocol is open - other tools could use it.

**Q: Is it free?**
A: Yes, PQTI is MIT licensed and free to use.

---

## Documentation

**Quick Starts:**
- [PyQt6 Quick Start](PYQT6_QUICK_START.md) - 5 minutes to first test
- [Flet Integration Guide](ADDING_PQTI_TO_FLET_APPS.md) - Complete Flet support

**Reference:**
- [INDEX](INDEX.md) - Complete documentation map
- [Architecture Overview](ARCHITECTURE.md) - How PQTI works
- [Technical Specification](../TECH_SPEC.md) - Deep technical details
- [Protocol Specification](../protocol/specification.md) - Language-independent protocol
- [Adapter Guide](../docs/ADAPTER_GUIDE.md) - Build adapters for new frameworks

---

## Getting Help

- **Documentation:** Start with [INDEX.md](INDEX.md)
- **Issues:** GitHub Issues
- **Questions:** See [FAQ.md](FAQ.md)

---

## Contributing

PQTI is open source (MIT License) and welcomes contributions:

1. **Build adapters** for new frameworks
2. **Improve documentation**
3. **Report issues** and bugs
4. **Share use cases** and success stories

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Vision

**Today:** PQTI enables AI-powered testing for PyQt6 apps.

**Tomorrow:** PQTI is the universal standard for GUI test automation across all frameworks and languages.

**Goal:** Make GUI testing so easy that every developer does it automatically.

---

## Status

- **Version:** 2.0
- **Released:** 2026-02-02
- **Status:** Production (PyQt6), Active Development (Flet)
- **License:** MIT
- **Repository:** `/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/PQTI`

---

## Get Started Now

### PyQt6 Users
Read: [PYQT6_QUICK_START.md](PYQT6_QUICK_START.md)
Time: 5 minutes to first test

### Flet Users
Read: [ADDING_PQTI_TO_FLET_APPS.md](ADDING_PQTI_TO_FLET_APPS.md)
Give to Claude Code - it will build the adapter and integrate it

### Other Frameworks
Read: [Adapter Guide](../docs/ADAPTER_GUIDE.md)
Build an adapter (~4-8 hours) or request one

---

**Stop writing GUI tests. Let AI write them for you.**

**Get started:** [INDEX.md](INDEX.md)
