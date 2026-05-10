# Landed Cost Automation Implementation Plan

## Overview
Implement automatic landed cost distribution for imported pharmaceutical items using Shipment ID as the linking mechanism between foreign supplier invoices and vendor service invoices.

## Requirements Summary

### Step 1: Foreign Supplier Purchase Invoice
- **Current State**: Purchase Invoice already has `custom_shipments` field linking to Shipments doctype
- **Action**: Rename field label from "Shipments" to "Shipment ID" for clarity
- **Purpose**: This invoice covers the cost of imported pharma items

### Step 2: Vendor Service Purchase Invoice  
- **New Requirement**: Add Shipment ID as an **accounting dimension** on vendor service invoices
- **Purpose**: Link local service vendor costs (customs, freight, storage) to specific shipments
- **Implementation**: 
  - Create custom field `custom_shipment_id` as Link to Shipments
  - Configure as accounting dimension so it appears on GL entries
  - This allows tracking which vendor costs belong to which shipment

### Step 3: Landed Cost Voucher Auto-fetch
- **Trigger**: When user selects a foreign supplier Purchase Invoice in Landed Cost Voucher
- **Auto-fetch Logic**:
  1. Detect the Shipment ID from the selected foreign supplier invoice
  2. Search for all vendor invoices with matching Shipment ID (via accounting dimension)
  3. Auto-populate those vendor invoices into the Landed Cost Voucher
  4. Extract expense accounts from vendor invoices
  5. Use those expense accounts to distribute landed costs

## Technical Implementation

### Phase 1: Field Modifications
1. ✅ Verify existing `custom_shipments` field on Purchase Invoice
2. Add `custom_shipment_id` field to Purchase Invoice for vendor invoices
3. Configure Shipment ID as accounting dimension

### Phase 2: Accounting Dimension Setup
1. Create Accounting Dimension for Shipment ID
2. Ensure it propagates to GL Entry
3. Test dimension appears on vendor invoices

### Phase 3: Landed Cost Voucher Customization
1. Add client script to detect when Purchase Invoice is selected
2. Implement auto-fetch logic:
   - Get Shipment ID from selected invoice
   - Query vendor invoices with same Shipment ID
   - Populate Landed Cost Voucher tables
3. Extract and apply expense accounts from vendor invoices

### Phase 4: Server-side Validation
1. Add Python controller methods for Landed Cost Voucher
2. Validate Shipment ID consistency
3. Ensure proper cost distribution

## Frappe v16 Considerations

Based on research:
- **Query Builder**: Use new query builder syntax for database queries
- **Accounting Dimensions**: Standard feature, well-supported in v16
- **Custom Fields**: Use `frappe.get_doc` and standard field creation APIs
- **Client Scripts**: Standard JavaScript, no major changes
- **Known Issues**: None directly affecting this implementation

## Files to Create/Modify

### New Files:
1. `onco/onco/doctype/landed_cost_voucher_hooks.py` - Server-side logic
2. `onco/onco/custom_scripts/landed_cost_voucher.py` - Controller overrides
3. `onco/onco/client_scripts/landed_cost_voucher_auto_fetch.js` - Client script
4. `onco/fixtures/custom_fields.json` - Custom field definitions
5. `onco/fixtures/accounting_dimensions.json` - Dimension configuration

### Modified Files:
1. `onco/onco/custom/purchase_invoice.json` - Add shipment_id field
2. `onco/hooks.py` - Register new hooks and fixtures

## Testing Plan
1. Create test shipment with foreign supplier invoice
2. Create vendor service invoices with Shipment ID dimension
3. Create Landed Cost Voucher and verify auto-fetch
4. Verify GL entries have correct dimensions
5. Verify item valuation updates correctly

## Next Steps
1. Implement Phase 1: Field modifications
2. Implement Phase 2: Accounting dimension setup
3. Implement Phase 3: LCV customization
4. Implement Phase 4: Validation
5. Testing and documentation
