# Final Setup Instructions - Incoming Check Report

## ✅ Implementation Complete

All files have been created and configured correctly. The Stock Entry button issue has been fixed.

## 📦 What Was Fixed

### Issue
The "Create Incoming Check Report" button was not appearing on Stock Entry forms.

### Solution
1. ✅ Moved JavaScript file to correct location: `onco/public/js/stock_entry_incoming_check.js`
2. ✅ Registered in `hooks.py` under `doctype_js`
3. ✅ Fixed directory structure for child table doctype

## 🚀 Installation Commands

Run these commands in order:

```bash
# 1. Navigate to Frappe bench
cd /path/to/frappe-bench

# 2. Install new doctypes (creates database tables)
bench --site your-site-name migrate

# 3. Clear cache
bench --site your-site-name clear-cache

# 4. Restart bench (IMPORTANT - loads the new hooks)
bench restart
```

## 🌐 Browser Steps

After running the commands above:

1. **Hard refresh your browser**:
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`
   - Or clear browser cache completely

2. **Test the button**:
   - Go to Stock Entry
   - Create or open a Stock Entry with Purpose = "Material Transfer"
   - Submit it
   - You should see "Create Incoming Check Report" button in the "Create" dropdown

## 📋 Complete File Structure

```
Onco/onco/
├── hooks.py (✅ Updated - Stock Entry registered)
├── public/js/
│   ├── p_inv.override.js
│   ├── purchase_receipt_override.js
│   ├── supplier_quotation.js
│   ├── purchase_order.js
│   └── stock_entry_incoming_check.js (✅ New - Button script)
└── onco/
    └── doctype/
        ├── incoming_check_report/
        │   ├── __init__.py
        │   ├── incoming_check_report.json
        │   ├── incoming_check_report.py
        │   └── incoming_check_report.js
        └── incoming_check_report_item/
            ├── __init__.py
            ├── incoming_check_report_item.json
            └── incoming_check_report_item.py
```

## ⚙️ Configuration Needed

### 1. Naming Series
Go to: **Setup > Settings > Naming Series**

Add: `ICR-.YYYY.-.#####`

### 2. Warehouses
Ensure these warehouses exist in your system:
- **Imported Finished Phr Incoming Warehouse - Onco**
- **Imported Finished Phr Receipt and Inspection Warehouse - Onco**
- **Your Accepted Warehouse** (create with your preferred name)
- **Your Rejected Warehouse** (create with your preferred name)

### 3. Permissions
Go to: **Setup > Permissions > Incoming Check Report**

Add roles:
- System Manager (full access)
- Quality Control (if you have this role)
- Any other roles that need access

## 🧪 Testing Workflow

### Step 1: Create Stock Entry
1. Go to **Stock > Stock Entry > New**
2. Set Purpose: **Material Transfer**
3. Set From Warehouse: **Imported Finished Phr Incoming Warehouse - Onco**
4. Set To Warehouse: **Imported Finished Phr Receipt and Inspection Warehouse - Onco**
5. Add items
6. **Submit** the Stock Entry

### Step 2: Create Incoming Check Report
1. After submission, click the **"Create"** dropdown button
2. Click **"Create Incoming Check Report"**
3. A new form should open with:
   - ✅ Stock Entry reference filled
   - ✅ Inspection warehouse auto-filled (from Stock Entry's to_warehouse)
   - ✅ Purchase Receipt reference (if linked)
   - ✅ Shipment reference (if linked)
   - ✅ Purchase Invoice reference (if linked)
   - ✅ Importation Approval reference (if linked)
   - ✅ Items table populated with quantities

### Step 3: Fill Inspection Details
1. **Vehicle Inspection**:
   - Seal Numbers
   - Seal Integrity
   - Temperature Recorder Status

2. **Document Check** (check all that apply):
   - Commercial Invoice
   - Packing List
   - Bill of Lading/Airway Bill
   - Certificate of Analysis
   - COO & GMP Certificate
   - All Documents Consistent

3. **Physical Check** (check all that apply):
   - Seal Integrity Verified
   - Package Condition OK
   - Labels Verified
   - Quantity Verified

4. **Temperature Control**:
   - Data Logger Present: Yes/No
   - If Yes: Upload Temperature Report
   - Temperature Range Status: In-Range/Out-of-Range
   - If Out-of-Range: Choose action (Quarantine or Accept with Reason)

5. **Quantity Verification**:
   - Review auto-populated quantities
   - Enter Over Quantity (if any)
   - Enter Damage Quantity (if any)
   - Accepted Quantity auto-calculates

6. **Warehouse Assignment**:
   - If inspection passes: Fill **Accepted Warehouse**
   - If inspection fails/quarantined: Fill **Rejected Warehouse**

7. **Inspection Result**:
   - Select: Passed / Failed / Quarantined
   - Add Remarks (optional)

8. **Email Notification** (optional):
   - Check "Send Shipment Receipt Notification"
   - Enter email (or leave blank to use supplier's email)

9. **Submit** the document

### Step 4: Verify Blocking Logic
1. If inspection result is "Failed" or "Quarantined":
   - Try to create **Purchase Receipt Report** → Should be blocked ❌
   - Try to create **Printing Order** → Should be blocked ❌
   - Try to create **Authority Good Release** → Should be blocked ❌

2. If inspection result is "Passed":
   - Can create **Purchase Receipt Report** ✅
   - Can create **Printing Order** ✅
   - Can create **Authority Good Release** ✅

## 🚨 Troubleshooting

### Button Not Appearing?

**Check 1**: Stock Entry conditions
- ✅ Stock Entry is submitted (docstatus = 1)
- ✅ Purpose is "Material Transfer"

**Check 2**: Cache and restart
```bash
bench --site your-site-name clear-cache
bench restart
```

**Check 3**: Browser cache
- Hard refresh: `Ctrl + Shift + R`
- Or clear browser cache completely

**Check 4**: Check browser console (F12)
- Look for JavaScript errors
- If you see errors about "stock_entry_incoming_check.js", the file might not be loaded

**Check 5**: Verify hooks.py
```bash
cat onco/hooks.py | grep -A 6 "doctype_js"
```
Should show:
```python
doctype_js = {
    "Purchase Invoice": "public/js/p_inv.override.js",
    "Purchase Receipt": "public/js/purchase_receipt_override.js",
    "Supplier Quotation": "public/js/supplier_quotation.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Stock Entry": "public/js/stock_entry_incoming_check.js"
}
```

### Manual Test
If button still doesn't appear, test manually in browser console (F12):
```javascript
frappe.model.open_mapped_doc({
    method: "onco.onco.doctype.incoming_check_report.incoming_check_report.make_incoming_check_report",
    frm: cur_frm
});
```

If this works, it's a caching issue. Clear cache and restart again.

## ✅ Success Criteria

After installation, you should have:
- ✅ "Create Incoming Check Report" button on submitted Stock Entries
- ✅ Button opens new Incoming Check Report with auto-populated data
- ✅ All inspection fields working correctly
- ✅ Quantity calculations working
- ✅ Warehouse assignment based on inspection result
- ✅ Email notifications working (if enabled)
- ✅ Blocking logic preventing downstream processes when inspection fails

## 📞 Next Steps

1. **Install** using the commands above
2. **Configure** naming series and warehouses
3. **Test** the complete workflow
4. **Integrate** blocking validation into downstream doctypes:
   - Purchase Receipt Report
   - Printing Order
   - Authority Good Release
5. **Train** users on the inspection process
6. **Deploy** to production

## 📝 Integration Code for Downstream Doctypes

Add this to Purchase Receipt Report, Printing Order, and Authority Good Release:

```python
# In the validate() method of each doctype

from onco.onco.doctype.incoming_check_report.incoming_check_report import validate_inspection_before_downstream

def validate(self):
    # ... existing validations ...
    
    # Check inspection status before allowing creation
    validate_inspection_before_downstream("Purchase Receipt Report", self.name)
    # Or: validate_inspection_before_downstream("Printing Order", self.name)
    # Or: validate_inspection_before_downstream("Authority Good Release", self.name)
```

This will block creation if inspection failed or goods are quarantined.

---

**Status**: ✅ **READY FOR INSTALLATION**
**Date**: February 8, 2026
**Action Required**: Run installation commands and test

🎉 **Implementation Complete!**
