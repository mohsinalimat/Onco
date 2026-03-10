# Copyright (c) 2026, Onco and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ImportationApprovals(Document):
    def autoname(self):
        """Generate naming series based on approval type with year from date field"""
        if not self.approval_type:
            frappe.throw(_("Approval Type is required for naming"))
        
        # Get year from the date field (not posting date)
        if not self.date:
            frappe.throw(_("Date is required for naming"))
        
        year = frappe.utils.getdate(self.date).year
        
        # Determine prefix based on approval type and modification/extension status
        base_prefix = ""
        if self.approval_type == 'Special Importation (SPIMA)':
            base_prefix = "EDA-SPIMA"
        elif self.approval_type == 'Annual Importation (APIMA)':
            base_prefix = "EDA-APIMA"
        else:
            frappe.throw(_("Invalid Approval Type: {0}").format(self.approval_type))
        
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
        # - EDA-SPIMA-2020-00001 (normal)
        # - EDA-SPIMA-MD-2020-00001 (modification)
        # - EDA-APIMA-EX-2024-00001 (extension)
        self.name = f"{prefix}-{year}-{counter:05d}"
    
    def get_next_counter(self, prefix, year):
        """Get auto-incremented counter for naming series specific to year"""
        # Query Importation Approvals documents with name like "{prefix}-{year}-%"
        existing = frappe.get_all(
            "Importation Approvals",
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
        self.validate_items_table()
        self.validate_approval_quantities()
    
    def validate_items_table(self):
        """Ensure items table is not empty and populated from request if needed"""
        if not self.items and self.importation_approval_request:
            # Auto-populate items from the linked request
            self.fetch_request_data()
        
        if not self.items:
            if self.importation_approval_request:
                frappe.throw("No items found in the linked Importation Approval Request. Please check the request document.")
            else:
                frappe.throw("Items table cannot be empty. Please link an Importation Approval Request.")
    
    def fetch_request_data(self):
        """Fetch data from linked Importation Approval Request"""
        if not self.importation_approval_request:
            return
            
        request_doc = frappe.get_doc("Importation Approval Request", self.importation_approval_request)
        
        if not request_doc.items:
            return
        
        # Clear existing items and add all items from request
        self.items = []
        
        for request_item in request_doc.items:
            self.append("items", {
                "item_code": request_item.item_code,
                "item_name": request_item.item_name,
                "supplier": request_item.supplier,
                "requested_qty": request_item.requested_qty,
                # As per HTML: "QUANTIY: AUTIMATICALLY FROM PERVIOUS STEP"
                "approved_qty": request_item.approved_qty,
                "status": "Approved"
            })
    
    def validate_approval_quantities(self):
        """Validate that approval quantities match the request"""
        if not self.importation_approval_request:
            return
            
        request_doc = frappe.get_doc("Importation Approval Request", self.importation_approval_request)
        
        for item in self.items:
            # Find corresponding item in request
            request_item = None
            for req_item in request_doc.items:
                if req_item.item_code == item.item_code:
                    request_item = req_item
                    break
            
            if not request_item:
                frappe.throw(f"Item {item.item_code} not found in the original request")
            
            if item.approved_qty > request_item.requested_qty:
                frappe.throw(f"Approved quantity for {item.item_code} cannot exceed requested quantity")
    
    def on_submit(self):
        """Create approval record and enable further actions"""
        # Check if this is an extension/modification of a closed document
        if self.original_document:
            original_doc = frappe.get_doc("Importation Approvals", self.original_document)
            if original_doc.docstatus == 2:  # Cancelled/Closed
                frappe.msgprint("Original document has been closed. This is the new active approval.")
        
        frappe.msgprint("Importation Approval created successfully. You can now create Purchase Orders, Modifications, or Extensions.")
    
    def before_submit(self):
        """Validate before submission"""
        # Prevent submission if this is not the latest version
        if self.original_document:
            # Check if there are newer versions
            newer_versions = frappe.get_all("Importation Approvals", 
                filters={
                    "original_document": self.original_document,
                    "creation": [">", self.creation],
                    "docstatus": ["!=", 2]
                })
            if newer_versions:
                frappe.throw("Cannot submit - newer version exists. Please use the latest version.")
    
    def validate_purchase_order_creation(self):
        """Validate if Purchase Order can be created from this document"""
        if self.docstatus != 1:
            frappe.throw("Document must be submitted before creating Purchase Order")
        
        # Check if document is closed due to modification/extension
        if self.docstatus == 2:
            frappe.throw("Cannot create Purchase Order from closed document. Use the latest version.")
        
        return True
    
    def validate_approval_quantities(self):
        """Validate that approval quantities match the request"""
        if not self.importation_approval_request:
            return
            
        request_doc = frappe.get_doc("Importation Approval Request", self.importation_approval_request)
        
        for item in self.items:
            # Find corresponding item in request
            request_item = None
            for req_item in request_doc.items:
                if req_item.item_code == item.item_code:
                    request_item = req_item
                    break
            
            if not request_item:
                frappe.throw(f"Item {item.item_code} not found in the original request")
            
            if item.approved_qty > request_item.requested_qty:
                frappe.throw(f"Approved quantity for {item.item_code} cannot exceed requested quantity")

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
    """Create Purchase Order from Importation Approvals"""
    from frappe.model.mapper import get_mapped_doc
    
    # Validate that Purchase Order can be created
    source_doc = frappe.get_doc("Importation Approvals", source_name)
    source_doc.validate_purchase_order_creation()
    
    def set_missing_values(source, target):
        target.custom_importation_approval = source.name  # Fixed: use correct field name
        target.custom_purchase_order_type = "Imported Purchase"
        target.custom_purchase_type = "Finished Products Item"
        
        # Ensure company is set (required for currency/pricing)
        if not target.company:
            target.company = frappe.db.get_default("company") or "ONCOPHARM EGYPT S.A.E"
            
        # Set supplier and currency
        if source.items:
            target.supplier = source.items[0].supplier
            if target.supplier:
                target.currency = frappe.db.get_value("Supplier", target.supplier, "default_currency")
        
        if not target.currency:
            target.currency = frappe.db.get_value("Company", target.company, "default_currency") or "EGP"
        
        # Set conversion rate (1.0 if same currency, otherwise fetch from exchange rate)
        company_currency = frappe.db.get_value("Company", target.company, "default_currency") or "EGP"
        if target.currency == company_currency:
            target.conversion_rate = 1.0
        else:
            # Try to get exchange rate
            from erpnext.setup.utils import get_exchange_rate
            target.conversion_rate = get_exchange_rate(target.currency, company_currency, target.transaction_date or frappe.utils.nowdate())
            
        target.transaction_date = frappe.utils.nowdate()
        
        # Send email notification to supplier if enabled
        if source.send_email_notification and target.supplier:
            custom_email = source.supplier_email if source.supplier_email else None
            send_supplier_notification(target.supplier, source.name, custom_email)
    
    def update_item(source, target, source_parent):
        target.item_code = source.item_code
        target.qty = source.approved_qty
        
        # Set importation approval reference on the item for quantity tracking
        target.custom_importation_approval = source_parent.name
        
        # Fetch item details to avoid 'Infinity' and bad tax templates
        from erpnext.stock.get_item_details import get_item_details
        # Try to find company from parent or defaults
        company = frappe.db.get_default("company") or "ONCOPHARM EGYPT S.A.E"
        
        # Get supplier and currency
        supplier = source.supplier or (source_parent.supplier if hasattr(source_parent, "supplier") else None)
        currency = None
        if supplier:
            currency = frappe.db.get_value("Supplier", supplier, "default_currency")
        if not currency:
            currency = frappe.db.get_value("Company", company, "default_currency") or "EGP"
        
        # Calculate conversion rate
        company_currency = frappe.db.get_value("Company", company, "default_currency") or "EGP"
        conversion_rate = 1.0
        if currency != company_currency:
            from erpnext.setup.utils import get_exchange_rate
            conversion_rate = get_exchange_rate(currency, company_currency, frappe.utils.nowdate()) or 1.0
        
        # Get a valid warehouse for the company (optional - can be set later)
        warehouse = frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")
        
        args = frappe._dict({
            "item_code": source.item_code,
            "company": company,
            "qty": target.qty,
            "transaction_date": frappe.utils.nowdate(),
            "doctype": "Purchase Order",
            "supplier": supplier,
            "currency": currency,
            "conversion_rate": conversion_rate,
            "warehouse": warehouse  # Pass valid warehouse or None
        })
        item_details = get_item_details(args)
        
        target.uom = item_details.get("uom")
        target.stock_uom = item_details.get("stock_uom")
        target.conversion_factor = item_details.get("conversion_factor") or 1.0
        target.item_tax_template = item_details.get("item_tax_template")
        target.rate = item_details.get("price_list_rate") or item_details.get("last_purchase_rate") or 0
        target.schedule_date = frappe.utils.nowdate()
        
        # Set warehouse from item details if available, otherwise leave empty for user to set
        if item_details.get("warehouse"):
            target.warehouse = item_details.get("warehouse")
    
    doclist = get_mapped_doc("Importation Approvals", source_name, {
        "Importation Approvals": {
            "doctype": "Purchase Order",
            "field_map": {
                "name": "custom_importation_approval"  # Fixed: use correct field name
            }
        },
        "Importation Approvals Item": {
            "doctype": "Purchase Order Item",
            "postprocess": update_item
        }
    }, target_doc, set_missing_values)
    
    return doclist

def send_supplier_notification(supplier, approval_reference, custom_email=None):
    """Send email notification to supplier about Purchase Order creation"""
    try:
        supplier_doc = frappe.get_doc("Supplier", supplier)
        email_to_send = custom_email or supplier_doc.email_id
        
        if email_to_send:
            frappe.sendmail(
                recipients=[email_to_send],
                subject=f"Purchase Order Created - Reference: {approval_reference}",
                message=f"""
                Dear {supplier_doc.supplier_name},
                
                A Purchase Order has been created based on Importation Approval: {approval_reference}
                
                Please check your portal for details.
                
                Best regards,
                Onco Pharma Team
                """,
                header="Purchase Order Notification"
            )
            frappe.msgprint(f"Email notification sent to {email_to_send}")
        else:
            frappe.msgprint("No email address found for supplier notification")
    except Exception as e:
        frappe.log_error(f"Failed to send supplier notification: {str(e)}")
        # Don't fail the PO creation if email fails

@frappe.whitelist()
def create_modification(source_name, modification_reason, requested_modification=None, new_conditions=None):
    """Create modification of Importation Approvals"""
    source_doc = frappe.get_doc("Importation Approvals", source_name)
    
    # Create new approval
    new_doc = frappe.copy_doc(source_doc)
    
    # Set modification flag - autoname will handle the naming
    new_doc.is_modification = 1
    new_doc.modification_reason = modification_reason
    new_doc.original_document = source_name
    new_doc.special_conditions = new_conditions or new_doc.special_conditions
    
    # Insert will trigger autoname() which will generate the correct name
    # Format: EDA-SPIMA-MD-{YEAR}-{COUNTER} or EDA-APIMA-MD-{YEAR}-{COUNTER}
    new_doc.insert()
    
    # Close original document to prevent further Purchase Orders
    source_doc.db_set('docstatus', 2)  # Cancel the original
    frappe.db.commit()
    
    return new_doc.name

@frappe.whitelist()
def create_extension(source_name, extension_reason, extension_details, new_validation_date, new_quantity=None):
    """Create extension of Importation Approvals"""
    source_doc = frappe.get_doc("Importation Approvals", source_name)
    
    # Create new approval
    new_doc = frappe.copy_doc(source_doc)
    
    # Set extension flag - autoname will handle the naming
    new_doc.is_extension = 1
    new_doc.extension_reason = extension_reason
    new_doc.valid_date = new_validation_date
    new_doc.original_document = source_name
    
    # Update quantities if provided
    if new_quantity:
        for item in new_doc.items:
            item.approved_qty = new_quantity
    
    # Insert will trigger autoname() which will generate the correct name
    # Format: EDA-SPIMA-EX-{YEAR}-{COUNTER} or EDA-APIMA-EX-{YEAR}-{COUNTER}
    new_doc.insert()
    
    # Close original document to prevent further Purchase Orders
    source_doc.db_set('docstatus', 2)  # Cancel the original
    frappe.db.commit()
    
    return new_doc.name