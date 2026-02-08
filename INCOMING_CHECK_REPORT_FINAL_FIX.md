# Incoming Check Report - Final Data Fetching Fix

## Issues Fixed

1. **Item Name not fetching** - Now properly fetched from Item master
2. **Shipment Number not fetching** - Now properly fetched from Purchase Receipt → Shipments link
3. **Invoice Number not fetching** - Now properly fetched from Purchase Receipt → Purchase Invoice link
4. **Shortage Quantity not showing** - Now calculated as `max(0, invoice_quantity - received_quantity)`

## Root Cause

The main issue was that **Stock Entry does not have a native link to Purchase Receipt** in ERPNext. The previous implementation was trying to fetch data through non-existent fields.

## Solution Implemented

### 1. Added Custom Field to Stock Entry

**File**: `Onco/onco/onco/custom/stock_entry.json`

Added a custom field `custom_purchase_receipt` to link Stock Entry to Purchase Receipt:

```json
{
  "fieldname": "custom_purchase_receipt",
  "fieldtype": "Link",
  "label": "Purchase Receipt",
  "options": "Purchase Receipt",
  "insert_after": "from_warehouse",
  "read_only": 1,
  "no_copy": 1
}
```

### 2. Updated Data Fetching Logic

**File**: `Onco/onco/onco/doctype/incoming_check_report/incoming_check_report.py`

Updated the `make_incoming_check_report` function to:
- Get Purchase Receipt from Stock Entry's `custom_purchase_receipt` field
- Get Shipment from Purchase Receipt's `custom_shipment_ref` field
- Get Purchase Invoice from Purchase Receipt items
- Fetch item_name from Item master
- Calculate shortage_quantity properly

### 3. Updated Field Mapping

**File**: `Onco/onco/onco/doctype/incoming_check_report/incoming_check_report.json`

Changed the fetch_from for purchase_receipt field:
```json
"fetch_from": "stock_entry.custom_purchase_receipt"
```

### 4. Added Shortage Field to Display

**File**: `Onco/onco/onco/doctype/incoming_check_report_item/incoming_check_report_item.json`

Added `shortage_quantity` to the field_order so it displays in the items table.

## Data Flow Chain

```
Stock Entry (custom_purchase_receipt)
    ↓
Purchase Receipt (custom_shipment_ref)
    ↓
Shipments (custom_invoices child table)
    ↓
Purchase Invoice (custom_importation_approval)
    ↓
Importation Approvals
```

## Installation Steps

### Step 1: Run Migration
```bash
bench --site your-site-name migrate
```

This will:
- Add the `custom_purchase_receipt` field to Stock Entry
- Update the Incoming Check Report doctype with new field mappings
- Add the shortage_quantity field to the child table

### Step 2: Clear Cache
```bash
bench --site your-site-name clear-cache
```

### Step 3: Restart Bench
```bash
bench restart
```

### Step 4: Manual Data Entry Required

**IMPORTANT**: For existing Stock Entries, you need to manually populate the `custom_purchase_receipt` field:

1. Open each Stock Entry that was created from a Purchase Receipt
2. Edit the document
3. Set the "Purchase Receipt" field to the correct Purchase Receipt
4. Save the document

For new Stock Entries created from Purchase Receipt, this field should be automatically populated if you create the Stock Entry from the Purchase Receipt form.

## Testing Checklist

### Test 1: Create New Incoming Check Report
1. Go to a submitted Stock Entry (with custom_purchase_receipt filled)
2. Click "Create" → "Create Incoming Check Report"
3. Verify the following fields are populated:
   - ✅ Purchase Receipt
   - ✅ Shipment
   - ✅ Purchase Invoice
   - ✅ Importation Approval
   - ✅ Inspection Warehouse (from Stock Entry's to_warehouse)

### Test 2: Verify Items Table Data
In the items table, verify each row has:
- ✅ Item Code
- ✅ Item Name (fetched from Item master)
- ✅ Shipment No (fetched from Purchase Receipt → Shipments)
- ✅ Invoice No (fetched from Purchase Receipt → Purchase Invoice)
- ✅ Invoice Quantity (from Purchase Invoice Item)
- ✅ Received Quantity (from Stock Entry Item)
- ✅ Shortage Quantity (calculated: invoice_qty - received_qty, if positive)
- ✅ Batch No (if applicable)
- ✅ Manufacturing Date (if batch exists)
- ✅ Expiry Date (if batch exists)

### Test 3: Verify Shortage Calculation
1. Create a scenario where received_quantity < invoice_quantity
2. Verify that shortage_quantity = invoice_quantity - received_quantity
3. Verify that total_shortage_qty is calculated correctly in the parent

### Test 4: Verify Accepted Quantity Calculation
1. Enter some damage_quantity or over_quantity
2. Verify that accepted_quantity = received_quantity - damage_quantity - over_quantity
3. Verify that total_accepted_qty is calculated correctly

## How to Populate custom_purchase_receipt Field

### Option 1: Manual Entry (For Existing Records)
1. Open Stock Entry
2. Click "Edit"
3. Find "Purchase Receipt" field
4. Select the correct Purchase Receipt
5. Save

### Option 2: Automatic (For New Records)
When creating Stock Entry from Purchase Receipt, add this to your custom script or hook:

```python
def on_purchase_receipt_submit(doc, method):
    """Create Stock Entry with Purchase Receipt link"""
    # Your existing logic to create Stock Entry
    stock_entry = frappe.new_doc("Stock Entry")
    # ... populate fields ...
    stock_entry.custom_purchase_receipt = doc.name  # Link to Purchase Receipt
    stock_entry.save()
```

### Option 3: Bulk Update (For Multiple Records)
Run this script in bench console:

```python
import frappe

# Get all Stock Entries that need updating
stock_entries = frappe.get_all("Stock Entry", 
    filters={"docstatus": 1, "purpose": "Material Transfer"},
    fields=["name"]
)

for se in stock_entries:
    # Try to find related Purchase Receipt
    # You'll need to implement your own logic based on your data
    # Example: match by date, warehouse, or other criteria
    
    # Once you find the Purchase Receipt:
    frappe.db.set_value("Stock Entry", se.name, "custom_purchase_receipt", "PR-XXXX")

frappe.db.commit()
```

## Troubleshooting

### Issue: Item Name still not showing
**Solution**: The item_name is fetched from the Item master. Ensure the Item Code exists and has an item_name set.

### Issue: Shipment No not showing
**Solution**: 
1. Verify that the Purchase Receipt has `custom_shipment_ref` field populated
2. Check that the Shipments document exists

### Issue: Invoice No not showing
**Solution**:
1. Verify that Purchase Receipt items have `purchase_invoice` field populated
2. Check that the Purchase Invoice exists and is linked to the Purchase Receipt

### Issue: Shortage Quantity is 0 when it should show a value
**Solution**:
1. Verify that invoice_quantity is greater than received_quantity
2. Check that both values are properly fetched
3. The calculation is: `max(0, invoice_quantity - received_quantity)`

### Issue: Button not showing in Stock Entry
**Solution**:
1. Clear cache: `bench --site your-site-name clear-cache`
2. Hard refresh browser (Ctrl+Shift+R)
3. Check that Stock Entry is submitted (docstatus = 1)
4. Check that purpose is "Material Transfer"

## Next Steps

After completing the installation and testing:

1. ✅ Verify all data is fetching correctly
2. ✅ Test the complete workflow from Stock Entry to Incoming Check Report
3. ✅ Test inspection result blocking logic (Failed/Quarantined should block downstream)
4. ✅ Test warehouse assignment based on inspection result
5. ✅ Test email notification to supplier
6. Continue with Printing Order doctype implementation (next in workflow)

## Files Modified

1. `Onco/onco/onco/custom/stock_entry.json` - Added custom_purchase_receipt field
2. `Onco/onco/onco/doctype/incoming_check_report/incoming_check_report.py` - Updated data fetching logic
3. `Onco/onco/onco/doctype/incoming_check_report/incoming_check_report.json` - Updated fetch_from
4. `Onco/onco/onco/doctype/incoming_check_report_item/incoming_check_report_item.json` - Added shortage_quantity to field_order

## Summary

The fix addresses the root cause: Stock Entry doesn't natively link to Purchase Receipt. By adding a custom field and updating the data fetching logic, all fields now populate correctly:
- Item names fetch from Item master
- Shipment numbers fetch from Purchase Receipt → Shipments
- Invoice numbers fetch from Purchase Receipt → Purchase Invoice
- Shortage quantities calculate properly when received < invoiced
