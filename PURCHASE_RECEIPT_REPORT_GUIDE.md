# Purchase Receipt Report - Quick Guide

## How to Submit Purchase Receipt Report

### Why It's Saved as Draft
When you create Purchase Receipt Report from Incoming Check Report, it's created in **Draft** status by default. This allows you to review and verify all the mapped data before finalizing it.

### Steps to Submit

1. **Open the Purchase Receipt Report**
   - It should be in Draft status (docstatus = 0)

2. **Review All Fields**
   - Purchase Receipt reference
   - Shipment reference
   - Vehicle inspection checks
   - Document checks
   - Physical checks
   - Temperature control data
   - Items with quantities

3. **Verify Items Table**
   - Check all items are correct
   - Verify quantities:
     - Invoice Qty
     - Received Qty
     - Damage Qty
     - Over Qty
     - Accepted Qty (auto-calculated)

4. **Click Submit Button**
   - Located at the top right of the form
   - Button will be blue/primary color
   - Click it to submit the document

5. **Confirm Submission**
   - System may ask for confirmation
   - Click "Yes" to confirm
   - Document status changes to "Submitted" (docstatus = 1)

---

## How to Create Printing Order

### After Submitting Purchase Receipt Report

1. **The "Create" Button Appears**
   - After submission, you'll see a "Create" dropdown button
   - Located at the top right of the form

2. **Click "Create" > "Printing Order"**
   - This opens the Printing Order creation dialog
   - System automatically maps data from Purchase Receipt Report

3. **Review Mapped Data**
   - Shipment No (auto-filled)
   - Date (auto-filled)
   - Items with quantities (auto-filled from accepted_qty)

4. **Save and Submit Printing Order**
   - Click "Save"
   - Review the data
   - Click "Submit"

5. **Mark as Completed**
   - After submission, click "Mark as Completed" button
   - This changes the status to "Completed"

6. **Create Authority Good Release**
   - After marking as Completed
   - "Create" button appears again
   - Click "Create" > "Authority Good Release"

---

## Troubleshooting

### Issue: Purchase Receipt Report Created from Incoming Check Report is Stuck in Draft

**Symptoms**:
- Purchase Receipt Report is created but only shows "Save" button
- No "Submit" button appears
- Document appears to be saved but cannot be submitted

**Root Causes**:
1. **No items mapped**: The document was created without any items in the child table
2. **Validation error**: A validation is failing silently
3. **Permission issue**: User doesn't have submit permission
4. **Browser cache**: Old JavaScript is cached

**Solutions**:

1. **Check if items exist**:
   - Open the Purchase Receipt Report
   - Scroll down to the "Items" section
   - If the table is empty, the document cannot be submitted
   - **Fix**: Go back to Incoming Check Report and ensure it has items before creating PRR

2. **Verify Incoming Check Report is submitted**:
   - The source Incoming Check Report MUST be submitted (docstatus = 1)
   - If it's in Draft, submit it first
   - Then create the Purchase Receipt Report again

3. **Clear browser cache and reload**:
   ```
   - Press Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
   - Or clear browser cache completely
   - Log out and log back in
   ```

4. **Check for validation errors**:
   - Open browser console (F12)
   - Look for red error messages
   - Check the ERPNext error log: Setup > Error Log

5. **Verify permissions**:
   ```python
   # In ERPNext console
   frappe.has_permission("Purchase Receipt Report", "submit")
   # Should return True
   ```

6. **Recreate the document**:
   - Delete the stuck Purchase Receipt Report
   - Go back to Incoming Check Report
   - Click "Create Purchase Receipt Report" again
   - The new document should have all items and be submittable

**After the Fix**:
- The Purchase Receipt Report should now show a "Submit" button at the top right
- Click Submit to change status from Draft to Submitted
- After submission, the "Create Printing Order" button will appear

### Issue: Submit Button is Disabled

**Possible Causes**:
1. Missing required fields
2. Validation errors
3. Insufficient permissions

**Solutions**:
1. Check for red error messages on the form
2. Ensure all required fields are filled
3. Check if you have submit permission:
   - Go to: Setup > Permissions > Role Permissions Manager
   - Search for "Purchase Receipt Report"
   - Ensure your role has "Submit" permission

### Issue: "Create" Button Doesn't Appear

**Cause**: Document not submitted

**Solution**:
1. Check document status at top of form
2. If it says "Draft", click Submit first
3. After submission, refresh the page if needed
4. "Create" button should appear

### Issue: Printing Order Button Not Showing

**Possible Causes**:
1. Document not submitted (docstatus !== 1)
2. JavaScript not loaded
3. Method not found

**Solutions**:
1. **Verify document is submitted**:
   ```python
   frappe.get_doc("Purchase Receipt Report", "PRR-2026-XXXXX").docstatus
   # Should return 1
   ```

2. **Clear cache**:
   ```bash
   bench --site [site] clear-cache
   bench restart
   ```

3. **Check browser console** for JavaScript errors:
   - Press F12 to open developer tools
   - Check Console tab for errors

4. **Verify method exists**:
   ```python
   from onco.onco.doctype.purchase_receipt_report.purchase_receipt_report import make_printing_order
   # Should not raise ImportError
   ```

### Issue: Data Not Mapping Correctly

**Cause**: Field mapping issue

**Solution**:
1. Check if all fields exist in both doctypes
2. Verify field names match in mapping function
3. Check `make_printing_order()` function in `purchase_receipt_report.py`

---

## Field Mappings

### Purchase Receipt Report → Printing Order

| Purchase Receipt Report | Printing Order |
|------------------------|----------------|
| custom_shipment_ref | shipment_no |
| (current date) | date |
| items[].item_code | items[].item_code |
| items[].item_name | items[].item_name |
| items[].batch_no | items[].batch_no |
| items[].accepted_qty | items[].qty_in_stock |
| items[].expiry_date | items[].expiry_date |

---

## Complete Workflow

```
Incoming Check Report (Submitted)
  ↓ (Click "Create Purchase Receipt Report")
Purchase Receipt Report (Draft)
  ↓ (Review and Submit)
Purchase Receipt Report (Submitted)
  ↓ (Click "Create" > "Printing Order")
Printing Order (Draft)
  ↓ (Save and Submit)
Printing Order (Submitted)
  ↓ (Click "Mark as Completed")
Printing Order (Completed)
  ↓ (Click "Create" > "Authority Good Release")
Authority Good Release (Draft)
  ↓ (Fill details and Submit)
Authority Good Release (Submitted)
  ↓ (Auto creates Stock Entry)
Stock Entry (to Sales Warehouse)
```

---

## Quick Commands

### Check Document Status
```python
# In ERPNext console
doc = frappe.get_doc("Purchase Receipt Report", "PRR-2026-XXXXX")
print(f"Status: {doc.docstatus}")
print(f"0 = Draft, 1 = Submitted, 2 = Cancelled")
```

### Submit Programmatically (if needed)
```python
doc = frappe.get_doc("Purchase Receipt Report", "PRR-2026-XXXXX")
doc.submit()
frappe.db.commit()
```

### Create Printing Order Programmatically
```python
from onco.onco.doctype.purchase_receipt_report.purchase_receipt_report import make_printing_order

po = make_printing_order("PRR-2026-XXXXX")
po.insert()
print(f"Created: {po.name}")
```

---

## Best Practices

1. **Always Review Before Submitting**
   - Check all inspection data is correct
   - Verify quantities match expectations
   - Ensure all required checks are completed

2. **Don't Skip Steps**
   - Submit Purchase Receipt Report first
   - Then create Printing Order
   - Don't try to create downstream documents from Draft

3. **Keep Documents Linked**
   - Ensure Purchase Receipt reference is correct
   - Verify Shipment reference is populated
   - Check all items are mapped correctly

4. **Document Issues**
   - Add remarks for any discrepancies
   - Attach supporting documents
   - Note any deviations from standard process

---

## Summary

✅ Purchase Receipt Report is **submittable**  
✅ Submit button is at top right of form  
✅ After submission, "Create" button appears  
✅ Click "Create" > "Printing Order" to proceed  
✅ Complete workflow: PRR → Printing Order → Authority Good Release  

If you're still having issues, check the troubleshooting section or contact support.
