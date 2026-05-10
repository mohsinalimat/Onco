# Quick Fix - Landed Cost Automation

## The Problem
The client script was looking for the wrong table names. In ERPNext v16, Landed Cost Voucher uses:
- **"Vouchers"** table (not "Purchase Receipts")
- **"Applicable Charges"** table (not "Taxes")
- **Purchase Invoices** (not Purchase Receipts)

## Apply the Fix

```bash
# 1. Clear cache
bench --site [your-site] clear-cache

# 2. Restart bench (if running)
# Press Ctrl+C to stop, then:
bench start
```

## Test Again

### Step 1: Create Foreign Supplier Purchase Invoice
1. **Buying → Purchase Invoice → New**
2. Supplier: Foreign supplier
3. **Shipment ID**: Select your shipment (e.g., SHIP-IMP-AWB-12345)
4. Add items
5. **Submit**

### Step 2: Create Vendor Purchase Invoices
1. **Buying → Purchase Invoice → New**
2. Supplier: Customs Broker
3. **Shipment ID (Vendor Services)**: SHIP-IMP-AWB-12345 ← Same shipment!
4. Add expense (Customs fee)
5. **Submit**

Repeat for other vendors (freight, storage, etc.)

### Step 3: Create Landed Cost Voucher
1. **Stock → Landed Cost Voucher → New**
2. In "Vouchers" table, add row:
   - **Receipt Document Type**: Purchase Invoice
   - **Receipt Document**: Select the foreign supplier invoice from Step 1
3. **Watch**: Shipment ID should auto-fill
4. **Check**: "Auto-fetch Vendor Invoices" checkbox
5. **Watch**: "Landed Cost" table should populate with vendor invoices
6. **Submit**

## What Should Happen

✅ Shipment ID auto-detects from Purchase Invoice  
✅ Vendor invoices auto-populate in "Landed Cost" section  
✅ Expense accounts come from vendor invoices  
✅ Costs distribute to items  

## If Still Not Working

Check browser console (F12):
- Look for JavaScript errors
- Check if the script is loading

Check if Purchase Invoice has Shipment ID:
```python
# In bench console
frappe.db.get_value('Purchase Invoice', 'PHR-LOC-PINV-2026-00008', ['custom_shipments', 'custom_shipment_id_dimension'])
```

Check if vendor invoices exist:
```python
frappe.db.sql("""
    SELECT name, supplier_name, custom_shipment_id_dimension 
    FROM `tabPurchase Invoice` 
    WHERE custom_shipment_id_dimension IS NOT NULL
""", as_dict=1)
```
