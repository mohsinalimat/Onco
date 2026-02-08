# Quick Setup Guide - Incoming Check Report Fix

## What Was Fixed

✅ Item names now fetch from Item master  
✅ Shipment numbers now fetch from Purchase Receipt → Shipments  
✅ Invoice numbers now fetch from Purchase Receipt → Purchase Invoice  
✅ Shortage quantities now calculate when received < invoiced  

## Installation (3 Commands)

```bash
# 1. Run migration to add custom field
bench --site your-site-name migrate

# 2. Clear cache
bench --site your-site-name clear-cache

# 3. Restart
bench restart
```

## Important: Link Stock Entry to Purchase Receipt

The fix adds a new field `custom_purchase_receipt` to Stock Entry. You need to populate this field for the data fetching to work.

### For New Stock Entries
When creating Stock Entry from Purchase Receipt, the field should auto-populate (you may need to add custom code).

### For Existing Stock Entries
You need to manually set the Purchase Receipt field:

1. Open Stock Entry
2. Find "Purchase Receipt" field
3. Select the correct Purchase Receipt
4. Save

## Testing

1. Open a Stock Entry with `custom_purchase_receipt` filled
2. Click "Create" → "Create Incoming Check Report"
3. Verify all fields populate:
   - Item Name ✓
   - Shipment No ✓
   - Invoice No ✓
   - Shortage Quantity ✓ (if received < invoiced)

## Files Changed

- `Onco/onco/onco/custom/stock_entry.json` - Added custom field
- `Onco/onco/onco/doctype/incoming_check_report/incoming_check_report.py` - Fixed data fetching
- `Onco/onco/onco/doctype/incoming_check_report/incoming_check_report.json` - Updated field mapping
- `Onco/onco/onco/doctype/incoming_check_report_item/incoming_check_report_item.json` - Added shortage field

## Need Help?

See `INCOMING_CHECK_REPORT_FINAL_FIX.md` for detailed documentation.
