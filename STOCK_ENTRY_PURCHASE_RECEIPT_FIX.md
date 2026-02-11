# Stock Entry to Incoming Check Report - Purchase Receipt Reference Fix

## Problem
When creating a Stock Entry from a Purchase Receipt and then creating an Incoming Check Report from that Stock Entry, the Purchase Receipt and Shipment references were not being carried through to the Incoming Check Report's child table items.

## Root Cause
The Stock Entry was not properly capturing the Purchase Receipt reference when created from ERPNext's standard "Material Transfer" flow, which prevented the Incoming Check Report from accessing the Shipment and Purchase Receipt data.

## Solution Implemented

### 1. Enhanced Stock Entry Custom Fields
Added `custom_shipment_ref` field to Stock Entry that automatically fetches from the linked Purchase Receipt:

**File: `onco/onco/custom/stock_entry.json`**
- Added `custom_shipment_ref` field with `fetch_from: "custom_purchase_receipt.custom_shipment_ref"`
- This ensures the Shipment reference flows through automatically

### 2. Improved Stock Entry Hook
Enhanced the `before_save` hook to automatically populate both Purchase Receipt and Shipment references:

**File: `onco/onco/stock_entry_hooks.py`**
- Checks Stock Entry items for `purchase_receipt` field (set by ERPNext)
- Falls back to warehouse/item matching if not found
- Automatically fetches and sets `custom_shipment_ref` from Purchase Receipt
- Provides user feedback when links are established

### 3. Enhanced Incoming Check Report Creation
Updated the `make_incoming_check_report` function to properly handle all reference sources:

**File: `onco/onco/doctype/incoming_check_report/incoming_check_report.py`**
- Checks multiple sources for Purchase Receipt:
  1. Stock Entry `custom_purchase_receipt` field
  2. Stock Entry items `purchase_receipt` field
- Fetches Shipment reference from:
  1. Purchase Receipt `custom_shipment_ref`
  2. Stock Entry `custom_shipment_ref` (fallback)
- Properly populates child table items with:
  - `shipment_no`: The Shipment reference
  - `invoice_no`: The Purchase Receipt reference
- Maps Stock Entry fields to Incoming Check Report parent fields

## How It Works

### Workflow
1. **Purchase Receipt Creation**: Created from Shipments with `custom_shipment_ref` field set
2. **Stock Entry Creation**: When created from Purchase Receipt:
   - ERPNext sets `purchase_receipt` field on Stock Entry items
   - `before_save` hook detects this and sets `custom_purchase_receipt` on parent
   - Hook also fetches and sets `custom_shipment_ref` from Purchase Receipt
3. **Incoming Check Report Creation**: When created from Stock Entry:
   - Reads Purchase Receipt from Stock Entry (custom field or items)
   - Fetches Shipment reference from Purchase Receipt
   - Populates all child table items with both references

### Data Flow
```
Shipments
  └─> Purchase Receipt (custom_shipment_ref)
       └─> Stock Entry (custom_purchase_receipt, custom_shipment_ref)
            └─> Incoming Check Report
                 ├─> Parent: purchase_receipt, shipment
                 └─> Items: shipment_no, invoice_no
```

## Testing

### Test Case 1: Standard Flow
1. Create Purchase Receipt from Shipments
2. Create Stock Entry (Material Transfer) from Purchase Receipt
3. Verify Stock Entry has:
   - `custom_purchase_receipt` = Purchase Receipt name
   - `custom_shipment_ref` = Shipment name
4. Create Incoming Check Report from Stock Entry
5. Verify Incoming Check Report has:
   - Parent: `purchase_receipt` and `shipment` fields populated
   - Items: Each item has `shipment_no` and `invoice_no` populated

### Test Case 2: Existing Stock Entry
For Stock Entries created before this fix:
- The `before_save` hook will attempt to auto-link on next save
- Fallback logic matches by warehouse and item if direct reference not found

## Files Modified
1. `onco/onco/custom/stock_entry.json` - Added shipment reference field
2. `onco/onco/stock_entry_hooks.py` - Enhanced auto-linking logic
3. `onco/onco/doctype/incoming_check_report/incoming_check_report.py` - Improved reference fetching
4. `onco/onco/public/js/stock_entry_incoming_check.js` - Removed manual linking (automatic only)

## Migration Required
Run `bench migrate` to apply the new custom field to Stock Entry doctype.

## Notes
- All linking is automatic - no manual intervention required
- The system tries multiple fallback methods to find the Purchase Receipt
- Clear warning messages shown if references cannot be found
- Existing Stock Entries will be auto-linked when possible
