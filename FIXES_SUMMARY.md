# Oncopharma Application - Issues and Fixes Summary

## Date: March 27, 2026
## Issues Addressed: 19-26

---

## Issue #19: Shipments Submission Validation

**Problem**: Shipments doctype can be submitted even when required fields before the "Create" button are not filled.

**Root Cause**: The `before_submit()` method in `shipments.py` has validation removed with comment "# Validation removed - invoice data is present"

**Solution**: Add comprehensive validation in `before_submit()` method to ensure all required fields are filled based on the tracking bar status.

**Files to Modify**:
- `Onco/onco/onco/doctype/shipments/shipments.py`

---

## Issue #20: Total Net Released Qty Calculation Mismatch

**Problem**: The `total_net_released_qty` field in Authority Good Release parent doctype shows different logic than `net_released_qty` in the child table items.

**Root Cause**: In `calculate_totals()` method, the calculation logic for `total_net_released_qty` doesn't match the item-level `net_released_qty` calculation.

**Current Logic**:
- Child table: `net_released_qty = released_qty` (for non-shortage control) or `net_released_qty = released_qty` (for shortage control)
- Parent total: Sums all `net_released_qty` from child items

**Expected Logic**: Should match exactly - sum of child `net_released_qty` fields.

**Solution**: The logic is actually correct. The issue might be a display/refresh problem. Need to verify the calculation is being triggered properly.

**Files to Check**:
- `Onco/onco/onco/doctype/authority_good_release/authority_good_release.py` - Line 697-710

---

## Issue #21: Release Type Change After Submission Error

**Problem**: Error messages:
1. "Not allowed to change Release Type after submission from None to Lot Release Batch"
2. "Failed to update Shipment: Not allowed to change Release Type after submission from None to Lot Release Batch"

**Root Cause**: When updating Shipment document in `update_shipment_release_status()`, the code tries to set `release_type` field which might be read-only after submission or have validation preventing changes.

**Solution**: Use `db_set()` instead of direct field assignment to bypass validation, or check if Shipment allows field updates after submission.

**Files to Modify**:
- `Onco/onco/onco/doctype/authority_good_release/authority_good_release.py` - Line 1050-1100

---

## Issue #22: Material Transfer Type in Stock Entries

**Problem**: Need to check the type of material transfer created from the "Create Stock Entries" button in Authority Good Release.

**Current Implementation**: 
- `create_sample_stock_entry()` - Creates "Material Transfer" for samples
- `create_released_stock_entry()` - Creates "Material Transfer" for released goods
- `create_final_release_stock_entry()` - Creates "Material Transfer" for final release

**Solution**: All stock entries are correctly set to "Material Transfer" type. This is appropriate for warehouse-to-warehouse transfers.

**Files Verified**:
- `Onco/onco/onco/doctype/authority_good_release/authority_good_release.py` - Lines 1200-1400

---

## Issue #23: Add Registration Number Field to Price Registration

**Problem**: Need to add "registration_number" field to the `Item Price Registration` child table doctype.

**Solution**: Add new field to the doctype JSON.

**Files to Modify**:
- `Onco/onco/onco/doctype/item_price_registration/item_price_registration.json`

---

## Issue #24: Remove update_stock Field from Purchase Invoice

**Problem**: The `update_stock` field in Purchase Invoice doctype updates the stock ledger, which may not be desired behavior.

**Current State**: Property setter sets `update_stock.default = 1`

**Solution**: Remove the property setter that sets the default value to 1, or hide the field entirely.

**Files to Modify**:
- `Onco/onco/onco/custom/purchase_invoice.json` - Remove property setter

---

## Issue #25: Stock User Notification on AGR Submission

**Problem**: Is there notification functionality on submit that pings stock users about new Authority Good Release documents? If so, where is it?

**Investigation Result**: No automatic notification found in the current codebase. The `on_submit()` method only:
1. Updates status
2. Creates stock entries (if flag enabled)
3. Updates shipment release status
4. Updates incoming check report

**Solution**: Need to add notification functionality if required.

**Recommendation**: Add notification using Frappe's notification system or email alerts.

---

## Issue #26: Serial and Batch Bundle Already Used Error

**Problem**: Error "Serial and Batch Bundle 063d5d0c3074b0840645 is already used in Purchase Receipt MAT-PRE-2026-00017" when creating stock entries from Authority Good Release.

**Root Cause**: The Serial and Batch Bundle is being reused from the Purchase Receipt. In ERPNext v15, each stock transaction requires a NEW Serial and Batch Bundle, not reusing existing ones.

**Solution**: Do NOT copy `serial_and_batch_bundle` from source documents. Instead:
1. Let ERPNext create new bundles automatically, OR
2. Create new Serial and Batch Bundle documents programmatically

**Files to Modify**:
- `Onco/onco/onco/doctype/authority_good_release/authority_good_release.py` - Stock entry creation methods

---

## Priority Order for Fixes

1. **CRITICAL - Issue #26**: Serial and Batch Bundle error (blocks stock entries)
2. **HIGH - Issue #19**: Shipments submission validation (data integrity)
3. **HIGH - Issue #21**: Release type change error (blocks workflow)
4. **MEDIUM - Issue #23**: Add registration number field (feature request)
5. **MEDIUM - Issue #24**: Remove update_stock field (configuration)
6. **LOW - Issue #20**: Total net released qty (verification needed)
7. **LOW - Issue #22**: Material transfer type (verification only)
8. **LOW - Issue #25**: Notification functionality (feature request)

---

## Next Steps

1. Review and approve this summary
2. Implement fixes in priority order
3. Test each fix in development environment
4. Deploy to production after testing

