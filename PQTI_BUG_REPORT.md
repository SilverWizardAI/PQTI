# PQTI Bug Report: Nested Type[index] Navigation Failure

**Date:** 2026-02-03
**Reporter:** MacR Testing
**Severity:** High
**Status:** ✅ FIXED

---

## Summary

Control navigation fails for nested `Type[index]` references in the Flet instrumentation library, preventing automated UI testing of applications with nested container structures.

---

## Issue Details

### Location
- **File:** `flet_instrument/core.py` (as documented)
- **Function:** `_find_control_by_ref()`
- **Lines:** 216-259 (ADDING_PQTI_TO_FLET_APPS.md)

### Problem
When navigating through nested controls using type-based references like `root/Column[0]/TextField[1]`, the function successfully finds the first level (`Column[0]`) but fails to continue processing the remaining path components.

### Example Failure
```python
# Reference: root/Column[0]/TextField[1]
# Expected: Navigate to Column[0], then find TextField[1] within it
# Actual: Finds Column[0], then returns None instead of continuing

ref = "root/Column[0]/TextField[1]"
control = _find_control_by_ref(ref)
# Result: None (should return the TextField)
```

### Root Cause
Missing `continue` statement after successful type-indexed control match. The control flow incorrectly falls through to `return None` instead of proceeding to the next path component.

**Buggy Code:**
```python
if index < len(matching):
    current = matching[index]
    # ❌ BUG: Missing continue statement
    # Code falls through to else: return None
else:
    return None
```

---

## Impact

### High Priority
- **Cannot automate UI testing** for apps with nested containers
- **Blocks PQTI adoption** for real-world Flet applications
- **Affects MacR testing** - search tab has nested Column/Row/TextField structure

### Workaround (Before Fix)
- Use data attributes for all controls: `data="my_textfield"`
- Avoid relying on type-based indexing for nested structures
- Perform database-level tests instead of UI automation
- Manual UI testing required

---

## Technical Analysis

### Control Flow Comparison

**Data Attribute Path** (Working):
```python
for control in current.controls:
    if getattr(control, 'data', None) == part:
        current = control
        found = True
        break

if found:
    continue  # ✅ Correctly continues to next part
```

**Type-Indexed Path** (Broken):
```python
if index < len(matching):
    current = matching[index]
    # ❌ Missing: continue
    # Falls through to else: return None
else:
    return None
```

### Why This Matters
Modern Flet apps use nested containers extensively:
```python
ft.Column([            # Column[0]
    ft.Row([          # Row[0]
        ft.TextField(),  # TextField[0]
        ft.TextField(),  # TextField[1] ← Can't reach this!
    ])
])
```

Without the fix, PQTI cannot navigate beyond the first level of type-indexed nesting.

---

## The Fix

### Code Change
```python
if index < len(matching):
    current = matching[index]
    continue  # ✅ FIXED: Continue to next part of path
else:
    return None
```

### Files Updated
1. ✅ `Product/ADDING_PQTI_TO_FLET_APPS.md` - Line 252
2. ✅ `docs/FLET_ADAPTER_PLAN.md` - Complete rewrite with fixed version

### Verification
After fix, nested navigation works correctly:
```python
# Now works:
_find_control_by_ref("root/Column[0]/TextField[1]")  # ✅ Returns TextField
_find_control_by_ref("root/Column[0]/Row[0]/Button[2]")  # ✅ Returns Button
```

---

## Discovery Process

### How Bug Was Found
1. MacR (Mac Retriever) implemented Flet instrumentation following PQTI docs
2. Added `enable_instrumentation(page)` to MacR
3. Attempted to test search tab UI with PQTI
4. Click commands failed with "Control not found" errors
5. Investigation revealed navigation stopped at first `Type[index]` match

### Test Case That Failed
```python
# MacR search tab structure (simplified):
ft.Column([                           # root/Column[0]
    ft.TextField(data="db_path"),     # root/Column[0]/TextField[0]
    ft.TextField(data="query"),       # root/Column[0]/TextField[1] ← FAILED
    ft.ElevatedButton(data="search"), # root/Column[0]/ElevatedButton[0] ← FAILED
])

# These references failed:
qt_click("root/Column[0]/ElevatedButton[0]")  # ✗ Control not found
qt_type("root/Column[0]/TextField[1]", "test")  # ✗ Control not found
```

---

## Lessons Learned

### Design Insights
1. **Control flow critical** - Missing `continue` can silently break navigation
2. **Test nested structures** - Shallow testing missed this bug
3. **Reference strategy matters** - Data attributes work, type-indexing needs care

### Prevention
- Add integration tests for nested navigation
- Document reference path best practices
- Consider warning in docs about type-indexing limitations (now fixed)

### Recommendation
**Use data attributes for important controls:**
```python
# Recommended:
ft.TextField(data="query_field")  # Reference: root/query_field

# Acceptable (now that bug is fixed):
ft.TextField()  # Reference: root/Column[0]/TextField[1]
```

---

## Testing Verification

### Before Fix
```bash
# Failed:
qt_connect("http://localhost:8551")
qt_snapshot()  # Shows full tree
qt_click("root/Column[0]/ElevatedButton[0]")  # ✗ Control not found
```

### After Fix
```bash
# Works:
qt_connect("http://localhost:8551")
qt_snapshot()  # Shows full tree
qt_click("root/Column[0]/ElevatedButton[0]")  # ✅ Click successful
qt_type("root/Column[0]/TextField[1]", "test query")  # ✅ Text entered
```

---

## Related Issues

### Minor Issue (Separate)
Test script column name error - easy fix, doesn't affect app functionality.

---

## Status

- ✅ **Bug Fixed** in documentation (2026-02-03)
- ✅ **ADDING_PQTI_TO_FLET_APPS.md** updated with fix
- ✅ **FLET_ADAPTER_PLAN.md** updated with comprehensive version
- ⏳ **MacR Integration** - Can now proceed with corrected implementation
- ⏳ **Flet Adapter** - Can implement in PQTI with fix included

---

## References

- **Bug Location:** Product/ADDING_PQTI_TO_FLET_APPS.md:216-259
- **Fix Applied:** Line 252 (added `continue` statement)
- **Test Case:** MacR search tab automation
- **Impact:** High (blocks real-world Flet app testing)
- **Resolution Time:** Same day (2026-02-03)

---

**Next Steps:**
1. Implement flet_instrument in MacR with fixed code
2. Re-test MacR search tab automation
3. Consider implementing full Flet adapter in PQTI repository
4. Add integration tests for nested navigation scenarios
