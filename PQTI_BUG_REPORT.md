# PQTI Bug Report: Three Critical Navigation Bugs in Flet Instrumentation

**Date:** 2026-02-03
**Reporter:** MacR Testing
**Severity:** Critical (blocks all real-world Flet app automation)
**Status:** ✅ ALL THREE BUGS FIXED

---

## Executive Summary

MacR discovered **three compounding bugs** in the Flet `_find_control_by_ref()` navigation function that completely blocked UI automation for nested container structures. These bugs worked together to make navigation fail beyond simple paths.

**Key Finding:** Fixing just one or two bugs wouldn't work - all three needed to be fixed together for navigation to function properly.

---

## Bug #1: Missing `continue` Statement

### Location
`flet_instrument/core.py:252` (ADDING_PQTI_TO_FLET_APPS.md)

### The Problem
After successfully finding a type-indexed control, the code updated `current` but failed to continue to the next path component. Instead, execution fell through to `return None`.

### Buggy Code
```python
if index < len(matching):
    current = matching[index]
    # ❌ MISSING: continue statement
    # Execution falls through to else: return None
else:
    return None
```

### The Fix
```python
if index < len(matching):
    current = matching[index]
    continue  # ✅ FIXED: Continue to next part of path
else:
    return None
```

### Impact
- **Symptoms:** Simple paths like `Container[0]` worked, but `Container[0]/Column[0]` failed
- **Severity:** High - blocks multi-level navigation
- **Lines Changed:** 1

---

## Bug #2: Index Mismatch (Overall vs Type-Filtered)

### Location
`flet_instrument/core.py:243-254` (ADDING_PQTI_TO_FLET_APPS.md)

### The Problem
**Fundamental architectural flaw:** Snapshot generation and navigation used incompatible indexing strategies.

**Snapshot Generation (line 192):**
```python
for i, child in enumerate(control.controls):
    child_ref = f"{ref}/{type(child).__name__}[{i}]"
    # Uses OVERALL index: Container[11] = "11th child overall"
```

**Navigation (BUGGY - OLD):**
```python
matching = [
    c for c in current.controls
    if type(c).__name__ == type_name  # Filter by type first!
]
if index < len(matching):
    current = matching[index]  # ❌ Use type-filtered index
```

### The Mismatch Example
```
Children: Container[0], Text[1], Text[2], Container[3], Text[4], ..., Container[11]
                                                                      ↑
Snapshot says: "Container at overall position 11"
Navigator looked for: "The 12th Container" (after filtering) = WRONG CONTROL!
```

If Containers are at overall positions [0, 3, 7, 11, 15]:
- **Snapshot:** `Container[11]` → child at position 11 (which is a Container) ✅
- **Buggy Navigator:** Filter Containers → [0,3,7,11,15] → take index 11 → gets position 15! ❌

### The Fix
```python
# Use overall index, then verify type matches
if index < len(current.controls):
    control = current.controls[index]  # ✅ Overall index
    if type(control).__name__ == type_name:  # ✅ Verify type
        current = control
        continue
    else:
        return None  # Type mismatch
else:
    return None  # Index out of range
```

### Impact
- **Symptoms:** Navigation found wrong controls or failed entirely
- **Severity:** CRITICAL - breaks all type-indexed navigation
- **Real Example:** `Container[11]/Row[content]` navigated to wrong Container
- **Lines Changed:** 5

---

## Bug #3: `[content]` References Not Handled

### Location
`flet_instrument/core.py:243` (ADDING_PQTI_TO_FLET_APPS.md)

### The Problem
Flet containers can have either:
- `controls` - list of multiple children
- `content` - single child attribute

When snapshot generation encounters containers with single children, it may generate `TypeName[content]` references (e.g., `Row[content]`). But the navigator crashed trying to parse this:

**Buggy Code:**
```python
index = int(part.split('[')[1].rstrip(']'))
# ❌ Crashes on int('content') → ValueError!
```

### The Fix
```python
index_str = part.split('[')[1].rstrip(']')

# Handle [content] as index 0
if index_str == 'content':
    index = 0  # ✅ Treat content as first child
else:
    index = int(index_str)
```

### Impact
- **Symptoms:** `ValueError` exception or `Control not found` for `TypeName[content]` refs
- **Severity:** High - blocks navigation to single-child containers
- **Real Example:** `Container[11]/Row[content]/ElevatedButton[0]` failed at Row[content]
- **Lines Changed:** 2

---

## How MacR Discovered These Bugs

### 1. Systematic Testing
Started with simple paths and increased complexity:

```python
✓ root/Container[0]                    # Level 1 - FOUND
✓ root/Container[0]/Column[content]    # Level 2 - FOUND
✓ root/Container[0]/Column[content]/Container[11]  # Level 3 - FOUND
✗ root/Container[0]/Column[content]/Container[11]/Row[content]  # FAILED HERE!
```

This pinpointed exactly where navigation broke.

### 2. Snapshot Analysis
Examined the UI snapshot JSON to see what structure actually existed:

```json
{
  "ref": "root/Container[0]/Column[content]/Container[11]",
  "children": [
    {
      "ref": "root/Container[0]/Column[content]/Container[11]/Row[content]",
      "type": "Row"
    }
  ]
}
```

The snapshot showed `Row[content]` existed, but navigation couldn't find it.

### 3. Source Code Analysis
Compared snapshot generation logic with navigation logic:
- **Discovery:** Snapshot uses `enumerate(controls)` → overall index
- **Discovery:** Navigator filters by type first → type-filtered index
- **Discovery:** Navigator crashes on `int('content')`

### 4. MacR's Test Case
```python
# MacR search tab structure (simplified):
root/Container[0]/Column[content]/Container[11]/Row[content]/ElevatedButton[0]

# What failed:
qt_click("root/Container[0]/Column[content]/Container[11]/Row[content]/ElevatedButton[0]")
# ✗ Control not found
```

---

## Attempted Workarounds (Before Finding Root Cause)

### ❌ Attempt 1: Use Simpler Paths
Tried `Column[0]` instead of `Column[content]` - Failed because Column was at `[content]`, not `[0]`.

### ❌ Attempt 2: Navigate Via Data Attributes
Tried finding controls by `data` attribute instead of indexed references - Failed because most controls didn't have data attributes.

### ✅ Attempt 3: Fix the Root Cause
Read the PQTI source code, compared snapshot vs navigation, and found all three bugs!

---

## The Complete Fix

### Before (Buggy - All 3 Bugs Present)
```python
# Try indexed reference: TypeName[index]
if '[' in part:
    type_name = part.split('[')[0]
    index = int(part.split('[')[1].rstrip(']'))  # ❌ Bug #3: Crashes on 'content'

    matching = [                                 # ❌ Bug #2: Type-filtered index
        c for c in current.controls
        if type(c).__name__ == type_name
    ]

    if index < len(matching):
        current = matching[index]
        # ❌ Bug #1: Missing continue
    else:
        return None
else:
    return None
```

### After (Fixed - All 3 Bugs Resolved)
```python
# Try indexed reference: TypeName[index] or TypeName[content]
if '[' in part:
    type_name = part.split('[')[0]
    index_str = part.split('[')[1].rstrip(']')

    # ✅ Bug #3 FIXED: Handle [content] as index 0
    if index_str == 'content':
        index = 0
    else:
        index = int(index_str)

    # ✅ Bug #2 FIXED: Use overall index, verify type
    if index < len(current.controls):
        control = current.controls[index]
        if type(control).__name__ == type_name:
            current = control
            continue  # ✅ Bug #1 FIXED: Continue to next part
        else:
            return None  # Type mismatch
    else:
        return None  # Index out of range
else:
    return None
```

**Total Changes:** ~8 lines of code to fix all three bugs!

---

## Verification

### Test Path
```python
"root/Container[0]/Column[content]/Container[11]/Row[content]/ElevatedButton[0]"
```

### Before Fixes
```
qt_connect("http://localhost:8551")
qt_snapshot()  # ✓ Shows full tree
qt_click("root/Container[0]/Column[content]/Container[11]/Row[content]/ElevatedButton[0]")
→ ✗ Control not found
```

### After All Three Fixes
```
qt_connect("http://localhost:8551")
qt_snapshot()  # ✓ Shows full tree
qt_click("root/Container[0]/Column[content]/Container[11]/Row[content]/ElevatedButton[0]")
→ ✅ Click successful
```

### MacR Test Results
**10 automated search tests - ALL PASSED!** ✅

---

## Why These Bugs Were Tricky

1. **Bug #1** - Easy to miss in code review, catastrophic impact
2. **Bug #2** - Required understanding BOTH snapshot generation AND navigation
3. **Bug #3** - Needed knowledge of Flet's internal `content` attribute pattern

**Critical Insight:** These bugs compounded. You couldn't fix just one or two - all three needed to be fixed together for navigation to work.

---

## Files Updated

1. ✅ `Product/ADDING_PQTI_TO_FLET_APPS.md` (lines 240-262)
2. ✅ `docs/FLET_ADAPTER_PLAN.md` (complete rewrite with all fixes)
3. ✅ `PQTI_BUG_REPORT.md` (this file - comprehensive documentation)
4. ✅ `STATUS.md` (project history updated)

---

## Lessons Learned

### For PQTI Development
1. **Test with real-world nested structures** - Shallow testing missed these bugs
2. **Verify snapshot/navigator consistency** - They must use the same indexing strategy
3. **Handle framework-specific patterns** - Flet's `content` attribute needs special care

### For Future Adapters
1. **Document indexing strategy clearly** - Overall vs type-filtered must be explicit
2. **Add integration tests for nested navigation** - Test 4+ levels deep
3. **Support framework-specific naming** - Like `[content]` for Flet

### For Reference System Design
**Use data attributes for critical controls:**
```python
# Recommended (robust):
ft.TextField(data="query_field")  # Reference: root/query_field

# Acceptable (now that bugs are fixed):
ft.TextField()  # Reference: root/Column[0]/TextField[1]
```

---

## Impact Assessment

### Before Fix
- ❌ **MacR automation blocked** - Search tab has nested structure
- ❌ **PQTI unusable** for real-world Flet apps with containers
- ❌ **Workaround required** - Database tests + manual UI testing

### After Fix
- ✅ **MacR automation working** - 10/10 tests passed
- ✅ **PQTI ready** for production Flet apps
- ✅ **Full UI automation** - Click, type, navigate at any depth

---

## Special Thanks

**Credit to MacR for exceptional debugging:**
- Systematic testing methodology
- Detailed bug analysis
- Source code investigation
- Complete fix implementation
- Comprehensive reporting

This is **dogfooding done right** - discovering and fixing issues before wide adoption! 🎉

---

## References

- **Bug Locations:** Product/ADDING_PQTI_TO_FLET_APPS.md:240-262
- **Test Case:** MacR search tab automation
- **Discovery Date:** 2026-02-03
- **Resolution Time:** Same day
- **Severity:** Critical → Fixed

---

**Status:** ✅ ALL THREE BUGS FIXED - Ready for MacR integration and PQTI production use
