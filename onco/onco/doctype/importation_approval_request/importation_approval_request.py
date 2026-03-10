# Copyright (c) 2026, Onco and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ImportationApprovalRequest(Document):
    def autoname(self):
        """Generate naming series based on request type with year from date field"""
        if not self.request_type:
            frappe.throw(_("Request Type is required for naming"))
        
        # Get year from the date field (not posting date)
        if not self.date:
            frappe.throw(_("Date is required for naming"))
        
        year = frappe.utils.getdate(self.date).year
        
        # Determine prefix based on request type and modification/extension status
        base_prefix = ""
        if self.request_type == 'Special Importation (SPIMR)':
            base_prefix = "EDA-SPIMR"
        elif self.request_type == 'Annual Importation (APIMR)':
            base_prefix = "EDA-APIMR"
        else:
            frappe.throw(_("Invalid Request Type: {0}").format(self.request_type))
        
        # Add suffix for modifications or extensions
        if self.is_modification:
            prefix = f"{base_prefix}-MD"
        elif self.is_extension:
            prefix = f"{base_prefix}-EX"
        else:
            prefix = base_prefix
        
        # Get the next counter for this prefix and year combination
        counter = self.get_next_counter(prefix, year)
        
        # Generate name in format: {PREFIX}-{YYYY}-{XXXXX}
        # Examples: 
        # - EDA-SPIMR-2020-00001 (normal)
        # - EDA-SPIMR-MD-2020-00001 (modification)
        # - EDA-APIMR-EX-2024-00001 (extension)
        self.name = f"{prefix}-{year}-{counter:05d}"
    
    def get_next_counter(self, prefix, year):
        """Get auto-incremented counter for naming series specific to year"""
        # Query Importation Approval Request documents with name like "{prefix}-{year}-%"
        existing = frappe.get_all(
            "Importation Approval Request",
            filters={
                "name": ["like", f"{prefix}-{year}-%"]
            },
            fields=["name"],
            order_by="name desc",
            limit=1
        )
        
        if existing:
            # Extract counter from name (format: PREFIX-YYYY-XXXXX)
            # Counter is the last component after splitting by "-"
            parts = existing[0].name.split("-")
            if len(parts) >= 3:
                try:
                    # Get the last part which should be the counter
                    last_counter = int(parts[-1])
                    return last_counter + 1
                except ValueError:
                    # If counter is not a valid integer, start from 1
                    pass
        
        # Return 1 if no existing documents or extraction failed
        return 1
    
    def validate(self):
        self.calculate_totals()
        self.validate_approval_quantities()
        
        # "After Saving Status Pending" - Auto-set status to Pending on save if not set
        if not self.status or self.status == "":
            self.status = "Pending"
    
    def calculate_totals(self):
        """Calculate total requested and approved quantities"""
        total_requested = 0
        total_approved = 0
        
        for item in self.items:
            total_requested += item.requested_qty or 0
            total_approved += item.approved_qty or 0
        
        self.total_requested_qty = total_requested
        self.total_approved_qty = total_approved
    
    def validate_approval_quantities(self):
        """Validate that approved quantities don't exceed requested quantities"""
        for item in self.items:
            if item.approved_qty and item.approved_qty > item.requested_qty:
                frappe.throw(f"Approved quantity for {item.item_code} cannot exceed requested quantity")
    
    def on_submit(self):
        """On submit, keep status as Pending unless explicitly approved/refused"""
        # Status remains "Pending" after submission
        # Use the "Approve Request" or "Refuse Request" buttons to change status
        pass

# Whitelisted methods must be at module level (not inside class)
@frappe.whitelist()
def approve_request(docname, approval_type="Totally Approved", items_data=None):
    """Approve the importation approval request
    
    Args:
        docname: Name of the Importation Approval Request
        approval_type: Type of approval (Totally Approved, Partially Approved, Refused)
        items_data: JSON string of item codes and their approved quantities (for reuse in Partial Approval)
    """
    import json
    doc = frappe.get_doc("Importation Approval Request", docname)
    
    if doc.docstatus != 1:
        frappe.throw("Document must be submitted before approval")
    
    # Parse items_data if provided
    approved_quantities = {}
    if items_data:
        if isinstance(items_data, str):
            approved_quantities = json.loads(items_data)
        else:
            approved_quantities = items_data

    # Set approval status and date
    doc.db_set('approval_status', approval_type, update_modified=False)
    doc.db_set('approval_date', frappe.utils.today(), update_modified=False)
    doc.db_set('status', approval_type, update_modified=False)
    
    total_approved = 0
    
    # Update item statuses based on quantities
    for item in doc.items:
        # Determine approved qty based on type
        new_approved_qty = 0
        
        if approval_type == 'Refused':
            new_approved_qty = 0
        elif approval_type == 'Totally Approved':
            new_approved_qty = item.requested_qty
        elif approval_type == 'Partially Approved':
            # Use provided data or fall back to existing/0
            if item.item_code in approved_quantities:
                new_approved_qty = approved_quantities[item.item_code]
            else:
                # If not in data, assume 0 for partial approval safety? 
                # Or keep existing? Let's assume 0 if not explicitly approved in the dialog.
                new_approved_qty = 0
        
        # Update the item's approved quantity in DB
        frappe.db.set_value('Importation Approval Request Item', item.name, 'approved_qty', new_approved_qty, update_modified=False)
        
        # Update item status
        item_status = ''
        if new_approved_qty == 0:
            item_status = 'Refused'
        elif new_approved_qty == item.requested_qty:
            item_status = 'Totally Approved'
        else:
            item_status = 'Partially Approved'
            
        frappe.db.set_value('Importation Approval Request Item', item.name, 'status', item_status, update_modified=False)
        
        total_approved += new_approved_qty

    # Update total approved qty on parent
    doc.db_set('total_approved_qty', total_approved, update_modified=False)
    
    frappe.msgprint(f"Request has been marked as {approval_type}")
    
    return doc.name

@frappe.whitelist()
def make_importation_approval(source_name, target_doc=None):
    """Create Importation Approval from Importation Approval Request"""
    from frappe.model.mapper import get_mapped_doc
    
    def set_missing_values(source, target):
        # Set approval type based on request type
        if source.request_type == 'Special Importation (SPIMR)':
            target.approval_type = 'Special Importation (SPIMA)'
            target.naming_series = 'EDA-SPIMA-.YYYY.-.#####'
        elif source.request_type == 'Annual Importation (APIMR)':
            target.approval_type = 'Annual Importation (APIMA)'
            target.naming_series = 'EDA-APIMA-.YYYY.-.#####'
            
        # Explicitly clear original_document to avoid LinkValidationError
        target.original_document = None
    
    def update_item(source, target, source_parent):
        # Map all item fields and set approved_qty to approved_qty from request
        target.requested_qty = source.requested_qty
        target.approved_qty = source.approved_qty  # Set to the actual approved quantity
        target.supplier = source.supplier  # Explicitly carry over supplier
        target.status = "Approved"
    
    doclist = get_mapped_doc("Importation Approval Request", source_name, {
        "Importation Approval Request": {
            "doctype": "Importation Approvals",
            "field_map": {
                "name": "importation_approval_request",
                "original_document": None  # Prevent mapping incompatible types
            }
        },
        "Importation Approval Request Item": {
            "doctype": "Importation Approvals Item",
            "postprocess": update_item
        }
    }, target_doc, set_missing_values)
    
    return doclist

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
    """Create Purchase Order from Importation Approval Request"""
    from frappe.model.mapper import get_mapped_doc
    
    def set_missing_values(source, target):
        if not target.company:
            target.company = frappe.db.get_default("company") or "ONCOPHARM EGYPT S.A.E"
            
        target.supplier = source.items[0].supplier if source.items else None
        
        if target.supplier:
            target.currency = frappe.db.get_value("Supplier", target.supplier, "default_currency")
            
        if not target.currency:
            target.currency = frappe.db.get_value("Company", target.company, "default_currency") or "EGP"
            
        target.transaction_date = frappe.utils.nowdate()
        target.custom_importation_approval_request = source.name # Link back if needed

    def update_item(source, target, source_parent):
        target.item_code = source.item_code
        target.qty = source.approved_qty if source.approved_qty > 0 else source.requested_qty
        
        # Fetch item details to avoid 'Infinity' and bad tax templates
        from erpnext.stock.get_item_details import get_item_details
        company = frappe.db.get_default("company") or "ONCOPHARM EGYPT S.A.E"
        
        args = frappe._dict({
            "item_code": source.item_code,
            "company": company,
            "qty": target.qty,
            "transaction_date": frappe.utils.nowdate(),
            "doctype": "Purchase Order",
            "supplier": source.supplier or None
        })
        item_details = get_item_details(args)
        
        target.uom = item_details.get("uom")
        target.stock_uom = item_details.get("stock_uom")
        target.conversion_factor = item_details.get("conversion_factor") or 1.0
        target.item_tax_template = item_details.get("item_tax_template")
        target.rate = item_details.get("price_list_rate") or item_details.get("last_purchase_rate") or 0
        target.schedule_date = frappe.utils.nowdate()
    doclist = get_mapped_doc("Importation Approval Request", source_name, {
        "Importation Approval Request": {
            "doctype": "Purchase Order",
            "field_map": {
                "name": "custom_importation_approval_ref" # Check field name
            }
        },
        "Importation Approval Request Item": {
            "doctype": "Purchase Order Item",
            "postprocess": update_item
        }
    }, target_doc, set_missing_values)
    
    return doclist

@frappe.whitelist()
def create_modification(source_name, modification_reason, requested_modification, items_to_modify=None):
    """Create modification of Importation Approval Request"""
    import json
    
    source_doc = frappe.get_doc("Importation Approval Request", source_name)
    
    # Create new request
    new_doc = frappe.copy_doc(source_doc)
    
    # Set modification flag - autoname will handle the naming
    new_doc.is_modification = 1
    new_doc.modification_reason = modification_reason
    new_doc.original_document = source_name
    new_doc.status = "Pending"
    
    # Clear approval data for new modification
    new_doc.approval_status = ""
    new_doc.approval_date = ""
    new_doc.total_approved_qty = 0
    
    # If specific items to modify are provided, update them
    if items_to_modify:
        items_data = json.loads(items_to_modify) if isinstance(items_to_modify, str) else items_to_modify
        for item in new_doc.items:
            if item.item_code in items_data:
                item.requested_qty = items_data[item.item_code].get('new_qty', item.requested_qty)
            item.approved_qty = 0
            item.status = "Pending"
    else:
        for item in new_doc.items:
            item.approved_qty = 0
            item.status = "Pending"
    
    # Insert will trigger autoname() which will generate the correct name
    # Format: EDA-SPIMR-MD-{YEAR}-{COUNTER} or EDA-APIMR-MD-{YEAR}-{COUNTER}
    new_doc.insert()
    
    # Close original document
    source_doc.db_set('status', 'Closed - Modified')
    
    return new_doc.name

@frappe.whitelist()
def create_extension(source_name, extension_reason, extension_details, new_validation_date=None, additional_qty=None):
    """Create extension of Importation Approval Request"""
    import json
    
    source_doc = frappe.get_doc("Importation Approval Request", source_name)
    
    # Create new request
    new_doc = frappe.copy_doc(source_doc)
    
    # Set extension flag - autoname will handle the naming
    new_doc.is_extension = 1
    new_doc.extension_reason = extension_reason
    new_doc.original_document = source_name
    new_doc.status = "Pending"
    
    # Clear approval data
    new_doc.approval_status = ""
    new_doc.approval_date = ""
    new_doc.total_approved_qty = 0
    
    if additional_qty:
        qty_data = json.loads(additional_qty) if isinstance(additional_qty, str) else additional_qty
        for item in new_doc.items:
            if item.item_code in qty_data:
                additional = qty_data[item.item_code].get('additional_qty', 0)
                item.requested_qty = item.requested_qty + additional
            item.approved_qty = 0
            item.status = "Pending"
    else:
        for item in new_doc.items:
            item.approved_qty = 0
            item.status = "Pending"
    
    # Insert will trigger autoname() which will generate the correct name
    # Format: EDA-SPIMR-EX-{YEAR}-{COUNTER} or EDA-APIMR-EX-{YEAR}-{COUNTER}
    new_doc.insert()
    
    # Close original document
    source_doc.db_set('status', 'Closed - Extended')
    
    return new_doc.name