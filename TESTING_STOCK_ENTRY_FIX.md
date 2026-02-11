# Testing Guide: Stock Entry to Incoming Check Report Fix

## Prerequisites
1. Run migration to apply new custom fields:
   ```bash
   bench --site [your-site] migrate
   ```

2. Clear cache:
   ```bash
   bench --site [your-site] clear-cache
   ```

## Test Scenario: Complete Flow

### Step 1: Verify Purchase Receipt Has Shipment Reference
1. Open Purchase Receipt: `MAT-PRE-2026-00009` (or any Purchase Receipt created from Shipments)
2. Check that `Shipment Ref` field is populated
3. Note the Shipment number (e.g., `hqlkcmp60d`)

### Step 2: Create Stock Entry from Purchase Receipt
1. Open the Purchase Receipt
2. Click "Create" > "Stock Entry" (Material Transfer)
3. Fill in required fields:
   - Purpose: Material Transfer
   - Source Warehouse: (the warehouse from Purchase Receipt)
   - Target Warehouse: (inspection warehouse)
4. Save and Submit the Stock Entry
5. **VERIFY**: Check that the Stock Entry now has:
   - `Purchase Receipt` field = `MAT-PRE-2026-00009`
   - `Shipment Ref` field = `hqlkcmp60d`
   - You should see an alert message: "Purchase Receipt [name] linked to Stock Entry"

### Step 3: Create Incoming Check Report
1. From the Stock Entry, click "Create" > "Create Incoming Check Report"
2. **VERIFY** the Incoming Check Report form:
   - `Stock Entry` = Your Stock Entry number
   - `Purchase Receipt` = `MAT-PRE-2026-00009`
   - `Shipment` = `hqlkcmp60d`
   - `Inspection Warehouse` = Target warehouse from Stock Entry

### Step 4: Verify Child Table Items
1. Scroll to the "Items" section in Incoming Check Report
2. For each item row, **VERIFY**:
   - `Shipment No` = `hqlkcmp60d` (should be populated automatically)
   - `Invoice No` = `MAT-PRE-2026-00009` (should be populated automatically)
   - `Item Code` = Correct item
   - `Received Quantity` = Quantity from Stock Entry
   - `Invoice Quantity` = Quantity from Purchase Receipt

### Step 5: Complete the Inspection
1. Fill in inspection details
2. Save and Submit
3. Should work without any "No Purchase Receipt linked" warnings

## Expected Results

### ✅ Success Indicators
- Stock Entry automatically has Purchase Receipt and Shipment references
- Incoming Check Report parent fields are populated
- All child table items have `shipment_no` and `invoice_no`
- No warning messages about missing Purchase Receipt
- Can save and submit Incoming Check Report successfully

### ❌ Failure Indicators
- Stock Entry missing `Purchase Receipt` or `Shipment Ref` fields
- Incoming Check Report shows warning: "No Purchase Receipt linked"
- Child table items have empty `Shipment No` or `Invoice No` fields
- Cannot create Incoming Check Report

## Troubleshooting

### Issue: Stock Entry doesn't have Purchase Receipt reference
**Cause**: Stock Entry items don't have `purchase_receipt` field set

**Solution**: 
1. Check if the Stock Entry was created from Purchase Receipt using standard ERPNext flow
2. The hook will try to match by warehouse and item as fallback
3. If still not working, check the console for any error messages

### Issue: Shipment reference is missing
**Cause**: Purchase Receipt doesn't have `custom_shipment_ref` field

**Solution**:
1. Verify the Purchase Receipt was created from Shipments doctype
2. Check Purchase Receipt has `custom_shipment_ref` field populated
3. If missing, the Purchase Receipt may have been created manually

### Issue: Child table items missing references
**Cause**: The `make_incoming_check_report` function couldn't find Purchase Receipt

**Solution**:
1. Check Stock Entry has `custom_purchase_receipt` field
2. Check browser console for JavaScript errors
3. Verify the `make_incoming_check_report` method is being called correctly

## Manual Verification Query

Run this query in ERPNext console to check Stock Entry links:

```python
# Check Stock Entry
se = frappe.get_doc("Stock Entry", "MAT-STE-2026-00007")
print(f"Purchase Receipt: {se.custom_purchase_receipt}")
print(f"Shipment Ref: {se.custom_shipment_ref}")

# Check if items have purchase_receipt
for item in se.items:
    print(f"Item {item.item_code}: purchase_receipt = {item.get('purchase_receipt')}")
```

## Notes
- The fix is automatic - no manual intervention needed
- All existing Stock Entries will be auto-linked when possible
- The system provides clear feedback messages during the process
