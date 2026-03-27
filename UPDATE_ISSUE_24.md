# Update: Issue #24 - Hide update_stock Field

## Date: March 27, 2026
## Status: ✅ UPDATED - Field Now Hidden

---

## Change Summary

**Original Fix**: Removed default value property setter
**Updated Fix**: Added property setter to completely hide the field

---

## Why This Change?

### Original Request
"Remove the `update_stock` field from the Purchase Invoice doctype because it updates the stock ledger."

### Initial Implementation
- Removed property setter that set `update_stock.default = 1`
- Result: Field was visible but unchecked by default

### User Feedback
"The update_stock function is still showing in the purchase invoice doctype so we need to make it hidden"

### Final Implementation
- Added property setter to hide the field completely
- Result: Field is now invisible to all users

---

## Technical Details

### Property Setter Added

```json
{
  "_assign": null,
  "_comments": null,
  "_liked_by": null,
  "_user_tags": null,
  "creation": "2026-03-27 12:00:00.000000",
  "default_value": null,
  "doc_type": "Purchase Invoice",
  "docstatus": 0,
  "doctype_or_field": "DocField",
  "field_name": "update_stock",
  "idx": 0,
  "is_system_generated": 0,
  "modified": "2026-03-27 12:00:00.000000",
  "modified_by": "Administrator",
  "module": null,
  "name": "Purchase Invoice-update_stock-hidden",
  "owner": "Administrator",
  "parent": null,
  "parentfield": null,
  "parenttype": null,
  "property": "hidden",
  "property_type": "Check",
  "row_name": null,
  "value": "1"
}
```

### File Modified
`Onco/onco/onco/custom/purchase_invoice.json`

---

## Impact

### Before This Update
- ❌ Field visible in Purchase Invoice form
- ❌ Users could accidentally check it
- ❌ Could cause unintended stock updates

### After This Update
- ✅ Field completely hidden from form
- ✅ Users cannot access it
- ✅ Stock updates only through Purchase Receipt
- ✅ Prevents accidental stock ledger entries

---

## Business Logic

### Correct Workflow for Stock Updates

**Purchase Invoice** → Does NOT update stock
- Only records the financial transaction
- Creates accounting entries
- No stock movement

**Purchase Receipt** → Updates stock
- Records physical receipt of goods
- Updates stock ledger
- Moves items to warehouse

### Why Hide update_stock?

1. **Prevents Confusion**: Users might think they should check it
2. **Enforces Workflow**: Stock updates should go through Purchase Receipt
3. **Data Integrity**: Separates financial and inventory transactions
4. **Best Practice**: ERPNext recommends using Purchase Receipt for stock updates

---

## Testing Instructions

### Test 1: Field Hidden
1. Open any Purchase Invoice (new or existing)
2. Look through all sections of the form
3. **Verify**: "Update Stock" checkbox is NOT visible anywhere

### Test 2: Stock Not Updated
1. Create new Purchase Invoice
2. Add items and submit
3. Check Stock Ledger Entry
4. **Verify**: No stock ledger entries created from Purchase Invoice

### Test 3: Purchase Receipt Still Works
1. Create Purchase Receipt
2. Add items and submit
3. Check Stock Ledger Entry
4. **Verify**: Stock ledger entries created correctly

---

## Alternative Approaches (Not Implemented)

### Option 1: Role-Based Visibility
Make field visible only to specific roles (e.g., Stock Manager)
```json
{
  "property": "hidden",
  "value": "eval:!frappe.user.has_role('Stock Manager')"
}
```

### Option 2: Read-Only
Make field visible but read-only
```json
{
  "property": "read_only",
  "value": "1"
}
```

### Option 3: Depends On
Show field only in specific conditions
```json
{
  "property": "depends_on",
  "value": "eval:doc.custom_allow_stock_update==1"
}
```

**Why We Chose Complete Hiding**: Simplest solution that prevents all confusion and accidental usage.

---

## Rollback Instructions

If you need to show the field again:

### Method 1: Remove Property Setter (via UI)
1. Go to: Customize Form → Purchase Invoice
2. Find "update_stock" field
3. Remove the "hidden" property
4. Save

### Method 2: Modify JSON File
Edit `purchase_invoice.json` and remove this property setter:
```json
{
  "name": "Purchase Invoice-update_stock-hidden",
  "property": "hidden",
  "value": "1"
}
```

### Method 3: Database Query
```sql
DELETE FROM `tabProperty Setter` 
WHERE name = 'Purchase Invoice-update_stock-hidden';
```

Then run:
```bash
bench --site your-site-name clear-cache
bench restart
```

---

## Related Documentation

- ERPNext Purchase Invoice: https://docs.erpnext.com/docs/v15/user/manual/en/accounts/purchase-invoice
- ERPNext Purchase Receipt: https://docs.erpnext.com/docs/v15/user/manual/en/stock/purchase-receipt
- Stock Ledger: https://docs.erpnext.com/docs/v15/user/manual/en/stock/stock-ledger

---

## Deployment

This change will take effect after:

```bash
bench --site your-site-name migrate
bench --site your-site-name clear-cache
bench restart
```

**No data migration needed** - this is a UI-only change.

---

## User Communication

### Message to Users

"The 'Update Stock' checkbox has been removed from Purchase Invoice forms. This change ensures that stock updates are only made through the proper Purchase Receipt workflow, preventing accidental stock ledger entries.

**What this means for you:**
- Purchase Invoices will continue to work normally for recording supplier bills
- Stock updates will only happen when you create and submit Purchase Receipts
- This improves data integrity and follows ERPNext best practices

**No action required** - your existing Purchase Invoices are not affected."

---

## Conclusion

The `update_stock` field is now completely hidden from Purchase Invoice forms, preventing any confusion or accidental stock updates. Stock movements will only occur through the proper Purchase Receipt workflow.

✅ **Change Complete and Ready for Deployment**

