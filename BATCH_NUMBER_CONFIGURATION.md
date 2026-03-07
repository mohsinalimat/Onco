# Batch Number Configuration for Purchase Invoice

## Problem Statement

When creating a Purchase Invoice from a Purchase Order (originating from Importation Approvals), the batch number field was not visible or mandatory, even though it's a critical piece of data that flows through the entire importation cycle:

**Importation Cycle Flow:**
```
Importation Approvals → Purchase Order → Purchase Invoice → Shipments → Purchase Receipt
```

The batch number must be captured at the Purchase Invoice stage and propagated through the rest of the cycle.

## Root Cause

In ERPNext, the `batch_no` field visibility in Purchase Invoice Item is controlled by:
1. The `use_serial_batch_fields` checkbox must be checked (value = 1)
2. The `update_stock` field in the parent Purchase Invoice must be enabled (value = 1)
3. The field has a `depends_on` condition: `eval:!doc.is_fixed_asset && doc.use_serial_batch_fields === 1 && parent.update_stock === 1`

By default, these fields were not being set when creating Purchase Invoices from Purchase Orders.

## Solution Implemented

### 1. Purchase Invoice Item Customization (`purchase_invoice_item.json`)

Added property setters to:
- **Make `batch_no` visible in list view** (`in_list_view = 1`)
- **Set column width** (`columns = 2`) to ensure it displays properly
- **Make it conditionally mandatory** based on whether the item has batch tracking enabled
- **Set `use_serial_batch_fields` default to 1** to ensure batch fields are always visible

```json
{
  "field_name": "batch_no",
  "property": "in_list_view",
  "value": "1"
},
{
  "field_name": "batch_no",
  "property": "mandatory_depends_on",
  "value": "eval:doc.item_code && frappe.get_doc('Item', doc.item_code).has_batch_no"
},
{
  "field_name": "use_serial_batch_fields",
  "property": "default",
  "value": "1"
}
```

### 2. Purchase Invoice Customization (`purchase_invoice.json`)

Added property setter to:
- **Set `update_stock` default to 1** to enable stock updates by default

```json
{
  "field_name": "update_stock",
  "property": "default",
  "value": "1"
}
```

### 3. Client Script (`purchase_invoice_batch_handling.js`)

Created a client-side script that:
- Automatically checks `update_stock` when a new Purchase Invoice is created
- Sets `use_serial_batch_fields = 1` for all items when `update_stock` is enabled
- Shows an alert when an item requiring a batch number is selected
- Ensures batch fields remain visible when items are added

### 4. Server-Side Hook (`purchase_invoice.py`)

Created Python hooks that:
- Enforce `update_stock = 1` before insert and on validate
- Automatically set `use_serial_batch_fields = 1` for all items
- Validate that batch numbers are provided for items that require them
- Throw an error if a batch-tracked item is missing its batch number

### 5. Hook Registration (`hooks.py`)

Registered the Purchase Invoice hooks:
```python
"Purchase Invoice": {
    "before_insert": "onco.onco.purchase_invoice.before_insert",
    "validate": "onco.onco.purchase_invoice.validate",
    "on_submit": "onco.onco.purchase_invoice.on_submit"
}
```

## How It Works

### When Creating a Purchase Invoice from Purchase Order:

1. **Before Insert**: The `before_insert` hook sets `update_stock = 1` and `use_serial_batch_fields = 1` for all items
2. **On Load**: The client script ensures these values remain set
3. **Item Selection**: When an item is selected, the script checks if it requires a batch number and shows an alert
4. **Validation**: Before saving, the server validates that all batch-tracked items have batch numbers
5. **Display**: The batch number field is now visible in the list view with proper column width

### Batch Number Flow:

```
Purchase Invoice (batch_no entered) 
    ↓
Shipments (batch_no fetched from Purchase Invoice)
    ↓
Purchase Receipt (batch_no fetched from Shipments)
    ↓
Stock Entry (batch_no available for stock movements)
```

## Configuration Requirements

### For Items to Use Batch Numbers:

1. Open the Item master
2. Check the "Has Batch No" checkbox
3. Optionally check "Automatically Create New Batch" if you want ERPNext to auto-generate batch numbers

### For Pharmaceutical Items:

The system already has custom fields for pharmaceutical items:
- `custom_pharmaceutical_item` (checkbox)
- `custom_registered` (checkbox)
- `custom_manufacturing_date` (date)
- `custom_expiry_date` (date)
- `custom_batch_no` (data field on Item master)

These fields work alongside the standard ERPNext batch tracking system.

## Testing the Configuration

1. **Create a Purchase Order** from an Importation Approval
2. **Create a Purchase Invoice** from the Purchase Order
3. **Verify**:
   - `update_stock` is checked
   - Batch number field is visible in the item table
   - When you select an item with batch tracking, you can see and enter the batch number
   - The system prevents saving without a batch number for batch-tracked items

## Troubleshooting

### Batch Number Field Not Visible:
- Check that `update_stock` is enabled (checkbox at top of form)
- Check that the item has "Has Batch No" enabled in Item master
- Verify `use_serial_batch_fields` is checked in the item row (may be hidden)

### Batch Number Not Mandatory:
- Ensure the item has "Has Batch No" enabled
- The mandatory validation only applies when `update_stock = 1`

### Changes Not Taking Effect:
1. Run `bench migrate` to apply the customizations
2. Clear cache: `bench clear-cache`
3. Restart bench: `bench restart`

## Files Modified/Created

1. `Onco/onco/onco/custom/purchase_invoice_item.json` - Added batch field property setters
2. `Onco/onco/onco/custom/purchase_invoice.json` - Added update_stock default
3. `Onco/onco/onco/client scripts/purchase_invoice_batch_handling.js` - Client-side logic
4. `Onco/onco/onco/purchase_invoice.py` - Server-side validation hooks
5. `onco/onco/hooks.py` - Registered Purchase Invoice hooks

## References

- [ERPNext Batch Documentation](https://docs.erpnext.com/docs/v12/user/manual/en/stock/batch)
- [ERPNext Forum: Batch No Field Not Showing](https://discuss.frappe.io/t/solved-purchase-recieve-item-not-showing-batch-no-field-despite-customization/36374)
