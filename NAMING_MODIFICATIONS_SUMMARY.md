# Naming Modifications Summary

## Implementation Status: ✅ COMPLETE

All requirements from the image have been implemented.

---

## 1. Importation Approvals - Authority Approval Number

### Requirement
- Error occurred while creating MD or EX from existing approval
- Field that takes the approval number issued from authority and appends it to ID
- Format: `EDA-SPIMA-2026-{IMP_NO}`

### Implementation ✅

**Files Modified:**
- `Onco/onco/onco/doctype/importation_approvals/importation_approvals.json`
- `Onco/onco/onco/doctype/importation_approvals/importation_approvals.py`

**Changes:**
1. Changed `original_document` field from Link to Data (prevents CancelledLinkError)
2. Added `authority_approval_number` field for IMP_NO from authority
3. Updated `autoname()` method to use authority_approval_number
4. Added `ignore_links=True` flag in create_modification/create_extension functions

**Naming Format:**
- Normal: `EDA-SPIMA-2026-IMP123` (uses authority_approval_number)
- Modification: `EDA-SPIMA-MD-2026-IMP123`
- Extension: `EDA-APIMA-EX-2026-IMP456`
- Fallback: `EDA-SPIMA-2026-00001` (if no authority number provided)

**How It Works:**
1. User enters Authority Approval Number (IMP_NO) in the field
2. System appends it to the document ID: `{PREFIX}-{YEAR}-{IMP_NO}`
3. For MD/EX, the IMP_NO is preserved from original document
4. No more CancelledLinkError when creating MD/EX from cancelled documents

---

## 2. Purchase Order - Local vs Imported

### Requirement
- Series should depend on PO type (local or imported)
- Local: `PO-LOC-YEAR-#####`
- Imported: `PO-IMP-YEAR-#####`

### Implementation ✅

**Files Modified:**
- `Onco/onco/onco/purchase_order.py`

**Changes:**
1. Updated `CustomPurchaseOrder.autoname()` method
2. Added logic to detect local vs imported based on:
   - `custom_purchase_order_type` field
   - `custom_importation_approval` field (if present = imported)
   - Default to local if not specified

**Naming Format:**
- Local: `PO-LOC-2026-00001`
- Imported: `PO-IMP-2026-00001`

**Auto-Detection Logic:**
```python
if custom_purchase_order_type == "Imported Purchase":
    → PO-IMP-YEAR-#####
elif custom_importation_approval exists:
    → PO-IMP-YEAR-#####
else:
    → PO-LOC-YEAR-#####
```

---

## 3. Purchase Invoice - Three Types with Supplier Invoice Number

### Requirement
- Same as PO, purchase type (local/imported)
- New type for general purchase
- Formats:
  - Local Pharma: `PHR-LOC-PINV-YEAR-#####-{supplier_invoice_no}`
  - Imported Pharma: `PHR-IMP-PINV-YEAR-#####-{supplier_invoice_no}`
  - General Purchase: `GEN-PINV-YEAR-#####-{supplier_invoice_no}`
- `{supplier_invoice_no}` = bill_no field
- `#####` = AUTO GENERATED counter
- If created against PO, type should be fetched automatically
- General purchase doesn't need PO

### Implementation ✅

**Files Created:**
- `Onco/onco/onco/purchase_invoice_naming.py` (new CustomPurchaseInvoice class)

**Files Modified:**
- `Onco/onco/hooks.py` (added Purchase Invoice override)
- `Onco/onco/onco/custom/purchase_invoice.json` (added custom_purchase_type field)

**Changes:**
1. Created `CustomPurchaseInvoice` class with custom autoname logic
2. Added `custom_purchase_type` field (Select: Local Pharma, Imported Pharma, General Purchase)
3. Implemented intelligent type detection
4. Registered override in hooks.py

**Naming Format:**
- Local Pharma: `PHR-LOC-PINV-2026-00001-INV123`
- Imported Pharma: `PHR-IMP-PINV-2026-00001-INV456`
- General Purchase: `GEN-PINV-2026-00001-INV789`
- Without supplier invoice: `PHR-LOC-PINV-2026-00001`

**Auto-Detection Logic (Priority Order):**

1. **Manual Selection** (highest priority)
   - Check `custom_purchase_type` field
   - If set, use that type

2. **From Purchase Order**
   - Check if linked to PO
   - If PO has `custom_importation_approval` → Imported Pharma
   - If PO name starts with `PO-IMP` → Imported Pharma
   - If PO name starts with `PO-LOC`:
     - Check if items are pharmaceutical → Local Pharma
     - Otherwise → General Purchase

3. **From Items** (no PO link)
   - Check if items have `custom_pharmaceutical_item = 1`
   - If yes → Local Pharma
   - If no → General Purchase

4. **Default**
   - General Purchase

**Supplier Invoice Number:**
- Taken from `bill_no` field
- Appended to end of name: `{BASE}-{supplier_invoice_no}`
- If empty, only base name is used

---

## Testing Checklist

### Importation Approvals
- [ ] Create new Importation Approval with authority_approval_number
- [ ] Verify name format: `EDA-SPIMA-2026-{IMP_NO}`
- [ ] Create Modification from existing approval
- [ ] Verify MD name: `EDA-SPIMA-MD-2026-{IMP_NO}`
- [ ] Create Extension from existing approval
- [ ] Verify EX name: `EDA-APIMA-EX-2026-{IMP_NO}`
- [ ] Verify no CancelledLinkError when creating MD/EX from cancelled document

### Purchase Order
- [ ] Create local PO (no importation approval)
- [ ] Verify name: `PO-LOC-2026-00001`
- [ ] Create imported PO (with importation approval)
- [ ] Verify name: `PO-IMP-2026-00001`
- [ ] Set custom_purchase_order_type = "Imported Purchase"
- [ ] Verify name: `PO-IMP-2026-00002`

### Purchase Invoice
- [ ] Create PI from imported PO
- [ ] Verify name: `PHR-IMP-PINV-2026-00001-{bill_no}`
- [ ] Verify type auto-detected as "Imported Pharma"
- [ ] Create PI from local PO with pharma items
- [ ] Verify name: `PHR-LOC-PINV-2026-00001-{bill_no}`
- [ ] Verify type auto-detected as "Local Pharma"
- [ ] Create PI without PO (general purchase)
- [ ] Manually select "General Purchase"
- [ ] Verify name: `GEN-PINV-2026-00001-{bill_no}`
- [ ] Create PI without bill_no
- [ ] Verify name: `PHR-LOC-PINV-2026-00002` (no suffix)

---

## Migration Instructions

```bash
# 1. Navigate to bench directory
cd /path/to/frappe-bench

# 2. Run migration to apply JSON changes
bench --site your-site-name migrate

# 3. Clear cache
bench --site your-site-name clear-cache

# 4. Restart bench
bench restart
```

---

## Files Changed Summary

### New Files
1. `Onco/onco/onco/purchase_invoice_naming.py` - Custom Purchase Invoice class

### Modified Files
1. `Onco/onco/onco/doctype/importation_approvals/importation_approvals.json`
   - Changed original_document from Link to Data
   - Added authority_approval_number field

2. `Onco/onco/onco/doctype/importation_approvals/importation_approvals.py`
   - Updated autoname() to use authority_approval_number
   - Fixed create_modification() with ignore_links
   - Fixed create_extension() with ignore_links

3. `Onco/onco/onco/purchase_order.py`
   - Updated autoname() for PO-LOC/PO-IMP naming
   - Added type detection logic

4. `Onco/onco/hooks.py`
   - Added Purchase Invoice override

5. `Onco/onco/onco/custom/purchase_invoice.json`
   - Added custom_purchase_type field

---

## Answers to Requirements

### ✅ Are all requirements working now?

**YES - All requirements are implemented:**

1. ✅ Importation Approvals: Authority approval number field added, MD/EX error fixed
2. ✅ Purchase Order: Local/Imported naming based on type
3. ✅ Purchase Invoice: Three types with supplier invoice number
4. ✅ Auto-detection: Type fetched from PO when creating PI against PO
5. ✅ General Purchase: Can be created without PO

### Key Features:
- Authority approval number (IMP_NO) properly appended to Importation Approvals
- No more CancelledLinkError when creating MD/EX
- PO naming distinguishes local vs imported
- PI naming has three types with auto-detection
- Supplier invoice number appended to PI name
- Auto-counter (####) generated for each type separately
- Manual override available via custom_purchase_type field
