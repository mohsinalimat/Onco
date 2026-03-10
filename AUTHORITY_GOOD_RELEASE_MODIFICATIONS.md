# Authority Good Release Modifications

## Summary of Changes

This document outlines all modifications made to the Authority Good Release doctype based on client requirements.

## Changes Implemented

### 1. Released Goods Warehouse Auto-Population
**Requirement**: Add "Imported Finished Phr Released Warehouse (Oncopharm) - Onco" when creating Authority Good Release from Incoming Check Report.

**Implementation**:
- Modified `authority_good_release.py` - Added `set_released_goods_warehouse()` method in `before_save()`
- Updated `authority_good_release.json` - Changed default value for `released_goods_warehouse` field
- The warehouse is now automatically set when the document is created from Incoming Check Report

### 2. Removed `actual_qty` Field
**Requirement**: Remove the redundant `actual_qty` field as `actual_quantity` already exists and works correctly.

**Implementation**:
- Removed `actual_qty` from `authority_good_release_item.json` field_order
- Updated all Python code references from `actual_qty` to `actual_quantity`
- Updated JavaScript client script to use `actual_quantity` instead of `actual_qty`

### 3. Added `remaining_qty` Field
**Requirement**: Add a field to show how much of the requested quantity remains unreleased.

**Implementation**:
- Added `remaining_qty` field to `authority_good_release_item.json`
- Field is read-only and calculated automatically
- Formula: `remaining_qty = requested_qty - released_qty`
- Added to parent totals as `total_remaining_qty`

### 4. Requested Quantity Logic
**Requirement**: 
- `requested_qty` should be read-only
- Auto-populated from `actual_quantity` field
- User can then edit `released_qty` before submission
- `remaining_qty` shows what's left to release

**Implementation**:
- Changed `requested_qty` to read-only in `authority_good_release_item.json`
- Added auto-population logic in `calculate_quantities()` method
- Formula: `requested_qty = actual_quantity` (auto-set if empty)
- User edits `released_qty` to specify how much to release
- System calculates `remaining_qty = requested_qty - released_qty`

### 5. Shortage Control Quantity Clarification
**Requirement**: Shortage control quantity represents the amount being held back from the released quantity.

**Implementation**:
- Updated calculation logic in `calculate_quantities()` method
- Formula: `net_released_qty = released_qty - shortage_control_qty`
- This means:
  - `released_qty` = Total quantity approved for release
  - `shortage_control_qty` = Amount held back for shortage control
  - `net_released_qty` = Actual quantity going to warehouse (released - shortage control)

### 6. Removed Useless Warehouse Fields
**Requirement**: Remove `sales_warehouse` and `onco_warehouse` fields from Authority Good Release doctype.

**Implementation**:
- Removed both fields from `authority_good_release.json` field_order
- Removed field definitions from JSON
- These fields are not needed in the current workflow

### 7. Updated Quantity Summary Section
**Requirement**: Match the quantity summary totals with the child table fields.

**Implementation**:
- Added `total_remaining_qty` to parent doctype
- Updated `calculate_totals()` method to sum all quantity fields correctly:
  - `total_requested_qty` - Sum of all requested quantities
  - `total_released_qty` - Sum of all released quantities
  - `total_actual_qty` - Sum of all actual quantities (from ICR)
  - `total_remaining_qty` - Sum of all remaining quantities
  - `total_net_released_qty` - Sum of all net released quantities
  - `total_shortage_control_qty` - Sum of all shortage control quantities
  - `total_sample_qty` - Sum of all sample quantities

## Workflow After Changes

### Creating Authority Good Release:

1. **Select Incoming Check Report**: Links to the inspection report
2. **Fetch Items**: Items are populated with:
   - `actual_quantity` - From Incoming Check Report (accepted quantity)
   - `requested_qty` - Auto-set to `actual_quantity` (read-only)
   - `released_qty` - User enters how much to release (editable)
   - `remaining_qty` - Auto-calculated (requested - released)

3. **For Shortage Control** (LRB with Shortage Control):
   - User enters `shortage_control_qty` - Amount to hold back
   - System calculates `net_released_qty = released_qty - shortage_control_qty`
   - Net released quantity goes to warehouse

4. **Submit**: Creates stock entries based on:
   - `net_released_qty` → Released Goods Warehouse
   - `shortage_control_qty` → Remains in source warehouse
   - `withdrew_sample_qty` → Sample Warehouse

### Stock Entry Logic:

When Authority Good Release is submitted:
- **Stock Entry 1** (if samples exist): Moves `withdrew_sample_qty` to Sample Warehouse
- **Stock Entry 2** (main release): Moves `released_qty` (or `net_released_qty` for shortage control) to Released Goods Warehouse
- **Stock Entry 3** (if final release): Moves from Released Goods Warehouse to Sales Warehouse

## Files Modified

1. `Onco/onco/onco/doctype/authority_good_release/authority_good_release.py`
   - Added `set_released_goods_warehouse()` method
   - Updated `calculate_quantities()` method
   - Updated `calculate_totals()` method
   - Changed all `actual_qty` references to `actual_quantity`

2. `Onco/onco/onco/doctype/authority_good_release/authority_good_release.json`
   - Removed `sales_warehouse` and `onco_warehouse` from field_order
   - Added `total_remaining_qty` field
   - Updated `released_goods_warehouse` default value

3. `Onco/onco/onco/doctype/authority_good_release_item/authority_good_release_item.json`
   - Removed `actual_qty` field
   - Added `remaining_qty` field
   - Changed `requested_qty` to read-only

4. `Onco/onco/onco/doctype/authority_good_release/authority_good_release.js`
   - Added `calculate_remaining_qty()` function
   - Updated `calculate_totals()` to include `total_remaining_qty`
   - Changed validation from `actual_qty` to `requested_qty`
   - Updated item fetching logic

## Testing Checklist

- [ ] Create Authority Good Release from Incoming Check Report
- [ ] Verify `released_goods_warehouse` is auto-populated
- [ ] Verify `requested_qty` is read-only and equals `actual_quantity`
- [ ] Edit `released_qty` and verify `remaining_qty` calculates correctly
- [ ] Test shortage control: verify `net_released_qty = released_qty - shortage_control_qty`
- [ ] Verify quantity summary totals match child table sums
- [ ] Submit and verify stock entries are created correctly
- [ ] Verify `sales_warehouse` and `onco_warehouse` fields are removed

## Migration Notes

After deploying these changes, run:

```bash
bench --site your-site-name migrate
bench --site your-site-name clear-cache
bench restart
```

## Questions Answered

**Q: What happens after releasing quantity and submitting?**
A: When you submit the Authority Good Release:
1. System validates all quantities
2. Creates stock entries automatically (if `create_stock_entry` is checked):
   - Moves `net_released_qty` from Inspection Warehouse to Released Goods Warehouse
   - Moves `withdrew_sample_qty` to Sample Warehouse (if applicable)
3. Updates Incoming Check Report with total released quantities
4. Updates Shipment with release status
5. Tracks cumulative releases across multiple AGR documents

**Q: How does shortage control work?**
A: 
- You specify `released_qty` = Total approved for release
- You specify `shortage_control_qty` = Amount to hold back
- System calculates `net_released_qty = released_qty - shortage_control_qty`
- Only `net_released_qty` moves to Released Goods Warehouse
- `shortage_control_qty` remains in source warehouse for future release

**Q: Can I release in multiple batches?**
A: Yes! The `remaining_qty` field shows what's left to release. You can create multiple Authority Good Release documents for the same Incoming Check Report, and the system tracks cumulative releases.
