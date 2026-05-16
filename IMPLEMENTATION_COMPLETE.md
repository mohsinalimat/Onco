# Tender Price Deviation Implementation - Complete

## Summary

Successfully refactored the Tender Price Deviation system to align with requirements from `Tender.html`. The system now uses **Sales Orders** (not Sales Invoices) for the approval workflow.

## Changes Made

### 1. Schema Updates

#### Tender Price Deviation (Approvals Table)
**File**: `Onco/onco/onco/doctype/tender_price_deviation/tender_price_deviation.json`

**Added Fields**:
- `sales_order_no` - Link to Sales Order
- `order_qty` - Order quantities (read-only, fetched from Sales Order)
- `approved_qty` - Approved quantities (manager enters)
- `approved_by` - User who approved
- `approved_date` - Date of approval
- `cause_of_deviation` - Reason for deviation

**Removed Fields**:
- `deviation_percent` - Not needed

#### Tender Price Deviation Details (History Table)
**File**: `Onco/onco/onco/doctype/tender_price_deviation_details/tender_price_deviation_details.json`

**Changed Fields**:
- `invoice_no` → `sales_order_no` - Now links to Sales Order instead of Sales Invoice

### 2. Backend Logic

#### Removed from tenders.py
- `calculate_price_deviations()` - No longer auto-populates on tender save
- `populate_tender_price_deviation_details()` - No longer uses tender items
- `get_deviation_summary()` - Obsolete
- `can_create_sales_invoice()` - Obsolete
- `update_deviation_details()` - Obsolete
- `check_sales_invoice_deviations()` - Obsolete

#### Created tender_validation.py
**File**: `Onco/onco/onco/tender_validation.py`

**New Functions**:
1. `validate_sales_order_tender_price(doc, method)` - Main validation entry point
2. `create_approval_requests(sales_order_doc, tender_doc, loss_making_items)` - Creates approval requests on Sales Order save
3. `validate_approvals(sales_order_doc, tender_doc, loss_making_items)` - Validates approvals on Sales Order submit
4. `log_deviation_history(doc, method)` - Logs to history table on Sales Order submit

### 3. Hooks Registration

**File**: `Onco/onco/hooks.py`

**Changed**:
```python
# OLD
"Sales Invoice": {
    "validate": "onco.onco.tender_validation.validate_sales_invoice_tender_price"
}

# NEW
"Sales Order": {
    "validate": "onco.onco.tender_validation.validate_sales_order_tender_price",
    "on_submit": [
        "onco.onco.tender_validation.validate_sales_order_tender_price",
        "onco.onco.tender_validation.log_deviation_history"
    ]
}
```

### 4. Tests Cleanup

**File**: `Onco/onco/onco/doctype/tenders/test_tenders.py`

**Removed obsolete tests**:
- `test_price_deviation_calculation()`
- `test_no_deviation_when_price_above_cost()`
- `test_deviation_summary()`
- `test_can_create_sales_invoice_with_unapproved_deviations()`
- `test_can_create_sales_invoice_with_approved_deviations()`

## New Workflow

### Step 1: Sales Person Creates Sales Order
- User creates Sales Order with tender items
- Links to Tender using `custom_tender` field
- Saves the Sales Order (draft)

### Step 2: System Detects Loss-Making Items
- On save, system checks if `tender_price < item_cost`
- If yes, creates approval request in Tender Price Deviation table
- Shows message: "Approval request created in Tender XXX"

### Step 3: Manager Approves in Tender
- Manager opens the Tender
- Reviews Tender Price Deviation table
- Fills in:
  - Approved Quantities
  - Status → "Approved"
  - Approved By
  - Approved Date
  - Cause of Deviation
- Saves Tender

### Step 4: Sales Person Submits Sales Order
- User tries to submit Sales Order
- System validates:
  - Status must be "Approved"
  - Approved Qty must be set
  - Order Qty ≤ Approved Qty
  - All approval fields filled
- If valid, allows submission

### Step 5: System Logs History
- On Sales Order submit, system automatically:
  - Creates record in Tender Price Deviation Details
  - Logs actual quantities, losses, approver
  - Permanent audit trail

## Key Features

✅ **Sales Order-based approval** - Approvals happen before order confirmation
✅ **Per-order granularity** - Each Sales Order gets its own approval
✅ **Quantity control** - Manager can approve partial quantities
✅ **Complete audit trail** - Who approved what, when, and why
✅ **Accurate history** - Only actual submitted Sales Orders logged
✅ **Automatic workflow** - No manual checkboxes needed

## Field Mapping

| Requirement | ERPNext Field | Location |
|-------------|---------------|----------|
| Sales Order No | `sales_order_no` | Tender Price Deviation |
| Order Quantities | `order_qty` | Tender Price Deviation |
| Approved Quantities | `approved_qty` | Tender Price Deviation |
| Tender Reference | `custom_tender` | Sales Order |

## Next Steps

1. **Migrate Data**: Clear existing Tender Price Deviation and Details tables
2. **Test Workflow**: Create test Sales Order with loss-making items
3. **User Training**: Train managers on new approval process
4. **Monitor**: Watch for any issues in production

## Migration Script

```python
# Run in ERPNext console
import frappe

# Clear old data
frappe.db.sql("DELETE FROM `tabTender Price Deviation`")
frappe.db.sql("DELETE FROM `tabTender Price Deviation Details`")
frappe.db.commit()

print("Migration complete - old data cleared")
```

## Testing Checklist

- [ ] Create Tender with items where tender_price < item_cost
- [ ] Create Sales Order with loss-making items
- [ ] Verify approval request created on save
- [ ] Verify Sales Order cannot submit without approval
- [ ] Manager approves in Tender
- [ ] Verify Sales Order can now submit
- [ ] Verify history record created
- [ ] Test quantity validation (order qty > approved qty)
- [ ] Test multiple items in same Sales Order
- [ ] Test multiple Sales Orders for same Tender

---

**Implementation Date**: 2026-05-16  
**Status**: Complete - Ready for Testing
