# Claude Development Guidelines for PQTI

**Last Updated:** 2026-02-03
**Project:** PQTI (PyQt Instrument) - Framework-Agnostic GUI Testing

---

## Module Size Standards

### Size Limits (Lines of Code)

| Range | Status | Action |
|-------|--------|--------|
| < 400 | ✅ **Target** | Ideal - maintain this size |
| 400-600 | ⚠️ **Acceptable** | Monitor for growth, consider refactoring |
| 600-800 | 🔶 **Absolute Limit** | Refactor soon |
| > 800 | 🚨 **Priority Refactor** | Must refactor immediately |

### Current PQTI Module Sizes

**Status Check:** (as of 2026-02-03)

```bash
$ find . -name "*.py" -not -path "./.venv/*" -exec wc -l {} + | sort -rn | head -10
```

| Module | LOC | Status |
|--------|-----|--------|
| `qt_instrument/core.py` | 296 | ✅ Target |
| `mcp_server/server.py` | 264 | ✅ Target |
| `tests/test_integration.py` | 238 | ✅ Target |
| `mcp_server/app_controller.py` | 215 | ✅ Target |
| `mcp_server/adapters/base.py` | 181 | ✅ Target |
| `mcp_server/adapters/pyqt6/adapter.py` | 147 | ✅ Target |
| `mcp_server/adapters/pyqt6/transport.py` | 145 | ✅ Target |
| `mcp_server/adapters/flet/adapter.py` | 144 | ✅ Target |
| `mcp_server/qt_client.py` | 139 | ✅ Target |
| `mcp_server/adapters/flet/transport.py` | 104 | ✅ Target |

**Summary:**
- ✅ All modules under 400 LOC (target range)
- ✅ No modules in acceptable range (400-600)
- ✅ No modules at absolute limit (600-800)
- ✅ No modules requiring priority refactor (>800)

**Largest module:** 296 LOC
**Average module size:** ~197 LOC

**Conclusion:** PQTI maintains excellent module size discipline! 🎉

---

## Monitoring Module Growth

### Regular Size Checks

**Check all Python modules:**
```bash
find . -name "*.py" -not -path "./.venv/*" -exec wc -l {} + | sort -rn
```

**Check for modules exceeding target:**
```bash
find . -name "*.py" -not -path "./.venv/*" -exec wc -l {} + | awk '$1 > 400 { print $1, $2 }'
```

**Check for modules requiring immediate refactor:**
```bash
find . -name "*.py" -not -path "./.venv/*" -exec wc -l {} + | awk '$1 > 800 { print "🚨 PRIORITY REFACTOR:", $1, $2 }'
```

### Pre-Commit Check

Before committing, verify no module grew beyond limits:

```bash
# Quick check - shows top 5 largest modules
find . -name "*.py" -not -path "./.venv/*" -exec wc -l {} + | sort -rn | head -6
```

---

## Refactoring Guidelines

### When a Module Approaches 400 LOC

**Consider splitting by:**
1. **Responsibility** - Separate distinct concerns
2. **Layer** - UI vs business logic vs data access
3. **Feature** - Group related functionality
4. **Utilities** - Extract helper functions

### When a Module Exceeds 600 LOC

**Immediate action required:**
1. Identify major sections/responsibilities
2. Extract into separate modules
3. Create subdirectory if needed
4. Update imports
5. Verify tests still pass

### When a Module Exceeds 800 LOC

**🚨 Priority refactor - block other work until fixed:**
1. Stop adding features to this module
2. Plan extraction strategy
3. Split into 2-4 focused modules
4. Target: Each resulting module < 400 LOC
5. Document refactoring in commit message

---

## Example: Refactoring Strategy

**If `qt_instrument/core.py` grew to 800+ LOC:**

**Before** (800+ LOC):
```
qt_instrument/
└── core.py  (800+ lines)
```

**After** (split into focused modules):
```
qt_instrument/
├── __init__.py
├── server.py          # QLocalServer, request handling (~200 LOC)
├── snapshot.py        # Widget tree traversal (~200 LOC)
├── interactions.py    # Click, type, hover actions (~200 LOC)
└── utils.py          # Helper functions (~100 LOC)
```

---

## Architecture Principles

### Keep Modules Focused

**Each module should:**
- Have one clear responsibility
- Be under 400 LOC (target)
- Be independently testable
- Have descriptive name that reflects purpose

### Framework-Agnostic Design

**Adapter pattern keeps modules small:**
- Each adapter ~150 LOC
- Each transport ~100-150 LOC
- Clean separation = smaller files

---

## Key Takeaways

1. ✅ **Target:** < 400 LOC per module
2. ⚠️ **Acceptable:** 400-600 LOC (monitor closely)
3. 🔶 **Absolute limit:** 600-800 LOC (refactor soon)
4. 🚨 **Priority refactor:** > 800 LOC (immediate action)

**PQTI's current state:** All modules well within target! Maintain this standard. ✨

---

## References

- **PQTI Architecture:** `../TECH_SPEC.md`
- **PQTI Status:** `../STATUS.md`
- **Adapter Guide:** `../docs/ADAPTER_GUIDE.md`
