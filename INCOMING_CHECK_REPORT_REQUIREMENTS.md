# Incoming Check Report - Requirements Analysis

## 📋 WORKFLOW CLARIFICATION

Based on the HTML documentation and your explanation, the **CORRECT** workflow is:

```
Importation Approval Request (EDA-IMAR)
  ↓ Create Importation Approval button
Importation Approvals (EDA-IMA)
  ↓ Create Purchase Order button
Purchase Order (Standard ERPNext)
  ↓ Standard ERPNext workflow
Purchase Invoice (Standard ERPNext)
  ↓ Link to Shipment
Shipments (Existing Custom)
  ↓ Create Purchase Receipt button
Purchase Receipt (Standard ERPNext)
  ↓ **NATIVE ERPNEXT: Auto Stock Entry Creation**
Stock Entry (Standard ERPNext)
  ↓ **NEW DOCTYPE NEEDED**
**Incoming Check Report** (NEW - TO BE CREATED)
  ↓ After inspection approval
Purchase Receipt Report (Existing Custom)
  ↓ Fetch Items button
Printing Order (Existing Custom)
  ↓ After printing
Authority Good Release (Existing Custom - Enhanced)
  ↓ Auto Stock Transfer
Stock Entry (Standard ERPNext)
```

## 🔍 KEY UNDERSTANDING

### Native ERPNext Behavior
- **After Purchase Receipt submission**, ERPNext allows creating a Stock Entry
- This Stock Entry transfers goods from one warehouse to another
- **This is acceptable by the client** ✅

### The Missing Piece: Incoming Check Report
After the Stock Entry is created (from Purchase Receipt), we need a **NEW doctype** called:
- **"Incoming Check Report"** (or "Inspection Check Report")

## 📦 INCOMING CHECK REPORT DOCTYPE

### Purpose
Quality control and inspection report that:
1. Fetches data from Stock Entry
2. Tracks back to Purchase Receipt → Purchase Invoice → Shipments → Importation Approvals
3. Records inspection results (vehicle, documents, physical checks, temperature)
4. Determines if goods are accepted or rejected
5. Sets accepted/rejected warehouses based on inspection results

### Warehouses Involved

**From HTML Documentation:**
1. **Imported Finished Phr Incoming Warehouse - Onco**
   - Initial warehouse when goods arrive (Purchase Receipt)

2. **Imported Finished Phr Receipt and Inspection Warehouse - Onco**
   - Warehouse after Stock Entry (inspection warehouse)
   - This is where Incoming Check Report inspection happens

3. **Accepted Warehouse** (to be configured)
   - Where accepted goods go after passing inspection

4. **Rejected Warehouse** (to be configured)
   - Where rejected/quarantined goods go after failing inspection

### Fields Required

#### Header Fields
- **Naming Series**: Auto-generated
- **Stock Entry Reference**: Link to Stock Entry (mandatory)
- **Purchase Receipt Reference**: Auto-fetched from Stock Entry
- **Shipment Reference**: Auto-fetched from Purchase Receipt
- **Purchase Invoice Reference**: Auto-fetched from Shipment
- **Importation Approval Reference**: Auto-fetched (tracking back to source)
- **Inspection Date**: Date (default: today)
- **Inspector Name**: Data/Link to User
- **Status**: Select (Draft, Inspection Passed, Inspection Failed, Quarantined)

#### Vehicle Inspection Section
- **Seal Numbers**: Data
- **Seal Integrity**: Select (Intact, Broken, Missing)
- **Temperature Recorder Status**: Select (Present, Not Present)

#### Document Check Section (Checkboxes)
- **Commercial Invoice Present**: Check
- **Packing List Present**: Check
- **Bill of Lading/Airway Bill Present**: Check
- **Certificate of Analysis Present**: Check
- **COO & GMP Certificate Present**: Check
- **All Documents Consistent**: Check

#### Physical Check Section (Checkboxes)
- **Seal Integrity Verified**: Check
- **Package Condition OK**: Check (no damage, leaks, broken containers)
- **Labels Verified**: Check (product name, strength, batch, expiry, storage)
- **Quantity Verified**: Check

#### Temperature Control Section
- **Data Logger Present**: Select (Yes, No)
- **Temperature Report**: Attach (if data logger present)
- **Temperature Range Status**: Select (In-Range, Out-of-Range)
- **Out-of-Range Action**: Select (Quarantine and Notify QA, Accept with Reason)
- **Acceptance Reason**: Text (mandatory if accepting out-of-range)

#### Quantity Verification Table (Child Table: Incoming Check Report Item)

| Field | Type | Auto-Fetch From | Editable |
|-------|------|-----------------|----------|
| Shipment No | Link | Shipment | No |
| Invoice No | Data | Purchase Invoice | No |
| Item Name | Link | Item | No |
| Batch No | Data | Stock Entry | No |
| Invoice Quantity | Float | Purchase Invoice | No |
| Received Quantity | Float | Purchase Receipt | No |
| Over Quantity | Float | Calculated | Manual Entry |
| Damage Quantity | Float | - | Manual Entry |
| Accepted Quantity | Float | Calculated | Auto (Received - Damage - Over) |
| Manufacturing Date | Date | Item/Batch | No |
| Expiry Date | Date | Item/Batch | No |
| Total Accepted | Float | Sum | No |
| Total Damage | Float | Sum | No |

#### Warehouse Assignment Section
- **Accepted Warehouse**: Link to Warehouse (mandatory if inspection passed)
- **Rejected Warehouse**: Link to Warehouse (mandatory if inspection failed/quarantined)

#### Notification Section
- **Send Shipment Receipt Notification**: Check
- **Notification Email**: Data (conditional mandatory if notification checked)

#### Actions After Inspection
- **Inspection Result**: Select (Passed, Failed, Quarantined)
- **Remarks**: Text

### Business Logic

#### 1. Auto-Fetch Data Chain
```python
Stock Entry → Purchase Receipt → Shipment → Purchase Invoice → Importation Approvals
```

All reference fields should auto-populate by traversing this chain.

#### 2. Quantity Calculations
```python
Accepted Quantity = Received Quantity - Damage Quantity - Over Quantity
Total Accepted = Sum of all Accepted Quantities
Total Damage = Sum of all Damage Quantities
```

#### 3. Inspection Status Logic
- **If Temperature Out-of-Range AND Action = "Quarantine"**:
  - Status = "Quarantined"
  - Cannot proceed to Purchase Receipt Report
  - Goods moved to Rejected Warehouse

- **If All Checks Pass**:
  - Status = "Inspection Passed"
  - Can proceed to Purchase Receipt Report
  - Goods moved to Accepted Warehouse

- **If Any Physical Check Fails**:
  - Status = "Inspection Failed"
  - Cannot proceed
  - Goods moved to Rejected Warehouse

#### 4. Blocking Logic
**From HTML**: "if chose quarantine and notify QA I can't do any thing"

If Status = "Quarantined" or "Inspection Failed":
- **BLOCK** creation of:
  - Purchase Receipt Report
  - Printing Order
  - Authority Good Release

#### 5. Email Notification
If "Send Shipment Receipt Notification" is checked:
- Send email to supplier with inspection report summary
- Use custom email if provided, otherwise use supplier's default email

### JavaScript Controller Requirements

```javascript
// Auto-fetch data from Stock Entry
frappe.ui.form.on('Incoming Check Report', {
    stock_entry: function(frm) {
        // Fetch Purchase Receipt from Stock Entry
        // Fetch Shipment from Purchase Receipt
        // Fetch Purchase Invoice from Shipment
        // Fetch Importation Approval from Purchase Invoice
        // Populate items table with data
    },
    
    // Calculate quantities
    refresh: function(frm) {
        calculate_totals(frm);
    },
    
    // Show/hide fields based on temperature status
    temperature_range_status: function(frm) {
        if (frm.doc.temperature_range_status === 'Out-of-Range') {
            frm.set_df_property('out_of_range_action', 'reqd', 1);
        }
    },
    
    // Validate inspection before submission
    validate: function(frm) {
        // Check all mandatory inspections completed
        // Validate warehouse assignments based on status
    }
});

// Item table calculations
frappe.ui.form.on('Incoming Check Report Item', {
    received_quantity: function(frm, cdt, cdn) {
        calculate_accepted_quantity(frm, cdt, cdn);
    },
    damage_quantity: function(frm, cdt, cdn) {
        calculate_accepted_quantity(frm, cdt, cdn);
    },
    over_quantity: function(frm, cdt, cdn) {
        calculate_accepted_quantity(frm, cdt, cdn);
    }
});
```

### Python Controller Requirements

```python
class IncomingCheckReport(Document):
    def validate(self):
        self.validate_stock_entry()
        self.fetch_reference_data()
        self.calculate_quantities()
        self.validate_inspection_completion()
        self.validate_warehouse_assignment()
    
    def fetch_reference_data(self):
        """Fetch all reference data from Stock Entry chain"""
        # Get Purchase Receipt from Stock Entry
        # Get Shipment from Purchase Receipt
        # Get Purchase Invoice from Shipment
        # Get Importation Approval from Purchase Invoice
    
    def calculate_quantities(self):
        """Calculate accepted and damage quantities"""
        for item in self.items:
            item.accepted_quantity = (
                item.received_quantity - 
                item.damage_quantity - 
                item.over_quantity
            )
    
    def validate_inspection_completion(self):
        """Ensure all required inspections are completed"""
        if self.temperature_range_status == 'Out-of-Range':
            if not self.out_of_range_action:
                frappe.throw("Out-of-range action is required")
            if self.out_of_range_action == 'Accept with Reason':
                if not self.acceptance_reason:
                    frappe.throw("Acceptance reason is required")
    
    def validate_warehouse_assignment(self):
        """Validate warehouse based on inspection result"""
        if self.inspection_result == 'Passed':
            if not self.accepted_warehouse:
                frappe.throw("Accepted warehouse is required")
        elif self.inspection_result in ['Failed', 'Quarantined']:
            if not self.rejected_warehouse:
                frappe.throw("Rejected warehouse is required")
    
    def on_submit(self):
        """Send notifications and update status"""
        if self.send_shipment_receipt_notification:
            self.send_notification_email()
        
        # Update Shipment status if needed
        if self.shipment_reference:
            frappe.db.set_value('Shipments', 
                self.shipment_reference, 
                'inspection_status', 
                self.inspection_result)
    
    def send_notification_email(self):
        """Send inspection report to supplier"""
        # Implementation similar to Importation Approvals email logic
```

## 🔗 INTEGRATION POINTS

### 1. Stock Entry Enhancement
Add custom button to Stock Entry:
```javascript
// In Stock Entry custom script
if (frm.doc.docstatus === 1 && frm.doc.purpose === 'Material Transfer') {
    frm.add_custom_button(__('Create Incoming Check Report'), function() {
        frappe.model.open_mapped_doc({
            method: "onco.onco.doctype.incoming_check_report.incoming_check_report.make_incoming_check_report",
            frm: frm
        });
    });
}
```

### 2. Purchase Receipt Report Enhancement
Add validation to prevent creation if inspection failed:
```python
def validate(self):
    # Check if Incoming Check Report exists and passed
    if self.purchase_receipt:
        incoming_check = frappe.db.get_value('Incoming Check Report',
            {'purchase_receipt_reference': self.purchase_receipt},
            ['name', 'inspection_result'])
        
        if incoming_check:
            if incoming_check[1] in ['Failed', 'Quarantined']:
                frappe.throw("Cannot create Purchase Receipt Report. Inspection failed or goods quarantined.")
```

### 3. Shipments Doctype Enhancement
Add field:
- **inspection_status**: Data (updated by Incoming Check Report)

## 📊 NAMING SERIES

Suggested naming series:
- **ICR-.YYYY.-.#####** (Incoming Check Report)
- Or: **INSP-CHK-.YYYY.-.#####**

## ✅ IMPLEMENTATION CHECKLIST

- [ ] Create Incoming Check Report doctype JSON
- [ ] Create Incoming Check Report Item child table JSON
- [ ] Implement Python controller with all validations
- [ ] Implement JavaScript controller with auto-fetch logic
- [ ] Add custom button to Stock Entry
- [ ] Add validation to Purchase Receipt Report
- [ ] Add inspection_status field to Shipments
- [ ] Configure warehouses in ERPNext
- [ ] Test complete workflow
- [ ] Test blocking logic for failed inspections
- [ ] Test email notifications

## 🎯 CRITICAL REQUIREMENTS

1. **Data Traceability**: Must trace back to Importation Approval Request
2. **Blocking Logic**: Failed inspections MUST block downstream processes
3. **Warehouse Management**: Proper warehouse assignment based on inspection result
4. **Quality Control**: All inspection checks must be completed before submission
5. **Email Notifications**: Optional supplier notification with report details

## 📝 NOTES

- This doctype is **NOT currently implemented** in the system
- It fills the gap between Stock Entry and Purchase Receipt Report
- It's a critical quality control checkpoint
- The client accepts the native ERPNext Stock Entry step
- This is the inspection/quality control layer after goods are received
