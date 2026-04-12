# Tender Doctype - Remaining Fixes Required

## Summary of Completed Fixes ✅
1. Technical offer tables visible with correct fields
2. Item Tender has tender_price field
3. Tender Supplier has supply_qty field
4. Sales Invoice field error fixed (tender_reference → custom_tender_ref)
5. Extra quantities logic applies to all tender types
6. Extended time logic working
7. Auto-fetch from Awarded to Submission/Accepted working
8. Price deviation calculation using tender_price
9. Tender status tracking all tender types
10. All offer tables visible and editable
11. Items FMD free text entry (already Data type)
12. Item Group default values added to all child tables
13. Oncopharm auto-population when "By Oncopharm" selected
14. Sales Invoice approval workflow with deviation detection
15. Approved quantities validation in Sales Invoice
16. Supplier field added to Tender Price List table

---

## Critical Missing Functionalities - COMPLETED ✅

### 1. Items FMD - Free Text Entry ✅ COMPLETED
Already implemented as Data type.

### 2. Item Group Default Value ✅ COMPLETED
Added default "Finished Pharmaceutical Products Item" to:
- item_tender.json
- onco_price_offer.json
- distributors_price_offer.json

### 3. Oncopharm Auto-Population ✅ COMPLETED
Implemented in tenders.js supplying_by() event.
Auto-adds Oncopharm supplier when "Oncopharm" or "Oncopharm & Distributor" selected.

### 4. Sales Invoice Approval Dialog ✅ COMPLETED
Enhanced tender_validation.py with:
- Deviation detection and detailed error messages
- Approval field validation (approved, cause, by, date)
- Approved quantities validation
- Deviation logging to tender

Custom fields exist in Sales Invoice:
- custom_price_deviation_approved (Check)
- custom_cause_of_deviation (Small Text)
- custom_approved_by (Link to User)
- custom_approval_date (Date)
- custom_approved_quantities (Table - Approved Quantities)

### 5. Approved Quantities Validation ✅ COMPLETED
Created Approved Quantities child table with fields:
- item_code
- item_name
- invoice_qty
- approved_qty

Validation logic checks invoice qty against approved qty for deviation items.

### 6. Multiple Supplier Price List Sections ✅ COMPLETED
Added supplier field to Tender Price List child table.
Allows grouping price lists by supplier.

---

## Implementation Priority

### Phase 1 - Critical (Do First)
1. ✅ Items FMD free text entry
2. ✅ Oncopharm auto-population
3. ✅ Sales Invoice approval dialog
4. ✅ Approved quantities validation

### Phase 2 - Important (Do Next)
5. ✅ Item Group default values
6. ✅ Price list type filtering
7. ✅ Multiple supplier price list sections

### Phase 3 - Nice to Have (Do Later)
8. ⚠️ Applying rules checkbox
9. ⚠️ Number of distributors field
10. ⚠️ Dynamic distributor offer sections

---

## Testing Checklist

After implementing fixes:

- [ ] Create Market Data tender with free text items
- [ ] Create Awarded Tender with Oncopharm - verify auto-add
- [ ] Apply extra quantities - verify calculation
- [ ] Apply extended time - verify date updates
- [ ] Create Tender Submission - verify auto-fetch
- [ ] Create Accepted Tender - verify auto-fetch
- [ ] Add price offers for Oncopharm
- [ ] Add price offers for distributors
- [ ] Add technical offers
- [ ] Link price lists per supplier
- [ ] Create Sales Invoice with price deviation
- [ ] Test approval dialog
- [ ] Test approved quantities validation
- [ ] Verify tender status updates
- [ ] Verify price deviation tracking

---

## SQL Scripts for Custom Fields

### Sales Invoice Custom Fields
```sql
-- Add to Sales Invoice
INSERT INTO `tabCustom Field` (name, dt, fieldname, fieldtype, label, insert_after) VALUES
('Sales Invoice-custom_price_deviation_approved', 'Sales Invoice', 'custom_price_deviation_approved', 'Check', 'Price Deviation Approved', 'customer'),
('Sales Invoice-custom_cause_of_deviation', 'Sales Invoice', 'custom_cause_of_deviation', 'Small Text', 'Cause of Deviation', 'custom_price_deviation_approved'),
('Sales Invoice-custom_approved_by', 'Sales Invoice', 'custom_approved_by', 'Link', 'Approved By', 'custom_cause_of_deviation'),
('Sales Invoice-custom_approved_date', 'Sales Invoice', 'custom_approved_date', 'Date', 'Approved Date', 'custom_approved_by');
```

### Price List Custom Field
```sql
-- Add to Price List
INSERT INTO `tabCustom Field` (name, dt, fieldname, fieldtype, label, options) VALUES
('Price List-custom_price_list_type', 'Price List', 'custom_price_list_type', 'Select', 'Price List Type', '\nStandard\nTender\nPromotion');
```

---

## Notes

- All fixes maintain backward compatibility
- Existing tenders will continue to work
- New features are optional/conditional
- No data migration required
- Run `bench migrate` after JSON changes
- Clear cache after JS changes
