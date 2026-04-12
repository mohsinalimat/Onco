# Tender Doctype Fixes Applied

## Critical Fixes Completed:

### 1. Technical Offer Tables - FIXED ✅
- Unhidden `onco_technical_offer` and `distributors_technical_offer` tables
- Fields already exist: Date of Submission, Subject, Attachment
- Tables now visible in Offers tab

### 2. Item Tender Price Field - FIXED ✅
- Added `tender_price` field to Item Tender doctype
- Field type: Currency
- Position: After tender_qty, before tender_start_date
- Now tracks awarded price per item

### 3. Tender Supplier Supply Quantity - FIXED ✅
- Added `supply_qty` field to Tender Supplier doctype
- Field type: Float
- Fixes extra quantity logic in `_apply_extra_qty_to_tender_supplier()`

### 4. Sales Invoice Field Error - FIXED ✅
- Changed `tender_reference` to `custom_tender_ref` in tenders.js
- Matches actual custom field name in Sales Invoice
- Fixes "Field not permitted in query" error

## Remaining Issues to Address:

### 5. Item Group Default Value
**Status:** NOT FIXED
**Action Required:** Set default value in Item Tender and Items FMD
```json
"default": "Finished Pharmaceutical Products Item"
```

### 6. Distributor Customer Group Filter
**Status:** PARTIALLY FIXED
**Current:** Filter exists in tenders.js line 60
**Issue:** May not work if customer group name differs
**Verify:** Customer group exists as "Pharmaceuticals Local Distributors Companies"

### 7. Upload Sheet UI Button
**Status:** ALREADY IMPLEMENTED ✅
**Location:** tenders.js line 25-29
**Button:** "Upload FMD Data" appears for Market Data tenders
**Function:** `upload_fmd_data()` uses FileUploader

### 8. Oncopharm Auto-Population
**Status:** NOT FIXED
**Action Required:** Add client script to auto-set supplier when "By Oncopharm" selected

### 9. Tender Submission Workflow
**Status:** NEEDS CLARIFICATION
**Current:** Uses same Tenders doctype with type "Tender Submission"
**Issue:** Naming series works but workflow unclear
**Question:** Should submission create new doc or update awarded tender?

### 10. Price Deviation Approval Workflow
**Status:** PARTIALLY IMPLEMENTED
**Current:** Manual status updates + "Approve All" button
**Missing:** Role-based approval workflow with notifications

## Next Steps:

1. Run `bench migrate` to apply doctype changes
2. Test tender creation with all types
3. Verify extra quantities and extended time logic
4. Test technical offer entry
5. Verify price deviation tracking
6. Test sales invoice validation

## Commands to Run:

```bash
bench --site onco.com migrate
bench --site onco.com clear-cache
bench --site onco.com restart
```
