# PQTI Product Documentation Index

**PQTI (PyQt Instrument)** - Framework-agnostic GUI test automation library for Claude Code

Version: 2.0
Date: 2026-02-02
Status: Production (PyQt6), Development (Flet)

---

## 📚 Documentation Map

### Quick Start

**For Users:**
- **[Quick Start Guide](QUICK_START.md)** - 5-minute setup for PyQt6 apps ⭐ START HERE
- **[Adding PQTI to Flet Apps](ADDING_PQTI_TO_FLET_APPS.md)** - Complete guide for Flet apps ⭐ FLET USERS
- **[FAQ](FAQ.md)** - Common questions and answers

**For Developers:**
- **[Architecture Overview](ARCHITECTURE.md)** - How PQTI works
- **[Technical Specification](../TECH_SPEC.md)** - Deep dive into design
- **[Protocol Specification](../protocol/specification.md)** - Language-independent protocol

### Framework-Specific Guides

- **[PyQt6 Apps](PYQT6_GUIDE.md)** - Ready today, full support
- **[Flet Apps](ADDING_PQTI_TO_FLET_APPS.md)** - Build adapter, then test
- **[Electron Apps](../docs/ADAPTER_GUIDE.md)** - Future: build adapter
- **[Web Apps (Playwright)](../docs/ADAPTER_GUIDE.md)** - Future: build adapter

### Development Guides

- **[Building Adapters](../docs/ADAPTER_GUIDE.md)** - How to add new framework support
- **[Flet Adapter Implementation Plan](../docs/FLET_ADAPTER_PLAN.md)** - Detailed Flet adapter design
- **[Contributing](CONTRIBUTING.md)** - How to contribute to PQTI

### Reference

- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[MCP Tools Reference](MCP_TOOLS.md)** - All available MCP tools
- **[Protocol Schema](../protocol/schema.json)** - JSON Schema definitions

---

## 🎯 What Is PQTI?

**PQTI is a testing library that enables Claude Code to automatically test GUI applications.**

### The Problem
Testing GUI apps is:
- Manual and time-consuming
- Error-prone
- Hard to repeat
- Different for each framework (PyQt6, Flet, Electron, etc.)

### The Solution
PQTI provides:
- **One line of code** to instrument your app
- **Unified protocol** that works across frameworks
- **Claude Code integration** for AI-powered testing
- **Automatic test generation** - no test code to write

### How It Works

```
Your GUI App  ←→  PQTI Library  ←→  Claude Code
                     ↓
              Automated Tests
```

1. **Add PQTI to your app** (one line of code)
2. **Tell Claude Code to test it**
3. **Get automated tests** - Claude writes them for you

---

## 🚀 Quick Start by Framework

### PyQt6 Apps (Ready Now!)

```python
# Add to your app:
from qt_instrument import enable_instrumentation
app = QApplication(sys.argv)
enable_instrumentation(app)
```

**Time to first test:** 5 minutes
**Guide:** [PyQt6 Guide](PYQT6_GUIDE.md)

### Flet Apps (Build Adapter First)

**Time to build adapter:** ~4 hours
**Time to first test after adapter:** 5 minutes
**Guide:** [Adding PQTI to Flet Apps](ADDING_PQTI_TO_FLET_APPS.md) ⭐

### Other Frameworks

**Status:** Not yet implemented
**How:** Build adapter using [Adapter Guide](../docs/ADAPTER_GUIDE.md)
**Time:** ~4-8 hours per framework

---

## 📖 Learning Path

### For Flet App Users (Your Path!)

1. **Read:** [Adding PQTI to Flet Apps](ADDING_PQTI_TO_FLET_APPS.md)
2. **Give to Claude Code:** The entire Flet guide
3. **Claude builds:** Flet adapter (~4 hours)
4. **Add to your app:** `enable_instrumentation(page)`
5. **Test:** Tell Claude to test your workflows

### For PyQt6 App Users

1. **Read:** [Quick Start Guide](QUICK_START.md)
2. **Add:** One line to your app
3. **Test:** Tell Claude to test
4. **Done:** Tests generated automatically

### For Framework Developers

1. **Read:** [Architecture Overview](ARCHITECTURE.md)
2. **Read:** [Technical Specification](../TECH_SPEC.md)
3. **Read:** [Building Adapters](../docs/ADAPTER_GUIDE.md)
4. **Build:** Your framework's adapter
5. **Share:** Contribute back to PQTI

---

## 🏗️ Architecture Overview

### Three-Layer Design

```
┌────────────────────────────────────────┐
│         Claude Code (User)             │
└───────────────┬────────────────────────┘
                │ MCP Protocol
┌───────────────▼────────────────────────┐
│     PQTI Core (Framework-Agnostic)     │
│  ┌──────────────────────────────────┐  │
│  │  App Controller                  │  │
│  │  - Routes commands               │  │
│  │  - Manages connections           │  │
│  └──────────────────────────────────┘  │
└───────────────┬────────────────────────┘
                │ Adapter Interface
┌───────────────▼────────────────────────┐
│      Framework Adapters                │
│  ┌─────────┬─────────┬──────────────┐  │
│  │ PyQt6   │  Flet   │  Electron    │  │
│  │ ✅ Done │ 🔨 Build│  🔮 Future   │  │
│  └────┬────┴────┬────┴──────┬───────┘  │
└───────┼─────────┼───────────┼──────────┘
        │         │           │
    ┌───▼───┐ ┌───▼───┐ ┌────▼────┐
    │PyQt6  │ │ Flet  │ │Electron │
    │ App   │ │ App   │ │  App    │
    └───────┘ └───────┘ └─────────┘
```

### Key Concepts

**Protocol Layer** (Language-independent)
- JSON-RPC based
- Methods: connect, snapshot, click, type, ping
- Works across all frameworks

**Adapter Layer** (Framework-specific)
- Translates protocol to framework APIs
- PyQt6 uses Unix sockets + QTest
- Flet uses HTTP/WebSocket + Flet APIs
- Each adapter ~150-200 lines of code

**Instrumentation Layer** (In your app)
- Tiny library you import
- One line: `enable_instrumentation(app)`
- Adds remote control capability

---

## 🎯 Use Cases

### 1. Automated Testing
**Before:** Manual clicking through UI
**After:** Claude tests automatically, generates test suite

### 2. Regression Testing
**Before:** Re-test manually after each change
**After:** Run automated tests, catch regressions

### 3. Cross-App Workflows
**Before:** Can't test flows across desktop + web
**After:** Test workflows spanning PyQt6 + Flet apps

### 4. Documentation
**Before:** Write usage docs manually
**After:** Claude generates docs by testing the UI

### 5. Onboarding
**Before:** Train users manually
**After:** Claude creates tutorials by demonstrating workflows

---

## 📊 Status by Framework

| Framework | Status | Time to Use | Adapter Code | Guide |
|-----------|--------|-------------|--------------|-------|
| **PyQt6** | ✅ Production | 5 minutes | Complete | [Guide](PYQT6_GUIDE.md) |
| **Flet** | 🔨 Build adapter | 4 hrs + 5 min | Need to build | [Guide](ADDING_PQTI_TO_FLET_APPS.md) |
| **Electron** | 🔮 Future | TBD | Not started | [Plan](../docs/ADAPTER_GUIDE.md) |
| **Playwright** | 🔮 Future | TBD | Not started | [Plan](../docs/ADAPTER_GUIDE.md) |
| **WPF** | 🔮 Future | TBD | Not started | [Plan](../docs/ADAPTER_GUIDE.md) |

---

## 🤝 Contributing

PQTI is open for contributions:

1. **Build adapters** for new frameworks
2. **Improve documentation**
3. **Report issues** with existing adapters
4. **Share use cases** and patterns

See [Contributing Guide](CONTRIBUTING.md)

---

## 📞 Support

- **Documentation:** You're reading it!
- **Issues:** GitHub Issues
- **Questions:** Start with [FAQ](FAQ.md)

---

## 🔗 Quick Links

**Essential Documents:**
- [Adding PQTI to Flet Apps](ADDING_PQTI_TO_FLET_APPS.md) ← **For Flet users**
- [Quick Start (PyQt6)](QUICK_START.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Technical Specification](../TECH_SPEC.md)

**For Developers:**
- [Building Adapters](../docs/ADAPTER_GUIDE.md)
- [Protocol Specification](../protocol/specification.md)
- [API Reference](API_REFERENCE.md)

**Source Code:**
- Repository: `/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/PQTI`
- License: MIT

---

**Last Updated:** 2026-02-02
**Version:** 2.0
**Status:** Production (PyQt6), Active Development (Flet)
