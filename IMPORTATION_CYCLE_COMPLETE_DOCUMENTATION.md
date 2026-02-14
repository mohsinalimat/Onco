# Importation Cycle - Complete Documentation
## Onco Pharma ERPNext Application

**Version**: 1.0  
**Last Updated**: February 2026  
**Application**: Onco Custom App for ERPNext v15

---

## Table of Contents

1. [Overview](#overview)
2. [Complete Workflow](#complete-workflow)
3. [Doctypes and Their Purpose](#doctypes-and-their-purpose)
4. [Step-by-Step Process](#step-by-step-process)
5. [Field Mappings](#field-mappings)
6. [Automatic Processes](#automatic-processes)
7. [User Guide](#user-guide)
8. [Technical Implementation](#technical-implementation)
9. [Troubleshooting](#troubleshooting)
10. [Deployment Guide](#deployment-guide)

---

## Overview

The Importation Cycle is a comprehensive workflow for managing imported pharmaceutical products from approval through to sales. It ensures complete traceability, quality control, and compliance with regulatory requirements.

### Key Features
- ✅ Complete traceability from approval to sales
- ✅ Comprehensive inspection and quality control
- ✅ Automatic stock movements based on inspection results
- ✅ Temperature control monitoring
- ✅ Document verification
- ✅ Batch tracking
- ✅ Multi-warehouse management
- ✅ Compliance documentation
- ✅ Audit trail for all transactions

### Supported Scenarios
1. **One Purchase Order → One Invoice**: Simple single-supplier orders
2. **Multiple Purchase Orders → One Invoice**: Consolidated invoicing
3. **Multiple Invoices → One Shipment**: Consolidated shipping

---

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPORTATION CYCLE WORKFLOW                    │
└─────────────────────────────────────────────────────────────────┘

1. IMPORTATION APPROVAL REQUEST
   └─> Create request for import approval from authorities
       (EDA-SPIMR or EDA-APIMR)

2. IMPORTATION APPROVALS
   └─> Receive approval from authorities
       (Totally Approved / Partially Approved / Refused)

3. PURCHASE ORDER
   └─> Create PO based on approved quantities

4. PURCHASE INVOICE
   └─> Receive invoice from supplier

5. SHIPMENTS
   └─> Create shipment linking multiple invoices
       └─> Track milestones (Arrived, Bank Auth, Customs, etc.)

6. PURCHASE RECEIPT
   └─> Goods physically received at warehouse
       └─> Created from Shipments doctype

7. STOCK ENTRY #1 (Manual)
   └─> Move goods to Inspection Warehouse
       └─> Material Transfer from Receipt to Inspection

8. INCOMING CHECK REPORT ⭐ NEW
   └─> Comprehensive inspection of goods
       ├─> Vehicle inspection
       ├─> Document verification
       ├─> Physical checks
       ├─> Temperature control
       └─> Record accepted/damaged quantities

9. AUTO STOCK ENTRIES (Automatic)
   ├─> Stock Entry #2: Accepted items → Accepted Warehouse
   └─> Stock Entry #3: Damaged items → Rejected Warehouse

10. PURCHASE RECEIPT REPORT
    └─> Compliance documentation
        └─> Created from Incoming Check Report

11. PRINTING ORDER
    └─> Print labels for items
        └─> Created from Purchase Receipt Report

12. AUTHORITY GOOD RELEASE
    └─> Release goods to sales warehouse
        └─> Created from Printing Order

13. AUTO STOCK ENTRY (Automatic)
    ├─> Released items → Sales Warehouse
    └─> Samples → Sample Warehouse

14. SALES
    └─> Create Sales Orders and Invoices
```

---

## Doctypes and Their Purpose

### 1. Importation Approval Request
**Purpose**: Request import approval from regulatory authorities (EDA)  
**Type**: Submittable  
**Created From**: Manual entry  
**Creates**: Importation Approvals (IMAR)

**Key Fields**:
- Product Name
- Supplier Name (auto-linked)
- Requested Quantity
- Requested To (Customer)
- Request Date

**Types**:
- **EDA-SPIMR**: Special Importation Approval Request
- **EDA-APIMR**: Annual Importation Approval Request

---

### 2. Importation Approvals
**Purpose**: Record approval status from authorities  
**Type**: Submittable  
**Created From**: Importation Approval Request  
**Creates**: Purchase Order

**Key Fields**:
- Approval Status (Totally Approved / Partially Approved / Refused)
- Approved Quantity
- Approval Date
- Approval Number

---

### 3. Shipments
**Purpose**: Track shipment from supplier to warehouse  
**Type**: Submittable  
**Created From**: Manual (links multiple Purchase Invoices)  
**Creates**: Purchase Receipt

**Key Fields**:
- Shipment Reference
- Source Warehouse
- Multiple Purchase Invoices (child table)
- Milestones:
  - Arrived
  - Bank Authenticated
  - Restricted Release Status
  - Customs Release Status
  - Received at Warehouse

**Status**: Auto-calculated based on milestone completion

---

### 4. Purchase Receipt
**Purpose**: Record physical receipt of goods  
**Type**: ERPNext Standard (Submittable)  
**Created From**: Shipments  
**Creates**: Stock Entry

**Custom Fields**:
- `custom_shipment_ref`: Link to Shipments

**Key Features**:
- Records received quantities
- Creates batch numbers
- Updates stock balances
- Links to Purchase Invoice

---

### 5. Stock Entry (to Inspection)
**Purpose**: Move goods from receipt warehouse to inspection warehouse  
**Type**: ERPNext Standard (Submittable)  
**Created From**: Manual (from Purchase Receipt)  
**Creates**: Incoming Check Report

**Custom Fields**:
- `custom_purchase_receipt`: Link to Purchase Receipt
- `custom_shipment_ref`: Link to Shipments (auto-fetched)

**Purpose**: Material Transfer  
**From**: Receipt Warehouse  
**To**: Inspection Warehouse

---

### 6. Incoming Check Report ⭐ NEW
**Purpose**: Comprehensive inspection of received goods  
**Type**: Submittable  
**Created From**: Stock Entry  
**Creates**: 
- Auto Stock Entries (to Accepted/Rejected Warehouses)
- Purchase Receipt Report (button)

**Key Sections**:

#### A. Vehicle Inspection
- Seal Numbers
- Seal Integrity
- Temperature Recorder Status

#### B. Document Check
- Commercial Invoice Present
- Packing List Present
- Bill of Lading Present
- Certificate of Analysis Present
- COO/GMP Certificate Present
- All Documents Consistent

#### C. Physical Check
- Seal Integrity Verified
- Package Condition OK
- Labels Verified
- Quantity Verified

#### D. Temperature Control
- Data Logger Present (Yes/No)
- Temperature Range Status (In-Range/Out-of-Range)
- Out-of-range Action:
  - Quarantine and Notify QA
  - Accept with Reason
- Acceptance Reason (if accepted despite deviation)

#### E. Quantity Verification (Child Table)
For each item:
- Shipment No
- Invoice No (Purchase Receipt)
- Item Code & Name
- Batch No
- Invoice Quantity
- Received Quantity
- Shortage Quantity (auto-calculated)
- Over Quantity
- Damage Quantity
- **Accepted Quantity** (auto-calculated)
- Manufacturing Date
- Expiry Date

**Calculations**:
```
Shortage Quantity = max(0, Invoice Quantity - Received Quantity)
Accepted Quantity = Received Quantity - Damage Quantity - Over Quantity
```

#### F. Inspection Result
- Passed
- Failed
- Quarantined

#### G. Warehouse Assignment
- Inspection Warehouse (auto-filled from Stock Entry)
- Accepted Warehouse (required if Passed)
- Rejected Warehouse (required if Failed/Quarantined)

#### H. Notification
- Send Shipment Receipt Notification (checkbox)
- Notification Email (supplier email)

**Automatic Actions on Submit**:
1. Creates Stock Entry for accepted items → Accepted Warehouse
2. Creates Stock Entry for damaged items → Rejected Warehouse
3. Updates Shipment inspection status
4. Sends email notification (if requested)

---

### 7. Purchase Receipt Report
**Purpose**: Compliance documentation of inspection  
**Type**: Submittable  
**Created From**: Incoming Check Report (button)  
**Creates**: Printing Order (button)

**Key Fields**:
- Purchase Receipt
- Shipment Reference
- Vehicle Inspection checks
- Document checks
- Physical checks
- Temperature control
- Items with accepted/damaged quantities

**Purpose**: Serves as official inspection record for compliance and audit

---

### 8. Printing Order
**Purpose**: Print labels for accepted items  
**Type**: Submittable  
**Created From**: Purchase Receipt Report (button)  
**Creates**: Authority Good Release (button, after marking as Completed)

**Key Fields**:
- Shipment No
- Date
- Items with quantities in stock
- Status (Draft/Completed)

**Workflow**:
1. Create from Purchase Receipt Report
2. Print labels for items
3. Mark as "Completed"
4. Create Authority Good Release

---

### 9. Authority Good Release
**Purpose**: Authorize release of goods from inspection to sales warehouse  
**Type**: Submittable  
**Created From**: Printing Order (button)  
**Creates**: Auto Stock Entry (on submit)

**Key Fields**:
- Shipment No
- Release Date
- Lot Release Subtype:
  - Lot Release Batch
  - Lot Release Batch with Shortage Control Quantity
- Warehouse From (Inspection/Unreleased Warehouse)
- Warehouse To (Sales Warehouse)
- Sample Warehouse
- No of Samples

**Items**:
- Item Code & Name
- Batch No
- Requested Qty
- Released Qty
- Actual Qty
- Shortage Control Qty (auto-calculated)
- Sample Qty
- Net Released Qty (auto-calculated)
- Release Status (Released/Held)

**Automatic Actions on Submit**:
1. Creates Stock Entry: Released items → Sales Warehouse
2. Creates Stock Entry: Samples → Sample Warehouse (if applicable)
3. Updates Shipment customs release status

---

### 10. Stock Entry (to Sales)
**Purpose**: Move released goods to sales warehouse  
**Type**: ERPNext Standard (Submittable)  
**Created From**: Authority Good Release (automatic)  
**Creates**: Nothing (end of importation cycle)

**Custom Fields**:
- `custom_shipment_ref`: Link to Shipments
- `custom_agr_ref`: Link to Authority Good Release

**Purpose**: Material Transfer  
**From**: Inspection/Unreleased Warehouse  
**To**: Sales Warehouse

---

## Step-by-Step Process

### Phase 1: Approval and Ordering

#### Step 1: Create Importation Approval Request
1. Go to: **Onco > Importation Approval Request > New**
2. Select Type: EDA-SPIMR or EDA-APIMR
3. Fill in:
   - Product Name
   - Requested Quantity
   - Requested To (Customer, if applicable)
   - Date
4. Save
5. Submit

#### Step 2: Create Importation Approvals
1. Go to: **Onco > Importation Approvals > New**
2. Link to Importation Approval Request
3. Set Status:
   - Totally Approved (quantity auto-filled)
   - Partially Approved (enter approved quantity)
   - Refused
4. Enter Approval Number and Date
5. Save
6. Submit

#### Step 3: Create Purchase Order
1. Go to: **Buying > Purchase Order > New**
2. Select Supplier
3. Add items based on approved quantities
4. Save
5. Submit

#### Step 4: Create Purchase Invoice
1. Go to: **Buying > Purchase Invoice > New**
2. Link to Purchase Order (optional)
3. Add items
4. Link to Importation Approval
5. Save
6. Submit

---

### Phase 2: Shipment and Receipt

#### Step 5: Create Shipments
1. Go to: **Onco > Shipments > New**
2. Fill in:
   - Shipment Reference
   - Source Warehouse
3. Add Purchase Invoices (child table):
   - Select Purchase Invoice
   - Add items with quantities, batches, expiry dates
4. Save
5. Update Milestones as shipment progresses:
   - ☑ Arrived
   - ☑ Bank Authenticated
   - ☑ Restricted Release Status
   - ☑ Customs Release Status
   - ☑ Received at Warehouse
6. Submit (when all milestones complete)

#### Step 6: Create Purchase Receipt
1. From Shipments form, click: **Create > Purchase Receipt**
2. System auto-fills:
   - Items from all linked invoices
   - Quantities
   - Batches
   - Shipment Reference
3. Select Warehouse
4. Save
5. Submit

---

### Phase 3: Inspection (NEW PROCESS)

#### Step 7: Create Stock Entry to Inspection Warehouse
1. From Purchase Receipt, click: **Create > Stock Entry**
2. Set:
   - Purpose: Material Transfer
   - Source Warehouse: (from Purchase Receipt)
   - Target Warehouse: **Inspection Warehouse**
3. Items auto-filled from Purchase Receipt
4. Save
5. Submit

**System automatically sets**:
- `custom_purchase_receipt`: Links to Purchase Receipt
- `custom_shipment_ref`: Links to Shipment

#### Step 8: Create Incoming Check Report
1. From Stock Entry, click: **Create > Create Incoming Check Report**
2. System auto-fills:
   - Stock Entry reference
   - Purchase Receipt
   - Shipment
   - Inspection Warehouse
   - Items with quantities

3. **Perform Inspection**:

   **A. Vehicle Inspection**:
   - Enter Seal Numbers
   - Check Seal Integrity
   - Check Temperature Recorder Status

   **B. Document Check**:
   - ☑ Commercial Invoice Present
   - ☑ Packing List Present
   - ☑ Bill of Lading Present
   - ☑ Certificate of Analysis Present
   - ☑ COO/GMP Certificate Present
   - ☑ All Documents Consistent

   **C. Physical Check**:
   - ☑ Seal Integrity Verified
   - ☑ Package Condition OK
   - ☑ Labels Verified
   - ☑ Quantity Verified

   **D. Temperature Control**:
   - Data Logger Present: Yes/No
   - If Yes:
     - Temperature Range Status: In-Range/Out-of-Range
     - If Out-of-Range:
       - Action: Quarantine or Accept with Reason
       - Enter Acceptance Reason (if accepting)

   **E. Quantity Verification**:
   - Review each item
   - Enter Damage Quantity (if any)
   - Enter Over Quantity (if any)
   - System auto-calculates Accepted Quantity

4. **Set Inspection Result**:
   - Passed
   - Failed
   - Quarantined

5. **Set Warehouses**:
   - Accepted Warehouse (if Passed)
   - Rejected Warehouse (if Failed/Quarantined)

6. **Optional**: Enable notification to supplier

7. Save

8. **Submit**

**System Automatically**:
- Creates Stock Entry #1: Accepted items → Accepted Warehouse
- Creates Stock Entry #2: Damaged items → Rejected Warehouse
- Updates Shipment inspection status
- Sends email notification (if enabled)

---

### Phase 4: Compliance and Release

#### Step 9: Create Purchase Receipt Report
1. From Incoming Check Report, click: **Create > Create Purchase Receipt Report**
2. System auto-fills:
   - All inspection checks
   - All items with quantities
   - Purchase Receipt reference
   - Shipment reference
3. Review data
4. Save
5. Submit

#### Step 10: Create Printing Order
1. From Purchase Receipt Report, click: **Create > Printing Order**
2. System auto-fills items with accepted quantities
3. Print labels for items
4. Save
5. Submit
6. Click: **Mark as Completed**

#### Step 11: Create Authority Good Release
1. From Printing Order (after marking as Completed), click: **Create > Authority Good Release**
2. Fill in:
   - Release Date
   - Lot Release Subtype
   - Warehouse From (Inspection/Unreleased)
   - Warehouse To (Sales)
   - Sample Warehouse (if taking samples)
   - No of Samples
3. Review items:
   - Set Released Qty for each item
   - Set Sample Qty (if applicable)
   - Set Release Status (Released/Held)
4. Save
5. **Submit**

**System Automatically**:
- Creates Stock Entry: Released items → Sales Warehouse
- Creates Stock Entry: Samples → Sample Warehouse
- Updates Shipment customs release status

---

### Phase 5: Sales

#### Step 12: Create Sales Order/Invoice
1. Goods now in Sales Warehouse
2. Create Sales Order as normal
3. Create Delivery Note
4. Create Sales Invoice
5. Complete sales process

---

## Field Mappings

### Stock Entry → Incoming Check Report

| Stock Entry | Incoming Check Report |
|-------------|----------------------|
| name | stock_entry |
| custom_purchase_receipt | purchase_receipt |
| custom_shipment_ref | shipment |
| to_warehouse | inspection_warehouse |
| items[].item_code | items[].item_code |
| items[].item_name | items[].item_name |
| items[].batch_no | items[].batch_no |
| items[].qty | items[].received_quantity |

### Incoming Check Report → Purchase Receipt Report

| Incoming Check Report | Purchase Receipt Report |
|----------------------|-------------------------|
| purchase_receipt | purchase_receipt |
| shipment | custom_shipment_ref |
| seal_integrity_verified | seal_numbers_match |
| temperature_recorder_status | temp_recorder_status |
| commercial_invoice_present | invoice_present |
| packing_list_present | packing_list_present |
| bill_of_lading_present | awb_present |
| certificate_of_analysis_present | coa_present |
| seal_integrity_verified | seal_integrity |
| package_condition_ok | package_condition |
| labels_verified | label_verification |
| quantity_verified | quantity_verification |
| data_logger_present | data_logger_present |
| temperature_range_status | out_of_range |
| out_of_range_action | quarantine_notify |
| acceptance_reason | accept_reason |
| items[].invoice_quantity | items[].invoice_qty |
| items[].received_quantity | items[].received_qty |
| items[].damage_quantity | items[].damage_qty |
| items[].over_quantity | items[].over_qty |
| items[].accepted_quantity | items[].accepted_qty |

### Purchase Receipt Report → Printing Order

| Purchase Receipt Report | Printing Order |
|------------------------|----------------|
| custom_shipment_ref | shipment_no |
| items[].item_code | items[].item_code |
| items[].item_name | items[].item_name |
| items[].batch_no | items[].batch_no |
| items[].accepted_qty | items[].qty_in_stock |
| items[].expiry_date | items[].expiry_date |

### Printing Order → Authority Good Release

| Printing Order | Authority Good Release |
|----------------|------------------------|
| shipment_no | shipment_no |
| items[].item_code | items[].item_code |
| items[].item_name | items[].item_name |
| items[].batch_no | items[].batch_no |
| items[].qty_in_stock | items[].accepted_qty |

---

## Automatic Processes

### 1. Stock Entry Hook (before_save)
**File**: `onco/onco/stock_entry_hooks.py`

**Triggers**: When Stock Entry is saved

**Actions**:
1. Checks if Stock Entry items have `purchase_receipt` field
2. If found, sets `custom_purchase_receipt` on parent
3. Fetches `custom_shipment_ref` from Purchase Receipt
4. Sets `custom_shipment_ref` on Stock Entry
5. Shows alert message to user

**Fallback**: If not found, queries database to match by warehouse and item

---

### 2. Incoming Check Report Auto Stock Entries (on_submit)
**File**: `onco/onco/doctype/incoming_check_report/incoming_check_report.py`

**Triggers**: When Incoming Check Report is submitted

**Actions**:
1. Separates items by accepted vs damaged quantities
2. **If accepted items exist**:
   - Creates Stock Entry (Material Transfer)
   - From: Inspection Warehouse
   - To: Accepted Warehouse
   - Items: All with accepted_quantity > 0
   - Submits automatically
3. **If damaged items exist**:
   - Creates Stock Entry (Material Transfer)
   - From: Inspection Warehouse
   - To: Rejected Warehouse
   - Items: All with (damage_quantity + over_quantity) > 0
   - Submits automatically
4. Updates Shipment inspection status
5. Sends email notification (if enabled)

**Error Handling**:
- Logs errors to Error Log
- Shows user-friendly error message
- Incoming Check Report remains submitted
- User can manually create Stock Entry if needed

---

### 3. Authority Good Release Auto Stock Entries (on_submit)
**File**: `onco/onco/doctype/authority_good_release/authority_good_release.py`

**Triggers**: When Authority Good Release is submitted

**Actions**:
1. **Creates Stock Entry for Released Items**:
   - From: Inspection/Unreleased Warehouse
   - To: Sales Warehouse
   - Items: All with net_released_qty > 0 and status = "Released"
   - Submits automatically

2. **Creates Stock Entry for Samples** (if applicable):
   - From: Inspection/Unreleased Warehouse
   - To: Sample Warehouse
   - Items: Sample quantities
   - Submits automatically

3. Updates Shipment customs release status

**Calculations**:
```
Shortage Control Qty = Actual Qty - Released Qty (if enabled)
Net Released Qty = Released Qty
```

---

### 4. Purchase Receipt Shipment Update (on_submit)
**File**: `onco/onco/doctype/shipments/shipments.py`

**Triggers**: When Purchase Receipt is submitted

**Actions**:
1. If Purchase Receipt has `custom_shipment_ref`
2. Updates Shipment:
   - `received_at_warehouse` = 1
   - `received_date` = now()
3. Shows message to user

---

## User Guide

### Quick Reference

#### Creating Documents
| From | To | Button Location |
|------|----|-----------------| 
| Shipments | Purchase Receipt | Create > Purchase Receipt |
| Purchase Receipt | Stock Entry | Create > Stock Entry |
| Stock Entry | Incoming Check Report | Create > Create Incoming Check Report |
| Incoming Check Report | Purchase Receipt Report | Create > Create Purchase Receipt Report |
| Purchase Receipt Report | Printing Order | Create > Printing Order |
| Printing Order | Authority Good Release | Create > Authority Good Release (after marking Completed) |

#### Viewing Related Documents
| From | View | Button Location |
|------|------|-----------------|
| Incoming Check Report | Stock Entries | View > View Stock Entries |
| Incoming Check Report | Purchase Receipt Report | View > View Purchase Receipt Report |

---

### Common Tasks

#### Task 1: Inspect Received Goods
1. Open Stock Entry (Material Transfer to Inspection)
2. Click "Create Incoming Check Report"
3. Fill in all inspection checks
4. Enter damage quantities (if any)
5. Set Inspection Result
6. Set Accepted/Rejected Warehouses
7. Submit
8. System automatically moves goods to appropriate warehouses

#### Task 2: Release Goods to Sales
1. Open Incoming Check Report
2. Click "Create Purchase Receipt Report"
3. Submit Purchase Receipt Report
4. Click "Create Printing Order"
5. Print labels
6. Mark as "Completed"
7. Click "Create Authority Good Release"
8. Set release quantities
9. Submit
10. System automatically moves goods to Sales Warehouse

#### Task 3: Handle Damaged Goods
1. In Incoming Check Report, enter Damage Quantity
2. Set Rejected Warehouse
3. Submit
4. System automatically moves damaged goods to Rejected Warehouse
5. Accepted goods go to Accepted Warehouse

#### Task 4: Handle Temperature Deviations
1. In Incoming Check Report:
   - Data Logger Present: Yes
   - Temperature Range Status: Out-of-Range
   - Out-of-range Action:
     - **Quarantine**: Goods held for QA review
     - **Accept with Reason**: Enter justification
2. If Quarantine selected:
   - Inspection Result auto-sets to "Quarantined"
   - Goods moved to Rejected Warehouse
3. If Accept with Reason:
   - Enter detailed reason
   - Can proceed with normal flow

#### Task 5: Track Shipment Status
1. Open Shipments document
2. Check Milestones:
   - ☐ Arrived
   - ☐ Bank Authenticated
   - ☐ Restricted Release Status
   - ☐ Customs Release Status
   - ☐ Received at Warehouse
3. Status auto-updates:
   - Draft: No milestones
   - In Progress: Some milestones
   - Completed: All milestones

#### Task 6: View Complete History
1. Open any document in the cycle
2. Check "Connections" section
3. See all linked documents:
   - Upstream (what created this)
   - Downstream (what this created)
4. Click to navigate between documents

---

### Best Practices

#### Inspection
1. ✅ Always perform complete inspection before submitting
2. ✅ Document all deviations with clear reasons
3. ✅ Take photos of damaged goods (attach to document)
4. ✅ Verify batch numbers match documentation
5. ✅ Check expiry dates are acceptable
6. ✅ Ensure temperature data logger is reviewed

#### Warehouse Management
1. ✅ Use dedicated Inspection Warehouse
2. ✅ Keep Accepted and Rejected Warehouses separate
3. ✅ Regularly review Rejected Warehouse inventory
4. ✅ Ensure Sales Warehouse has proper access controls

#### Documentation
1. ✅ Complete all required fields
2. ✅ Add remarks for any unusual situations
3. ✅ Attach supporting documents (COA, temperature logs, etc.)
4. ✅ Ensure all documents are submitted before proceeding

#### Quality Control
1. ✅ Never skip inspection steps
2. ✅ Always verify quantities match documentation
3. ✅ Report temperature deviations immediately
4. ✅ Quarantine suspicious goods
5. ✅ Notify QA team of any issues

---

## Technical Implementation

### Custom Fields

#### Stock Entry
```json
{
  "custom_purchase_receipt": {
    "fieldtype": "Link",
    "options": "Purchase Receipt",
    "read_only": 1
  },
  "custom_shipment_ref": {
    "fieldtype": "Link",
    "options": "Shipments",
    "read_only": 1,
    "fetch_from": "custom_purchase_receipt.custom_shipment_ref"
  }
}
```

#### Purchase Receipt
```json
{
  "custom_shipment_ref": {
    "fieldtype": "Link",
    "options": "Shipments"
  }
}
```

---

### Hooks Configuration

**File**: `onco/hooks.py`

```python
doc_events = {
    "Purchase Receipt": {
        "on_submit": "onco.onco.doctype.shipments.shipments.on_purchase_receipt_submit"
    },
    "Stock Entry": {
        "before_save": "onco.onco.stock_entry_hooks.before_save"
    }
}

doctype_js = {
    "Stock Entry": "public/js/stock_entry_incoming_check.js"
}
```

---

### API Methods

#### 1. Create Incoming Check Report from Stock Entry
```python
@frappe.whitelist()
def make_incoming_check_report(source_name, target_doc=None):
    """
    Creates Incoming Check Report from Stock Entry
    
    Args:
        source_name: Stock Entry name
        target_doc: Optional target document
        
    Returns:
        Mapped Incoming Check Report document
    """
```

**Usage**:
```javascript
frappe.model.open_mapped_doc({
    method: "onco.onco.doctype.incoming_check_report.incoming_check_report.make_incoming_check_report",
    frm: frm
});
```

#### 2. Create Purchase Receipt Report from Incoming Check Report
```python
@frappe.whitelist()
def make_purchase_receipt_report(source_name, target_doc=None):
    """
    Creates Purchase Receipt Report from Incoming Check Report
    
    Args:
        source_name: Incoming Check Report name
        target_doc: Optional target document
        
    Returns:
        Mapped Purchase Receipt Report document
    """
```

**Usage**:
```javascript
frappe.model.open_mapped_doc({
    method: "onco.onco.doctype.incoming_check_report.incoming_check_report.make_purchase_receipt_report",
    frm: frm
});
```

#### 3. Create Printing Order from Purchase Receipt Report
```python
@frappe.whitelist()
def make_printing_order(source_name, target_doc=None):
    """
    Creates Printing Order from Purchase Receipt Report
    
    Args:
        source_name: Purchase Receipt Report name
        target_doc: Optional target document
        
    Returns:
        Mapped Printing Order document
    """
```

#### 4. Create Authority Good Release from Printing Order
```python
@frappe.whitelist()
def make_authority_good_release(source_name, target_doc=None):
    """
    Creates Authority Good Release from Printing Order
    
    Args:
        source_name: Printing Order name
        target_doc: Optional target document
        
    Returns:
        Mapped Authority Good Release document
    """
```

---

### Database Schema

#### Key Tables

**Incoming Check Report**
- `tabIncoming Check Report` (parent)
- `tabIncoming Check Report Item` (child)

**Purchase Receipt Report**
- `tabPurchase Receipt Report` (parent)
- `tabPurchase Receipt Report Item` (child)

**Printing Order**
- `tabPrinting Order` (parent)
- `tabPrinting Order Item` (child)

**Authority Good Release**
- `tabAuthority Good Release` (parent)
- `tabAuthority Good Release Item` (child)

---

### Permissions

#### Required Roles

**Inspection Team**:
- Read: Purchase Receipt, Stock Entry
- Create/Submit: Incoming Check Report
- Read: Purchase Receipt Report

**Quality Control**:
- Read: All inspection documents
- Create/Submit: Purchase Receipt Report
- Read: Printing Order, Authority Good Release

**Warehouse Manager**:
- Read: All documents
- Create/Submit: Printing Order, Authority Good Release
- Manage: Stock Entries

**System Manager**:
- Full access to all doctypes
- Can modify configurations
- Can view Error Log

---

## Troubleshooting

### Issue 1: Stock Entry doesn't have Purchase Receipt reference

**Symptoms**:
- `custom_purchase_receipt` field is empty
- Incoming Check Report shows warning
- Cannot trace back to Purchase Receipt

**Causes**:
1. Stock Entry not created from Purchase Receipt
2. Stock Entry items don't have `purchase_receipt` field
3. Hook not triggered

**Solutions**:
1. **Check Stock Entry items**:
   ```python
   se = frappe.get_doc("Stock Entry", "MAT-STE-2026-XXXXX")
   for item in se.items:
       print(f"Item: {item.item_code}, PR: {item.get('purchase_receipt')}")
   ```

2. **Manually set if needed**:
   ```python
   frappe.db.set_value("Stock Entry", "MAT-STE-2026-XXXXX", 
       "custom_purchase_receipt", "MAT-PRE-2026-XXXXX")
   ```

3. **Verify hook is registered**:
   - Check `hooks.py` has Stock Entry before_save hook
   - Run `bench migrate`
   - Restart bench

---

### Issue 2: Auto Stock Entries not created from Incoming Check Report

**Symptoms**:
- Incoming Check Report submitted successfully
- No Stock Entries created
- No success messages shown

**Causes**:
1. No accepted or damaged quantities
2. Warehouses not set
3. Error in Stock Entry creation
4. Insufficient permissions

**Solutions**:
1. **Check Error Log**:
   - Go to: Setup > Error Log
   - Look for "Incoming Check Report - Stock Entry Creation Failed"

2. **Verify quantities**:
   ```python
   icr = frappe.get_doc("Incoming Check Report", "ICR-2026-XXXXX")
   for item in icr.items:
       print(f"Item: {item.item_code}")
       print(f"  Accepted: {item.accepted_quantity}")
       print(f"  Damaged: {item.damage_quantity}")
   ```

3. **Check warehouses**:
   ```python
   print(f"Inspection: {icr.inspection_warehouse}")
   print(f"Accepted: {icr.accepted_warehouse}")
   print(f"Rejected: {icr.rejected_warehouse}")
   ```

4. **Verify permissions**:
   - User must have Stock Entry create/submit permissions
   - Check Role Permission Manager

---

### Issue 3: Purchase Receipt Report not created from Incoming Check Report

**Symptoms**:
- Button doesn't appear
- Error when clicking button
- Fields not mapped correctly

**Causes**:
1. Incoming Check Report not submitted
2. Purchase Receipt Report already exists
3. Missing Purchase Receipt reference
4. JavaScript error

**Solutions**:
1. **Check if already exists**:
   ```python
   frappe.db.get_value("Purchase Receipt Report", 
       {"purchase_receipt": "MAT-PRE-2026-XXXXX"}, "name")
   ```

2. **Check browser console** for JavaScript errors

3. **Verify method exists**:
   ```python
   from onco.onco.doctype.incoming_check_report.incoming_check_report import make_purchase_receipt_report
   doc = make_purchase_receipt_report("ICR-2026-XXXXX")
   print(doc.as_dict())
   ```

4. **Clear cache**:
   ```bash
   bench --site [site] clear-cache
   bench restart
   ```

---

### Issue 4: Authority Good Release doesn't create Stock Entry

**Symptoms**:
- Authority Good Release submitted
- No Stock Entry created
- No success message

**Causes**:
1. No items with released status
2. Net released quantity is 0
3. Warehouse not set
4. Error in creation

**Solutions**:
1. **Check items**:
   ```python
   agr = frappe.get_doc("Authority Good Release", "AGR-2026-XXXXX")
   for item in agr.items:
       print(f"Item: {item.item_code}")
       print(f"  Released Qty: {item.released_qty}")
       print(f"  Net Released: {item.net_released_qty}")
       print(f"  Status: {item.release_status}")
   ```

2. **Verify at least one item has**:
   - `net_released_qty` > 0
   - `release_status` = "Released"

3. **Check Error Log** for details

---

### Issue 5: Incorrect Stock Balances

**Symptoms**:
- Stock balance doesn't match expected
- Items missing from warehouse
- Duplicate stock entries

**Causes**:
1. Multiple Stock Entries created
2. Stock Entry not submitted
3. Wrong warehouse selected
4. Batch tracking issues

**Solutions**:
1. **Check Stock Ledger**:
   ```python
   frappe.db.sql("""
       SELECT posting_date, voucher_no, actual_qty, qty_after_transaction, warehouse
       FROM `tabStock Ledger Entry`
       WHERE item_code = '4260095680853: Anexate® 0.5 m...'
       AND warehouse LIKE '%Inspection%'
       ORDER BY posting_date DESC, posting_time DESC
       LIMIT 20
   """, as_dict=True)
   ```

2. **Check Bin**:
   ```python
   frappe.db.get_value("Bin", 
       {"item_code": "ITEM-CODE", "warehouse": "WAREHOUSE"}, 
       ["actual_qty", "reserved_qty", "projected_qty"], 
       as_dict=True)
   ```

3. **Repost Stock** if needed:
   - Go to: Stock > Tools > Repost Item Valuation
   - Select item and warehouse
   - Submit

---

### Issue 6: Temperature Deviation Handling

**Symptoms**:
- Unsure how to handle out-of-range temperature
- Inspection Result not auto-setting
- Goods not quarantined

**Solutions**:
1. **If Temperature Out-of-Range**:
   - Data Logger Present: Yes
   - Temperature Range Status: Out-of-Range
   - Choose Action:
     - **Quarantine**: Inspection Result auto-sets to "Quarantined"
     - **Accept with Reason**: Must provide detailed justification

2. **Quarantine Process**:
   - Set Rejected Warehouse
   - Goods automatically moved to Rejected Warehouse
   - QA team notified
   - Requires QA approval to release

3. **Accept with Reason**:
   - Enter detailed reason in Acceptance Reason field
   - Document who approved acceptance
   - Attach supporting documentation
   - Proceed with normal flow

---

### Issue 7: Shipment Status Not Updating

**Symptoms**:
- Shipment status stuck at "Draft" or "In Progress"
- Milestones checked but status not changing

**Causes**:
1. Not all milestones completed
2. Status field manually changed
3. Validation preventing update

**Solutions**:
1. **Check all milestones**:
   - ☑ Arrived
   - ☑ Bank Authenticated
   - ☑ Restricted Release Status
   - ☑ Customs Release Status
   - ☑ Received at Warehouse

2. **Status auto-calculates**:
   - All milestones = "Completed"
   - Some milestones = "In Progress"
   - No milestones = "Draft"

3. **Cannot manually change status** - it's system-controlled

---

## Deployment Guide

### Prerequisites
- ERPNext v15.x installed
- Frappe Framework v15.x
- Python 3.10+
- MariaDB 10.6+

### Installation Steps

#### 1. Install Onco App
```bash
cd ~/frappe-bench
bench get-app https://github.com/your-repo/onco.git
bench --site [your-site] install-app onco
```

#### 2. Run Migrations
```bash
bench --site [your-site] migrate
```

This will:
- Create all custom doctypes
- Add custom fields to standard doctypes
- Set up hooks
- Configure permissions

#### 3. Clear Cache
```bash
bench --site [your-site] clear-cache
```

#### 4. Restart Services
```bash
bench restart
```

#### 5. Verify Installation
```bash
bench --site [your-site] console
```

```python
# Check if doctypes exist
frappe.db.exists("DocType", "Incoming Check Report")
frappe.db.exists("DocType", "Purchase Receipt Report")
frappe.db.exists("DocType", "Printing Order")
frappe.db.exists("DocType", "Authority Good Release")

# Check custom fields
frappe.get_meta("Stock Entry").get_field("custom_purchase_receipt")
frappe.get_meta("Stock Entry").get_field("custom_shipment_ref")
```

---

### Configuration

#### 1. Set Up Warehouses
Create these warehouses in: **Stock > Warehouse**

Required Warehouses:
- Imported Finished Phr Receipt and Inspection Warehouse - Onco
- Imported Finished Phr Unreleased Warehouse (Oncopharm) - Onco
- Rejected Warehouse - Onco
- Imported Finished Phr Sales warehouse - Onco
- Imported Finished Phr Sample warehouse - Onco

#### 2. Configure Permissions
Go to: **Setup > Permissions > Role Permissions Manager**

Set permissions for:
- Incoming Check Report
- Purchase Receipt Report
- Printing Order
- Authority Good Release

#### 3. Set Up Email
Configure email for notifications:
- Go to: **Setup > Email > Email Account**
- Set up SMTP settings
- Test email sending

#### 4. Configure Naming Series
Go to: **Setup > Settings > Naming Series**

Set naming series for:
- Incoming Check Report: ICR-YYYY-#####
- Purchase Receipt Report: PRR-YYYY-#####
- Printing Order: PO-YYYY-#####
- Authority Good Release: AGR-YYYY-#####

---

### Testing

#### 1. Create Test Data
```python
# Create test item
item = frappe.get_doc({
    "doctype": "Item",
    "item_code": "TEST-ITEM-001",
    "item_name": "Test Pharmaceutical Item",
    "item_group": "Products",
    "stock_uom": "Nos",
    "has_batch_no": 1,
    "create_new_batch": 1
})
item.insert()

# Create test supplier
supplier = frappe.get_doc({
    "doctype": "Supplier",
    "supplier_name": "Test Pharma Supplier",
    "supplier_group": "Pharmaceutical"
})
supplier.insert()
```

#### 2. Run Test Workflow
Follow the complete workflow from Step 1 to Step 12 with test data

#### 3. Verify Results
- Check all documents created
- Verify stock balances
- Check all references linked
- Verify automatic processes worked

---

### Backup and Recovery

#### Backup
```bash
# Backup database
bench --site [your-site] backup

# Backup with files
bench --site [your-site] backup --with-files
```

#### Restore
```bash
# Restore database
bench --site [your-site] restore [backup-file]
```

---

### Monitoring

#### Check System Health
```bash
# Check bench status
bench status

# Check logs
tail -f ~/frappe-bench/logs/[site].log
```

#### Monitor Performance
- Go to: **Setup > System Settings**
- Enable "Track Function Calls"
- Monitor slow queries

#### Error Monitoring
- Regularly check: **Setup > Error Log**
- Set up email alerts for errors
- Monitor failed background jobs

---

## Appendix

### Glossary

**EDA**: Egyptian Drug Authority  
**IMAR**: Import Authorization  
**SPIMR**: Special Importation Approval Request  
**APIMR**: Annual Importation Approval Request  
**COA**: Certificate of Analysis  
**COO**: Certificate of Origin  
**GMP**: Good Manufacturing Practice  
**QA**: Quality Assurance  
**AGR**: Authority Good Release  
**ICR**: Incoming Check Report  
**PRR**: Purchase Receipt Report  

---

### Support

For technical support:
- Email: support@oncopharma.com
- Documentation: https://docs.oncopharma.com
- ERPNext Forum: https://discuss.erpnext.com

---

### Version History

**v1.0 - February 2026**
- Initial release
- Complete importation cycle implementation
- Incoming Check Report with auto stock movements
- Purchase Receipt Report integration
- Printing Order and Authority Good Release
- Comprehensive documentation

---

**End of Documentation**
