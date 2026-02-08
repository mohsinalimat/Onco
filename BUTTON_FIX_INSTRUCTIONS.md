# Stock Entry Button Fix - Instructions

## Issue
The "Create Incoming Check Report" button was not appearing on Stock Entry forms.

## Root Cause
The custom JavaScript file was not properly registered in the hooks.py file and was in the wrong directory.

## Fix Applied

### 1. Moved JavaScript File
**From**: `Onco/onco/onco/client scripts/stock_entry_incoming_check.js`
**To**: `Onco/onco/public/js/stock_entry_incoming_check.js`

### 2. Updated hooks.py
Added Stock Entry to the `doctype_js` dictionary:
```python
doctype_js = {
    "Purchase Invoice": "public/js/p_inv.override.js",
    "Purchase Receipt": "public/js/purchase_receipt_override.js",
    "Supplier Quotation": "public/js/supplier_quotation.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Stock Entry": "public/js/stock_entry_incoming_check.js"  # ← Added this line
}
```

## Installation Steps

### Step 1: Clear Cache
```bash
cd /path/to/frappe-bench
bench --site your-site-name clear-cache
```

### Step 2: Restart Bench
```bash
bench restart
```

### Step 3: Hard Refresh Browser
- Press `Ctrl + Shift + R` (Windows/Linux)
- Or `Cmd + Shift + R` (Mac)
- Or clear browser cache completely

### Step 4: Test the Button

1. **Go to Stock Entry**
   - Navigate to an existing Stock Entry or create a new one
   - Purpose must be "Material Transfer"
   - Submit the Stock Entry

2. **Verify Button Appears**
   - After submission, you should see a "Create" dropdown button
   - Click it and you should see "Create Incoming Check Report"

3. **Click the Button**
   - Click "Create Incoming Check Report"
   - A new Incoming Check Report form should open
   - All data should be auto-populated from the Stock Entry

## Troubleshooting

### Button Still Not Appearing?

#### Check 1: Verify File Exists
```bash
ls -la onco/public/js/stock_entry_incoming_check.js
```
Should show the file exists.

#### Check 2: Verify hooks.py Updated
```bash
cat onco/hooks.py | grep -A 5 "doctype_js"
```
Should show Stock Entry in the list.

#### Check 3: Check Browser Console
1. Open Stock Entry form
2. Press F12 to open Developer Tools
3. Go to Console tab
4. Look for any JavaScript errors
5. If you see errors related to "stock_entry_incoming_check.js", the file path might be wrong

#### Check 4: Verify Bench Restarted
```bash
# Check if bench is running
ps aux | grep bench

# If needed, restart again
bench restart
```

#### Check 5: Check Stock Entry Conditions
The button only appears when:
- ✅ Stock Entry is **submitted** (docstatus = 1)
- ✅ Purpose is **"Material Transfer"**

If either condition is not met, the button won't appear.

### Alternative: Manual Button Test

If the button still doesn't appear, you can test the functionality manually:

1. Open Stock Entry form
2. Open Browser Console (F12)
3. Paste this code and press Enter:

```javascript
frappe.model.open_mapped_doc({
    method: "onco.onco.doctype.incoming_check_report.incoming_check_report.make_incoming_check_report",
    frm: cur_frm
});
```

If this works, the backend is fine and it's just a frontend caching issue.

## Expected Behavior

### When Button Appears
- Stock Entry is submitted
- Purpose = "Material Transfer"
- No Incoming Check Report exists for this Stock Entry yet

### Button Text
- **"Create Incoming Check Report"** - If no report exists
- **"View Incoming Check Report"** - If report already exists

### When Clicked
1. Opens new Incoming Check Report form
2. Auto-populates:
   - Stock Entry reference
   - Inspection warehouse (from Stock Entry's to_warehouse)
   - Purchase Receipt reference
   - Shipment reference
   - Purchase Invoice reference
   - Importation Approval reference
   - Items table with all quantities

## Verification Checklist

After applying the fix:
- [ ] File moved to `onco/public/js/stock_entry_incoming_check.js`
- [ ] hooks.py updated with Stock Entry entry
- [ ] Cache cleared
- [ ] Bench restarted
- [ ] Browser hard refreshed
- [ ] Stock Entry submitted with Purpose = "Material Transfer"
- [ ] Button appears in "Create" dropdown
- [ ] Clicking button opens Incoming Check Report
- [ ] Data auto-populates correctly

## Notes

- The button uses ERPNext's standard `frappe.model.open_mapped_doc()` function
- The mapping is handled by the Python method `make_incoming_check_report()` in the Incoming Check Report controller
- The button checks if a report already exists to avoid duplicates
- If a report exists, it shows a "View" button instead

---

**Status**: ✅ Fixed
**Date**: February 8, 2026
**Action Required**: Clear cache and restart bench
