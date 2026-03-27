# CRITICAL FIX: Net Released Qty Calculation Error

## Date: March 27, 2026
## Issue: Net Released Qty showing negative values
## Status: ✅ FIXED

---

## Problem Description

The `net_released_qty` field in Authority Good Release was showing negative values when using "With Shortage Control Quantity" subtype.

### Example of the Bug:
- **Requested Qty**: 500
- **Released Qty**: 200
- **Shortage Control Qty**: 300
- **Net Released Qty**: -100 ❌ (WRONG!)

### Root Cause

There were TWO methods calculating `net_released_qty` with CONFLICTING logic:

1. **`calculate_quantities()` method (Line 187)**:
   ```python
   item.net_released_qty = item.released_qty or 0  # CORRECT ✓
   ```

2. **`calculate_net_quantities()` method (Line 836)**:
   ```python
   item.net_released_qty = (item.released_qty or 0) - (item.shortage_control_qty or 0)  # WRONG ✗
   ```

The `calculate_net_quantities()` method was called AFTER `calculate_quantities()` in the `validate()` method, overwriting the correct value with the wrong formula.

**Wrong Formula**: `Net Released = Released - Shortage Control`
- Example: 200 - 300 = -100 ❌

---

## Correct Understanding

### Shortage Control Concept

When using "With Shortage Control Quantity":

1. **Requested Qty** = Total quantity available for release (from Incoming Check Report)
2. **Released Qty** = Quantity being released to warehouse NOW
3. **Shortage Control Qty** = Quantity being held back for future release
4. **Net Released Qty** = Same as Released Qty (what actually moves to warehouse)

### Correct Formula

```
Requested Qty = Released Qty + Shortage Control Qty
```

### Example:
- **Requested Qty**: 500 (total available)
- **Released Qty**: 200 (releasing now)
- **Shortage Control Qty**: 300 (holding back)
- **Net Released Qty**: 200 (moves to warehouse) ✓

**Validation**: 500 = 200 + 300 ✓

---

## The Fix

### File Modified
`Onco/onco/onco/doctype/authority_good_release/authority_good_release.py`

### Changes Made

#### 1. Updated `calculate_quantities()` method (Line ~163-193)
Added clearer comments explaining the logic:

```python
# Net released = released qty (what actually moves to released warehouse)
# Shortage control qty stays in source warehouse
# Formula: Requested = Released + Shortage Control
# Example: 500 = 200 + 300
# Net Released = 200 (moves to warehouse)
item.net_released_qty = item.released_qty or 0
```

#### 2. Fixed `calculate_net_quantities()` method (Line ~830-850)
Changed from WRONG formula to CORRECT formula:

**BEFORE (WRONG)**:
```python
def calculate_net_quantities(self):
    """Calculate net released quantities based on shortage control
    Formula: Net released = released_qty - shortage_control_qty
    """
    for item in self.items:
        if self.lrb_subtype == "With Shortage Control Quantity":
            # Net Released = Released Qty - Shortage Control Qty
            item.net_released_qty = (item.released_qty or 0) - (item.shortage_control_qty or 0)
```

**AFTER (CORRECT)**:
```python
def calculate_net_quantities(self):
    """Calculate net released quantities based on shortage control
    
    IMPORTANT: Net Released Qty = Released Qty (the amount going to warehouse)
    The shortage control quantity stays in the source warehouse.
    
    Formula: Requested Qty = Released Qty + Shortage Control Qty
    Example: 500 = 200 + 300
    
    Net Released Qty = Released Qty = 200 (what moves to released warehouse)
    Shortage Control Qty = 300 (what stays in source warehouse)
    """
    for item in self.items:
        if self.lrb_subtype == "With Shortage Control Quantity":
            # Net Released = Released Qty (NOT released - shortage!)
            # The shortage control qty stays in source warehouse
            # The released qty is what actually moves to released warehouse
            item.net_released_qty = item.released_qty or 0
```

---

## Impact

### Before Fix:
- ❌ Net Released Qty showed negative values
- ❌ Total Net Released Qty in parent showed negative sum
- ❌ Stock entries would fail or create incorrect quantities
- ❌ Confusing for users

### After Fix:
- ✅ Net Released Qty = Released Qty (correct)
- ✅ Total Net Released Qty = Sum of Released Qty (correct)
- ✅ Stock entries create with correct quantities
- ✅ Clear and logical for users

---

## Business Logic Explanation

### Scenario: Releasing goods in batches

**Initial State** (from Incoming Check Report):
- Total goods received and inspected: 500 units

**First Release** (Authority Good Release #1):
- Want to release: 200 units to sales warehouse
- Want to hold back: 300 units for future release
- **Requested Qty**: 500
- **Released Qty**: 200
- **Shortage Control Qty**: 300
- **Net Released Qty**: 200

**Stock Movement**:
- 200 units → Released Goods Warehouse ✓
- 300 units → Stay in Inspection Warehouse ✓

**Second Release** (Authority Good Release #2 - later):
- Can release the remaining 300 units
- **Requested Qty**: 300 (from remaining)
- **Released Qty**: 300
- **Shortage Control Qty**: 0
- **Net Released Qty**: 300

---

## Testing Instructions

### Test Case 1: With Shortage Control

1. Create Authority Good Release
2. Select Release Type: "Lot Release Batch"
3. Select LRB Subtype: "With Shortage Control Quantity"
4. Add item with:
   - Requested Qty: 500
   - Released Qty: 200
   - Shortage Control Qty: 300
5. Save document
6. **Verify**:
   - Net Released Qty = 200 ✓
   - Total Net Released Qty = 200 ✓
   - No negative values ✓

### Test Case 2: Without Shortage Control

1. Create Authority Good Release
2. Select Release Type: "Lot Release Batch"
3. Select LRB Subtype: "Without Shortage Control Quantity"
4. Add item with:
   - Requested Qty: 500
   - Released Qty: 500
5. Save document
6. **Verify**:
   - Net Released Qty = 500 ✓
   - Shortage Control Qty = 0 ✓
   - Total Net Released Qty = 500 ✓

### Test Case 3: Auto-calculation

1. Create Authority Good Release with shortage control
2. Add item with:
   - Requested Qty: 500
   - Released Qty: 200
   - Leave Shortage Control Qty empty
3. Save document
4. **Verify**:
   - Shortage Control Qty auto-calculated to 300 ✓
   - Net Released Qty = 200 ✓

---

## Related Issues

This fix resolves:
- **Issue #20**: Total Net Released Qty calculation mismatch
- **Negative values bug**: Net Released Qty showing negative numbers
- **Stock entry errors**: Incorrect quantities in stock movements

---

## Deployment Priority

🔴 **CRITICAL** - Deploy immediately

This bug affects:
- Data integrity
- Stock movements
- User confusion
- Workflow blocking

---

## Rollback Plan

If issues occur after deployment:

1. The old (wrong) formula was:
   ```python
   item.net_released_qty = (item.released_qty or 0) - (item.shortage_control_qty or 0)
   ```

2. To rollback, revert the changes in `calculate_net_quantities()` method

3. However, **DO NOT ROLLBACK** - the old formula was mathematically incorrect

---

## Conclusion

The Net Released Qty calculation is now correct. The formula `Net Released = Released Qty` properly represents the quantity moving to the released warehouse, while the shortage control quantity stays in the source warehouse for future release.

**Formula Summary**:
```
Requested Qty = Released Qty + Shortage Control Qty
Net Released Qty = Released Qty
```

**Example**:
```
500 = 200 + 300
Net Released = 200
```

✅ **Ready for immediate deployment**

