# Installation Guide: Batch Number Configuration

## Quick Installation Steps

Follow these steps to apply the batch number configuration to your ERPNext instance:

### 1. Apply the Changes

```bash
# Navigate to your bench directory
cd /path/to/your/bench

# Run migrations to apply customizations
bench --site your-site-name migrate

# Clear cache
bench --site your-site-name clear-cache

# Restart bench
bench restart
```

### 2. Verify Installation

1. **Open Purchase Invoice**
   - Go to: Buying → Purchase Invoice → New
   - Check that "Update Stock" is checked by default

2. **Add an Item with Batch Tracking**
   - Select an item that has "Has Batch No" enabled
   - Verify the "Batch No" field is visible in the item row
   - Try to save without entering a batch number - it should show an error

3. **Create from Purchase Order**
   - Create a Purchase Invoice from an existing Purchase Order
   - Verify batch number fields are visible and functional

### 3. Enable Batch Tracking on Items

For items that need batch tracking:

```sql
-- Check which items have batch tracking enabled
SELECT item_code, item_name, has_batch_no 
FROM `tabItem` 
WHERE has_batch_no = 1;
```

Or via UI:
1. Go to: Stock → Item → [Select Item]
2. Check "Has Batch No"
3. Optionally check "Automatically Create New Batch"
4. Save

### 4. Bulk Enable Batch Tracking (Optional)

If you need to enable batch tracking for multiple pharmaceutical items:

```python
# Run this in bench console: bench --site your-site-name console

import frappe

# Enable batch tracking for all pharmaceutical items
items = frappe.get_all('Item', 
    filters={'custom_pharmaceutical_item': 1},
    fields=['name']
)

for item in items:
    doc = frappe.get_doc('Item', item.name)
    doc.has_batch_no = 1
    doc.create_new_batch = 0  # Set to 1 for auto-creation
    doc.save()
    print(f"Enabled batch tracking for {item.name}")

frappe.db.commit()
```

## Rollback (If Needed)

If you need to revert the changes:

### 1. Remove Property Setters

```python
# Run in bench console
import frappe

# Remove Purchase Invoice Item property setters
frappe.db.sql("""
    DELETE FROM `tabProperty Setter` 
    WHERE doc_type = 'Purchase Invoice Item' 
    AND field_name IN ('batch_no', 'use_serial_batch_fields')
    AND modified >= '2026-03-07'
""")

# Remove Purchase Invoice property setter
frappe.db.sql("""
    DELETE FROM `tabProperty Setter` 
    WHERE doc_type = 'Purchase Invoice' 
    AND field_name = 'update_stock'
    AND modified >= '2026-03-07'
""")

frappe.db.commit()
```

### 2. Remove Files

```bash
# Remove created files
rm Onco/onco/onco/client\ scripts/purchase_invoice_batch_handling.js
rm Onco/onco/onco/purchase_invoice.py
```

### 3. Update hooks.py

Remove the Purchase Invoice section from `doc_events` in `onco/onco/hooks.py`

### 4. Apply Changes

```bash
bench --site your-site-name migrate
bench --site your-site-name clear-cache
bench restart
```

## Troubleshooting

### Issue: Changes not appearing after migration

**Solution:**
```bash
# Force reload customizations
bench --site your-site-name reload-doc onco custom "Purchase Invoice Item"
bench --site your-site-name reload-doc onco custom "Purchase Invoice"
bench --site your-site-name clear-cache
bench restart
```

### Issue: JavaScript not loading

**Solution:**
```bash
# Build assets
bench build --app onco

# Or clear cache and restart
bench --site your-site-name clear-cache
bench restart
```

### Issue: Batch field still not visible

**Solution:**
1. Check that the item has "Has Batch No" enabled
2. Verify "Update Stock" is checked in Purchase Invoice
3. Open browser console (F12) and check for JavaScript errors
4. Try in incognito/private mode to rule out browser cache

### Issue: Python hooks not executing

**Solution:**
```bash
# Verify hooks are registered
bench --site your-site-name console

import frappe
from onco.onco import hooks
print(hooks.doc_events)

# Should show Purchase Invoice hooks
```

## Post-Installation Checklist

- [ ] Migrations completed successfully
- [ ] Cache cleared
- [ ] Bench restarted
- [ ] Batch number field visible in Purchase Invoice Item
- [ ] Update Stock checked by default
- [ ] Validation working (prevents saving without batch for batch-tracked items)
- [ ] Client script alerts working
- [ ] Items have "Has Batch No" enabled as needed
- [ ] Test Purchase Invoice creation from Purchase Order
- [ ] Verify batch number flows to Shipments and Purchase Receipt

## Support

For issues or questions:
1. Check the `BATCH_NUMBER_CONFIGURATION.md` file for detailed documentation
2. Review ERPNext logs: `bench --site your-site-name logs`
3. Check browser console for JavaScript errors
4. Verify customizations in: Setup → Customize Form → Purchase Invoice Item

## Next Steps

After installation:
1. Train users on entering batch numbers in Purchase Invoices
2. Update any existing Purchase Invoices if needed
3. Monitor the importation cycle to ensure batch numbers flow correctly
4. Consider adding batch number to print formats if needed
