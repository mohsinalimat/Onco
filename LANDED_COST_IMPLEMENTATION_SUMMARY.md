# Landed Cost Automation - Implementation Summary

## What Was Built

Automatic landed cost distribution for imported pharma items using Shipment ID as the linking mechanism.

## Files Created/Modified

### Core Implementation (Required)
1. **`onco/onco/custom/purchase_invoice.json`** - Modified
   - Updated `custom_shipments` label to "Shipment ID"
   - Added `custom_shipment_id_dimension` field for vendor invoices

2. **`onco/onco/custom/landed_cost_voucher.json`** - New
   - Added `custom_shipment_id` (auto-detected)
   - Added `custom_auto_fetch_vendor_invoices` checkbox

3. **`onco/onco/custom_scripts/landed_cost_voucher.py`** - New
   - `get_vendor_invoices_for_shipment()` - Fetches vendor invoices by Shipment ID
   - `get_primary_expense_account()` - Extracts expense account from invoice
   - `validate_landed_cost_voucher()` - Validates Shipment ID consistency
   - `before_submit_landed_cost_voucher()` - Logs to Shipment document

4. **`onco/onco/client_scripts/landed_cost_voucher_auto_fetch.js`** - New
   - Auto-detects Shipment ID from Purchase Receipt
   - Auto-fetches vendor invoices when checkbox enabled
   - Populates Taxes and Charges table
   - Manual "Fetch Vendor Invoices" button

5. **`onco/hooks.py`** - Modified
   - Registered client script for Landed Cost Voucher
   - Added document event hooks for validation

### Optional Files
- `install_landed_cost_dimension.py` - Sets up accounting dimension (optional)
- `test_landed_cost_automation.py` - Test suite
- `TESTING_LANDED_COST.md` - Testing guide
- `LANDED_COST_AUTOMATION_GUIDE.md` - User documentation

## Installation

```bash
# 1. Migrate to install custom fields
bench --site [your-site] migrate

# 2. Clear cache
bench --site [your-site] clear-cache

# 3. (Optional) Setup accounting dimension
bench --site [your-site] execute onco.onco.install_landed_cost_dimension.run_installation

# 4. Reload browser
```

## How It Works

### Step 1: Foreign Supplier Invoice
- Create Purchase Invoice for imported items
- Set **Shipment ID** field
- Submit

### Step 2: Vendor Service Invoices
- Create Purchase Invoices for vendors (customs, freight, storage)
- Set **Shipment ID (Vendor Services)** field ← Links to shipment
- Submit each invoice

### Step 3: Landed Cost Voucher
- Create Purchase Receipt from Shipment
- Create Landed Cost Voucher
- Select Purchase Receipt → Shipment ID auto-detects
- Enable **"Auto-fetch Vendor Invoices"** checkbox
- System automatically:
  - Finds all vendor invoices with same Shipment ID
  - Populates Taxes and Charges table
  - Uses correct expense accounts
  - Distributes costs to items

## Key Fields

| DocType | Field | Purpose |
|---------|-------|---------|
| Purchase Invoice | `custom_shipments` | Links foreign supplier invoice to Shipment |
| Purchase Invoice | `custom_shipment_id_dimension` | Links vendor invoice to Shipment (for landed cost) |
| Landed Cost Voucher | `custom_shipment_id` | Auto-detected Shipment (read-only) |
| Landed Cost Voucher | `custom_auto_fetch_vendor_invoices` | Enable auto-fetch |

## Database Query Logic

The auto-fetch uses this query:

```sql
SELECT 
    pi.name,
    pi.supplier_name,
    pi.grand_total,
    pi.currency
FROM 
    `tabPurchase Invoice` pi
WHERE 
    pi.custom_shipment_id_dimension = 'SHIP-IMP-AWB-12345'
    AND pi.docstatus = 1
    AND pi.company = 'Your Company'
```

## Frappe v16 Compatibility

✅ Uses modern Query Builder syntax  
✅ Standard Custom Fields API  
✅ Client-side form events  
✅ Whitelisted server methods  
✅ Document hooks (validate, before_submit)  

## Testing

Follow: **`TESTING_LANDED_COST.md`**

Quick test:
1. Create foreign supplier invoice with Shipment ID
2. Create 2-3 vendor invoices with same Shipment ID (Vendor Services field)
3. Create Purchase Receipt from Shipment
4. Create Landed Cost Voucher, select Purchase Receipt
5. Enable "Auto-fetch Vendor Invoices"
6. Verify vendor invoices populate automatically

## Troubleshooting

### Auto-fetch doesn't work
- Check vendor invoices have `custom_shipment_id_dimension` set
- Check vendor invoices are submitted (docstatus = 1)
- Check Purchase Receipt has `custom_shipment_ref` or `shipment` field

### Fields don't appear
```bash
bench --site [site] migrate
bench --site [site] clear-cache
# Reload browser (Ctrl+Shift+R)
```

### Wrong expense account
- System picks account with highest amount from vendor invoice
- Manually edit in Landed Cost Voucher before submitting

## Support

Check logs:
```bash
bench --site [site] console
>>> frappe.get_traceback()
```

Check if fields exist:
```python
frappe.db.exists("Custom Field", "Purchase Invoice-custom_shipment_id_dimension")
frappe.db.exists("Custom Field", "Landed Cost Voucher-custom_shipment_id")
```

## Version Info

- **Created**: May 10, 2026
- **Frappe Version**: v16+
- **ERPNext Version**: v16+
- **App**: Onco

---

**Status**: ✅ Ready for Testing
