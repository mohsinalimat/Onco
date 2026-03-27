# CRITICAL FIX: Negative Stock Error in Authority Good Release

## Issue #27: Negative Stock Error When Creating Stock Entries

### Problem
When clicking "Create Stock Entries" button in Authority Good Release, the system showed this error:
```
Batch No 1234 of an Item 3400932914692 has negative stock of quantity -200.0 
in the warehouse Imported Finished Phr Receipt and Inspection Warehouse - Onco
```

Even though the Stock Ledger showed 1,001 units available in the batch.

### Root Cause
The stock entry creation methods were using the WRONG source warehouse:

1. **`create_released_stock_entry()`** called `get_source_warehouse()` which fetched the warehouse from Incoming Check Report's `inspection_warehouse` field
2. **`create_sample_stock_entry()`** also called `get_source_warehouse()` 
3. The `source_warehouse` field in Authority Good Release had default value "Under Release - O"
4. But the actual stock was in "Imported Finished Phr Receipt and Inspection Warehouse - Onco"

This mismatch caused the system to try transferring stock from a warehouse where it didn't exist, resulting in negative stock errors.

### Solution

#### 1. Fixed `create_released_stock_entry()` Method
**File**: `Onco/onco/onco/doctype/authority_good_release/authority_good_release.py`

Changed from:
```python
# Get source warehouse from Incoming Check Report
source_warehouse = self.get_source_warehouse()
```

To:
```python
# Use source_warehouse field from the document
source_warehouse = self.source_warehouse

# Validate source_warehouse is set
if not source_warehouse:
    frappe.throw(_("Source Warehouse is required to create released stock entry"))
```

#### 2. Fixed `create_sample_stock_entry()` Method
**File**: `Onco/onco/onco/doctype/authority_good_release/authority_good_release.py`

Changed from:
```python
# Get source warehouse from Incoming Check Report
source_warehouse = self.get_source_warehouse()
```

To:
```python
# Use source_warehouse field from the document
source_warehouse = self.source_warehouse

# Validate source_warehouse is set
if not source_warehouse:
    frappe.throw(_("Source Warehouse is required to create sample stock entry"))
```

#### 3. Updated Default Source Warehouse
**File**: `Onco/onco/onco/doctype/authority_good_release/authority_good_release.json`

Changed the `source_warehouse` field default from:
```json
"default": "Under Release - O"
```

To:
```json
"default": "Imported Finished Phr Receipt and Inspection Warehouse - Onco"
```

### Why This Fix Works

1. **Direct Field Usage**: Now uses the `source_warehouse` field directly from the Authority Good Release document, which the user can see and verify
2. **Correct Default**: The default warehouse now matches where stock actually exists after Purchase Receipt
3. **User Control**: Users can change the source warehouse if needed before creating stock entries
4. **Validation**: Added validation to ensure source warehouse is set before creating stock entries

### Testing Steps

1. Open an Authority Good Release document
2. Verify the "Source Warehouse" field shows "Imported Finished Phr Receipt and Inspection Warehouse - Onco"
3. Check that this matches where your batch stock actually exists (use Stock Ledger)
4. Click "Create Stock Entries" button
5. Stock entries should now be created successfully without negative stock errors

### Impact

- Fixes negative stock errors when creating stock entries
- Ensures stock is transferred from the correct warehouse
- Provides transparency - users can see and modify the source warehouse
- Maintains data integrity in stock ledger

### Related Issues
- Issue #26: Serial/Batch Bundle "already used" error (also fixed)
- Issue #20: Net Released Qty showing negative values (fixed)

---
**Status**: ✅ COMPLETED
**Date**: March 27, 2026
**Files Modified**: 2
