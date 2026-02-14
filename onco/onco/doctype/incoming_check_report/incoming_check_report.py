# Copyright (c) 2026, Onco and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class IncomingCheckReport(Document):
    def validate(self):
        self.validate_stock_entry()
        self.fetch_reference_data()
        self.fetch_inspection_warehouse()
        self.calculate_quantities()
        self.validate_inspection_completion()
        self.validate_warehouse_assignment()
        self.update_status()
    
    def validate_stock_entry(self):
        """Validate that Stock Entry exists and is submitted"""
        if not self.stock_entry:
            frappe.throw(_("Stock Entry is required"))
        
        stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
        if stock_entry.docstatus != 1:
            frappe.throw(_("Stock Entry must be submitted before creating Incoming Check Report"))
    
    def fetch_inspection_warehouse(self):
        """Fetch inspection warehouse from Stock Entry's to_warehouse field"""
        if self.stock_entry and not self.inspection_warehouse:
            # Fetch to_warehouse from Stock Entry (target warehouse)
            to_warehouse = frappe.db.get_value("Stock Entry", self.stock_entry, "to_warehouse")
            if to_warehouse:
                self.inspection_warehouse = to_warehouse
    
    def fetch_reference_data(self):
        """Fetch all reference data from Stock Entry chain"""
        if not self.stock_entry:
            return
        
        # Get Purchase Receipt from Stock Entry custom field
        stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
        purchase_receipt = stock_entry.get("custom_purchase_receipt")
        
        if not purchase_receipt:
            frappe.msgprint(
                _("Warning: No Purchase Receipt linked to this Stock Entry. Some data may not be available.<br><br>"
                  "To fix this issue:<br>"
                  "1. Go to the Stock Entry and manually set the 'Purchase Receipt' field, OR<br>"
                  "2. Ensure the Stock Entry was created from a Purchase Receipt using the standard ERPNext flow"),
                indicator='orange',
                title=_('Missing Purchase Receipt Link')
            )
            return
        
        self.purchase_receipt = purchase_receipt
        
        # Get Shipment from Purchase Receipt
        shipment = frappe.db.get_value("Purchase Receipt", purchase_receipt, "custom_shipment_ref")
        if shipment:
            self.shipment = shipment
        
        # Get Purchase Invoice from Purchase Receipt items
        pr_items = frappe.get_all("Purchase Receipt Item",
            filters={"parent": purchase_receipt},
            fields=["purchase_invoice"],
            limit=1
        )
        if pr_items and pr_items[0].purchase_invoice:
            self.purchase_invoice = pr_items[0].purchase_invoice
            
            # Get Importation Approval from Purchase Invoice
            importation_approval = frappe.db.get_value(
                "Purchase Invoice",
                self.purchase_invoice,
                "custom_importation_approval"
            )
            if importation_approval:
                self.importation_approval = importation_approval
    
    def calculate_quantities(self):
        """Calculate accepted, shortage, and damage quantities"""
        total_invoice = 0
        total_received = 0
        total_over = 0
        total_damage = 0
        total_accepted = 0
        total_shortage = 0
        
        for item in self.items:
            # Calculate shortage quantity
            item.shortage_quantity = max(0, (item.invoice_quantity or 0) - (item.received_quantity or 0))
            
            # Calculate accepted quantity
            item.accepted_quantity = (
                (item.received_quantity or 0) - 
                (item.damage_quantity or 0) - 
                (item.over_quantity or 0)
            )
            
            # Ensure accepted quantity is not negative
            if item.accepted_quantity < 0:
                item.accepted_quantity = 0
            
            # Sum totals
            total_invoice += item.invoice_quantity or 0
            total_received += item.received_quantity or 0
            total_over += item.over_quantity or 0
            total_damage += item.damage_quantity or 0
            total_accepted += item.accepted_quantity or 0
            total_shortage += item.shortage_quantity or 0
        
        # Update parent totals
        self.total_invoice_qty = total_invoice
        self.total_received_qty = total_received
        self.total_over_qty = total_over
        self.total_damage_qty = total_damage
        self.total_accepted_qty = total_accepted
        self.total_shortage_qty = total_shortage
    
    def validate_inspection_completion(self):
        """Ensure all required inspections are completed"""
        # Temperature control validation
        if self.data_logger_present == 'Yes':
            if not self.temperature_range_status:
                frappe.throw(_("Temperature Range Status is required when Data Logger is present"))
            
            if self.temperature_range_status == 'Out-of-Range':
                if not self.out_of_range_action:
                    frappe.throw(_("Out-of-range action is required when temperature is out of range"))
                
                if self.out_of_range_action == 'Accept with Reason':
                    if not self.acceptance_reason:
                        frappe.throw(_("Acceptance reason is required when accepting out-of-range temperature"))
        
        # Ensure inspection result is set
        if not self.inspection_result:
            frappe.throw(_("Inspection Result is required before submission"))
    
    def validate_warehouse_assignment(self):
        """Validate warehouse based on inspection result"""
        if self.inspection_result == 'Passed':
            if not self.accepted_warehouse:
                frappe.throw(_("Accepted Warehouse is required when inspection passes"))
        elif self.inspection_result in ['Failed', 'Quarantined']:
            if not self.rejected_warehouse:
                frappe.throw(_("Rejected Warehouse is required when inspection fails or goods are quarantined"))
    
    def update_status(self):
        """Update status based on inspection result"""
        if self.inspection_result == 'Passed':
            self.status = 'Inspection Passed'
        elif self.inspection_result == 'Failed':
            self.status = 'Inspection Failed'
        elif self.inspection_result == 'Quarantined':
            self.status = 'Quarantined'
        else:
            self.status = 'Draft'
    
    def on_submit(self):
        """Send notifications, update related documents, and create stock entries"""
        # Send email notification if requested
        if self.send_shipment_receipt_notification:
            self.send_notification_email()
        
        # Update Shipment status if linked
        if self.shipment:
            frappe.db.set_value('Shipments', 
                self.shipment, 
                'custom_inspection_status', 
                self.inspection_result)
            frappe.db.set_value('Shipments',
                self.shipment,
                'custom_inspection_date',
                self.inspection_date)
        
        # Create Stock Entries based on inspection results
        self.create_stock_entries_for_inspection()
    
    def send_notification_email(self):
        """Send inspection report to supplier"""
        try:
            if not self.purchase_invoice:
                return
            
            # Get supplier from Purchase Invoice
            supplier = frappe.db.get_value("Purchase Invoice", self.purchase_invoice, "supplier")
            if not supplier:
                return
            
            supplier_doc = frappe.get_doc("Supplier", supplier)
            
            # Use custom email if provided, otherwise use supplier's email
            email_to_send = self.notification_email or supplier_doc.email_id
            
            if not email_to_send:
                frappe.msgprint(_("No email address found for supplier notification"))
                return
            
            # Prepare email content
            subject = _("Shipment Inspection Report - {0}").format(self.name)
            
            message = f"""
            <p>Dear {supplier_doc.supplier_name},</p>
            
            <p>The shipment inspection has been completed for your shipment.</p>
            
            <h3>Inspection Details:</h3>
            <ul>
                <li><strong>Inspection Report:</strong> {self.name}</li>
                <li><strong>Inspection Date:</strong> {self.inspection_date}</li>
                <li><strong>Shipment:</strong> {self.shipment or 'N/A'}</li>
                <li><strong>Purchase Invoice:</strong> {self.purchase_invoice or 'N/A'}</li>
                <li><strong>Inspection Result:</strong> {self.inspection_result}</li>
            </ul>
            
            <h3>Quantity Summary:</h3>
            <ul>
                <li><strong>Total Received:</strong> {self.total_received_qty}</li>
                <li><strong>Total Accepted:</strong> {self.total_accepted_qty}</li>
                <li><strong>Total Damaged:</strong> {self.total_damage_qty}</li>
                <li><strong>Total Over:</strong> {self.total_over_qty}</li>
            </ul>
            
            <p><strong>Status:</strong> {self.status}</p>
            
            {f'<p><strong>Remarks:</strong> {self.remarks}</p>' if self.remarks else ''}
            
            <p>Best regards,<br/>
            Onco Pharma Quality Control Team</p>
            """
            
            frappe.sendmail(
                recipients=[email_to_send],
                subject=subject,
                message=message,
                header=_("Shipment Inspection Report")
            )
            
            frappe.msgprint(_("Email notification sent to {0}").format(email_to_send))
            
        except Exception as e:
            frappe.log_error(f"Failed to send inspection notification: {str(e)}")
            frappe.msgprint(_("Failed to send email notification. Error logged."))
    
    def create_stock_entries_for_inspection(self):
        """Create Stock Entries to move goods based on inspection results"""
        if not self.inspection_warehouse:
            frappe.throw(_("Inspection Warehouse is required to create stock entries"))
        
        # Separate items by inspection result
        accepted_items = []
        rejected_items = []
        
        for item in self.items:
            # Add accepted quantity items
            if item.accepted_quantity and item.accepted_quantity > 0:
                accepted_items.append({
                    'item_code': item.item_code,
                    'qty': item.accepted_quantity,
                    'batch_no': item.batch_no,
                    'item_name': item.item_name
                })
            
            # Add damaged/rejected quantity items
            damage_qty = (item.damage_quantity or 0) + (item.over_quantity or 0)
            if damage_qty > 0:
                rejected_items.append({
                    'item_code': item.item_code,
                    'qty': damage_qty,
                    'batch_no': item.batch_no,
                    'item_name': item.item_name
                })
        
        # Create Stock Entry for accepted items
        if accepted_items and self.accepted_warehouse:
            accepted_se = self.create_stock_entry(
                items=accepted_items,
                target_warehouse=self.accepted_warehouse,
                purpose="Material Transfer",
                remarks=f"Accepted items from Incoming Check Report {self.name}"
            )
            if accepted_se:
                frappe.msgprint(
                    _("Stock Entry {0} created for accepted items").format(accepted_se.name),
                    alert=True,
                    indicator='green'
                )
        
        # Create Stock Entry for rejected/damaged items
        if rejected_items and self.rejected_warehouse:
            rejected_se = self.create_stock_entry(
                items=rejected_items,
                target_warehouse=self.rejected_warehouse,
                purpose="Material Transfer",
                remarks=f"Rejected/Damaged items from Incoming Check Report {self.name}"
            )
            if rejected_se:
                frappe.msgprint(
                    _("Stock Entry {0} created for rejected/damaged items").format(rejected_se.name),
                    alert=True,
                    indicator='orange'
                )
    
    def create_stock_entry(self, items, target_warehouse, purpose, remarks):
        """Create a Stock Entry document"""
        try:
            stock_entry = frappe.new_doc("Stock Entry")
            stock_entry.purpose = purpose
            stock_entry.stock_entry_type = "Material Transfer"
            stock_entry.from_warehouse = self.inspection_warehouse
            stock_entry.to_warehouse = target_warehouse
            stock_entry.posting_date = frappe.utils.today()
            stock_entry.posting_time = frappe.utils.nowtime()
            stock_entry.set_posting_time = 1
            stock_entry.custom_purchase_receipt = self.purchase_receipt
            stock_entry.custom_shipment_ref = self.shipment
            
            # Add reference to Incoming Check Report
            stock_entry.add_comment('Comment', f'Created from Incoming Check Report: {self.name}')
            
            # Add items
            for item_data in items:
                stock_entry.append("items", {
                    "item_code": item_data['item_code'],
                    "item_name": item_data.get('item_name'),
                    "qty": item_data['qty'],
                    "s_warehouse": self.inspection_warehouse,
                    "t_warehouse": target_warehouse,
                    "batch_no": item_data.get('batch_no'),
                    "transfer_qty": item_data['qty'],
                    "uom": frappe.db.get_value("Item", item_data['item_code'], "stock_uom")
                })
            
            stock_entry.insert()
            stock_entry.submit()
            
            return stock_entry
            
        except Exception as e:
            frappe.log_error(
                message=f"Failed to create Stock Entry from Incoming Check Report {self.name}: {str(e)}",
                title="Incoming Check Report - Stock Entry Creation Failed"
            )
            frappe.msgprint(
                _("Failed to create Stock Entry: {0}").format(str(e)),
                alert=True,
                indicator='red'
            )
            return None


@frappe.whitelist()
def make_incoming_check_report(source_name, target_doc=None):
    """Create Incoming Check Report from Stock Entry"""
    from frappe.model.mapper import get_mapped_doc
    
    def set_missing_values(source, target):
        # Fetch inspection warehouse from Stock Entry's to_warehouse
        target.inspection_warehouse = source.to_warehouse
        target.inspection_date = frappe.utils.today()
        
        # Get Purchase Receipt from Stock Entry custom field OR from items
        purchase_receipt = source.get("custom_purchase_receipt")
        
        # If not found in custom field, check Stock Entry items
        if not purchase_receipt and source.items:
            for item in source.items:
                if item.get("purchase_receipt"):
                    purchase_receipt = item.purchase_receipt
                    break
        
        if not purchase_receipt:
            frappe.msgprint(
                _("Warning: No Purchase Receipt linked to this Stock Entry. Some data may not be available."),
                indicator='orange',
                title=_('Missing Purchase Receipt')
            )
        
        # Get Shipment reference - try multiple sources
        shipment_no = None
        purchase_invoice = None
        
        if purchase_receipt:
            # Set Purchase Receipt on parent
            target.purchase_receipt = purchase_receipt
            
            # Get Shipment reference from Purchase Receipt
            shipment_no = frappe.db.get_value("Purchase Receipt", purchase_receipt, "custom_shipment_ref")
            if shipment_no:
                target.shipment = shipment_no
            
            # Get Purchase Invoice from Purchase Receipt items
            pr_items = frappe.get_all("Purchase Receipt Item",
                filters={"parent": purchase_receipt},
                fields=["purchase_invoice"],
                limit=1
            )
            if pr_items and pr_items[0].purchase_invoice:
                purchase_invoice = pr_items[0].purchase_invoice
                target.purchase_invoice = purchase_invoice
        
        # Also check Stock Entry custom_shipment_ref field
        if not shipment_no and source.get("custom_shipment_ref"):
            shipment_no = source.custom_shipment_ref
            target.shipment = shipment_no
        
        # Fetch items from Stock Entry and populate
        if source.items:
            target.items = []
            for se_item in source.items:
                # Get item details
                item_code = se_item.item_code
                batch_no = se_item.batch_no
                received_qty = se_item.qty
                
                # Get item name from Item master
                item_name = frappe.db.get_value("Item", item_code, "item_name")
                
                # Get invoice quantity from Purchase Receipt (the actual receipt document)
                invoice_qty = received_qty  # Default to received qty
                invoice_no = purchase_receipt  # Reference the Purchase Receipt
                
                if purchase_receipt:
                    # Find matching item in Purchase Receipt to get the original ordered quantity
                    pr_item = frappe.db.get_value(
                        "Purchase Receipt Item",
                        {
                            "parent": purchase_receipt,
                            "item_code": item_code
                        },
                        ["qty"],
                        as_dict=True
                    )
                    if pr_item:
                        invoice_qty = pr_item.qty
                
                # Get batch details if batch exists
                manufacturing_date = None
                expiry_date = None
                if batch_no:
                    batch_details = frappe.db.get_value(
                        "Batch",
                        batch_no,
                        ["manufacturing_date", "expiry_date"],
                        as_dict=True
                    )
                    if batch_details:
                        manufacturing_date = batch_details.manufacturing_date
                        expiry_date = batch_details.expiry_date
                
                # Calculate shortage
                shortage_qty = max(0, invoice_qty - received_qty)
                
                # Add item to Incoming Check Report with shipment and purchase receipt references
                target.append("items", {
                    "item_code": item_code,
                    "item_name": item_name,
                    "batch_no": batch_no,
                    "shipment_no": shipment_no,  # This will populate the child table
                    "invoice_no": invoice_no,    # This is the Purchase Receipt reference
                    "invoice_quantity": invoice_qty,
                    "received_quantity": received_qty,
                    "shortage_quantity": shortage_qty,
                    "over_quantity": 0,
                    "damage_quantity": 0,
                    "accepted_quantity": received_qty,
                    "manufacturing_date": manufacturing_date,
                    "expiry_date": expiry_date
                })
    
    doclist = get_mapped_doc("Stock Entry", source_name, {
        "Stock Entry": {
            "doctype": "Incoming Check Report",
            "field_map": {
                "name": "stock_entry",
                "custom_purchase_receipt": "purchase_receipt",
                "custom_shipment_ref": "shipment"
            }
        }
    }, target_doc, set_missing_values)
    
    return doclist


@frappe.whitelist()
def make_purchase_receipt_report(source_name, target_doc=None):
    """Create Purchase Receipt Report from Incoming Check Report"""
    from frappe.model.mapper import get_mapped_doc
    
    # Validate source document
    source_doc = frappe.get_doc("Incoming Check Report", source_name)
    
    if source_doc.docstatus != 1:
        frappe.throw(_("Incoming Check Report must be submitted before creating Purchase Receipt Report"))
    
    if not source_doc.items or len(source_doc.items) == 0:
        frappe.throw(_("Incoming Check Report has no items to map"))
    
    def set_missing_values(source, target):
        # Map inspection check fields
        # Vehicle Inspection
        if source.seal_numbers:
            target.seal_numbers_match = 1 if source.seal_integrity_verified else 0
        
        if source.temperature_recorder_status:
            target.temp_recorder_status = source.temperature_recorder_status
        
        # Document Check
        target.invoice_present = 1 if source.commercial_invoice_present else 0
        target.packing_list_present = 1 if source.packing_list_present else 0
        target.awb_present = 1 if source.bill_of_lading_present else 0
        target.coa_present = 1 if source.certificate_of_analysis_present else 0
        
        # Physical Check
        target.seal_integrity = 1 if source.seal_integrity_verified else 0
        target.package_condition = 1 if source.package_condition_ok else 0
        target.label_verification = 1 if source.labels_verified else 0
        target.quantity_verification = 1 if source.quantity_verified else 0
        
        # Temperature Control
        target.data_logger_present = 1 if source.data_logger_present == 'Yes' else 0
        
        if source.temperature_range_status == 'Out-of-Range':
            target.out_of_range = 1
            if source.out_of_range_action == 'Quarantine and Notify QA':
                target.quarantine_notify = 1
            if source.acceptance_reason:
                target.accept_reason = source.acceptance_reason
        
        # Validate that items were mapped
        if not target.items or len(target.items) == 0:
            frappe.throw(_("Failed to map items from Incoming Check Report to Purchase Receipt Report"))
    
    doclist = get_mapped_doc("Incoming Check Report", source_name, {
        "Incoming Check Report": {
            "doctype": "Purchase Receipt Report",
            "field_map": {
                "purchase_receipt": "purchase_receipt",
                "shipment": "custom_shipment_ref"
            }
        },
        "Incoming Check Report Item": {
            "doctype": "Purchase Receipt Report Item",
            "field_map": {
                "shipment_no": "shipment_no",
                "invoice_no": "invoice_no",
                "item_code": "item_code",
                "item_name": "item_name",
                "batch_no": "batch_no",
                "invoice_quantity": "invoice_qty",
                "received_quantity": "received_qty",
                "damage_quantity": "damage_qty",
                "over_quantity": "over_qty",
                "accepted_quantity": "accepted_qty",
                "manufacturing_date": "manufacturing_date",
                "expiry_date": "expiry_date"
            }
        }
    }, target_doc, set_missing_values)
    
    return doclist


def validate_inspection_before_downstream(doctype_name, docname):
    """
    Validate that inspection passed before allowing downstream processes
    Called from Purchase Receipt Report, Printing Order, Authority Good Release
    """
    # Get Purchase Receipt from the document
    purchase_receipt = frappe.db.get_value(doctype_name, docname, "purchase_receipt")
    
    if not purchase_receipt:
        return  # No validation needed if no purchase receipt linked
    
    # Check if Incoming Check Report exists for this Purchase Receipt
    incoming_check = frappe.db.get_value(
        "Incoming Check Report",
        {"purchase_receipt": purchase_receipt, "docstatus": 1},
        ["name", "inspection_result", "status"],
        as_dict=True
    )
    
    if incoming_check:
        if incoming_check.inspection_result in ['Failed', 'Quarantined']:
            frappe.throw(_(
                "Cannot create {0}. Inspection failed or goods are quarantined. "
                "Incoming Check Report: {1}, Status: {2}"
            ).format(doctype_name, incoming_check.name, incoming_check.status))
