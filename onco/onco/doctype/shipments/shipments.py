# Copyright (c) 2025, ds and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.model.document import Document
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice as _make_purchase_invoice
class Shipments(Document):
    def autoname(self):
        """
        Generate naming series based on mode of shipping and AWB/SWB number
        Format: SHIP-IMP-AWB-{AWB_NUMBER} or SHIP-IMP-SWB-{SWB_NUMBER}
        """
        if not self.mode_of_shipping:
            frappe.throw(_("Mode of Shipping is required for naming"))
        
        if self.mode_of_shipping == "Air freight":
            if not self.awb_no:
                frappe.throw(_("AWB No is required for Air freight shipments"))
            self.name = f"SHIP-IMP-AWB-{self.awb_no}"
        elif self.mode_of_shipping == "Sea freight":
            if not self.swb_no:
                frappe.throw(_("SWB No is required for Sea freight shipments"))
            self.name = f"SHIP-IMP-SWB-{self.swb_no}"
        else:
            frappe.throw(_("Invalid Mode of Shipping: {0}").format(self.mode_of_shipping))
    
    def validate(self):
        self.validate_status_sequence()
        self.calculate_milestone_completion()
    
    def before_submit(self):
        """Validate before submission"""
        # Validation removed - invoice data is present
        pass
    
    def validate_status_sequence(self):
        """Prevent users from manually changing status field - Enhanced validation"""
        if self.is_new():
            return
        
        # Get the old doc to compare
        old_doc = self.get_doc_before_save()
        if old_doc and old_doc.status != self.status:
            # Check if status was changed manually (not by calculate_milestone_completion)
            # We allow the change if it's being set by the system
            if not self.flags.get('status_updated_by_system'):
                frappe.throw(_("Status cannot be changed manually. It is automatically updated based on milestone completion."))
    
    def before_save(self):
        """Additional validation to prevent status field manipulation"""
        # Ensure status field cannot be set via form or API unless by system
        if not self.is_new() and not self.flags.get('status_updated_by_system'):
            old_doc = self.get_doc_before_save()
            if old_doc and old_doc.status != self.status:
                # Revert to old status if changed manually
                self.status = old_doc.status

    def calculate_milestone_completion(self):
        steps = [
            self.arrived,
            self.bank_authenticated,
            self.restricted_release_status,
            self.customs_release_status,
            self.received_at_warehouse
        ]
        # Set flag to allow status update by system
        self.flags.status_updated_by_system = True
        
        if all(steps):
            self.status = "Completed"
        elif any(steps):
            self.status = "In Progress"


    def on_submit(self):
        """Update status when shipment is submitted"""
        pass  # Stock transfer is created from Authority Good Release, not from Shipments

@frappe.whitelist()
def set_shipment_id(purchase_inv,ship):
    if ship:
        # Assuming 'ship' is the name or ID of the shipment
        try:
            invoice = frappe.get_doc("Purchase Invoice", purchase_inv)
            invoice.db_set("custom_shipments",ship)
            invoice.db_set("custom_is_shiped",1)
            return invoice
        except frappe.DoesNotExistError:
            frappe.throw(_("Purchase Invoice not found"))
        except Exception as e:
            frappe.throw(str(e))
@frappe.whitelist()
def get_shipment(purchase_invoice,rec):
    invoice = frappe.get_doc("Purchase Invoice", purchase_invoice)
    ship_id = invoice.get("custom_shipments")
    print(f"Shipment\n\n\n{ship_id}")
    shipment = frappe.get_doc("Shipments", ship_id)
    if not shipment:
        frappe.throw(f"No shipment data")
    return shipment
@frappe.whitelist()
def set_shipment(doc_shipments, rec):
    try:
        if isinstance(rec, str): 
            receipt = json.loads(rec)
            shipments = json.loads(doc_shipments)
        else:
            receipt = rec  
        return shipments
    
    except Exception as e:
        frappe.throw(str(e))

from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_purchase_receipt(source_name, target_doc=None):
	doc = frappe.get_doc("Shipments", source_name)
	
	# Collect all items from the Purchase Invoices child table
	if not doc.custom_invoices or len(doc.custom_invoices) == 0:
		frappe.throw("Please link at least one Purchase Invoice with items first")

	# Group items by invoice to get unique invoices
	invoices_dict = {}
	for row in doc.custom_invoices:
		if row.purchase_invoice:
			if row.purchase_invoice not in invoices_dict:
				invoices_dict[row.purchase_invoice] = []
			invoices_dict[row.purchase_invoice].append(row)
	
	invoices = list(invoices_dict.keys())
	
	if not invoices:
		frappe.throw("No valid Purchase Invoices found in the child table")

	def set_missing_values(source, target):
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")
		# Link Shipment
		target.custom_shipment_ref = source_name

	# Map the first invoice to create the target doc
	target_doc = get_mapped_doc("Purchase Invoice", invoices[0], {
		"Purchase Invoice": {
			"doctype": "Purchase Receipt",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Purchase Invoice Item": {
			"doctype": "Purchase Receipt Item",
		},
	}, target_doc, set_missing_values)

	# Clear the items and rebuild from our child table data
	target_doc.items = []
	
	# Add all items from all invoices based on the child table
	for inv_name in invoices:
		items_for_invoice = invoices_dict[inv_name]
		for item_row in items_for_invoice:
			# Fetch the actual item from Purchase Invoice to get all details
			pi_item = frappe.db.get_value("Purchase Invoice Item", 
				filters={
					"parent": inv_name,
					"item_code": item_row.item_code
				},
				fieldname=["name", "item_code", "item_name", "description", "qty", "uom", 
						   "stock_uom", "conversion_factor", "rate", "purchase_order", 
						   "warehouse", "expense_account", "cost_center", "project"],
				as_dict=True
			)
			
			if pi_item:
				# Check if item has batch tracking enabled
				item_doc = frappe.get_doc("Item", pi_item.item_code)
				
				pr_item = {
					"item_code": pi_item.item_code,
					"item_name": pi_item.item_name,
					"description": pi_item.description,
					"qty": item_row.qty,  # Use qty from child table
					"uom": item_row.uom,
					"stock_uom": pi_item.stock_uom,  # Required field
					"conversion_factor": pi_item.conversion_factor or 1.0,
					"rate": item_row.rate,
					"purchase_order": pi_item.purchase_order,
					"purchase_invoice_item": pi_item.name,
					"purchase_invoice": inv_name,
					"warehouse": doc.source_warehouse or pi_item.warehouse or target_doc.set_warehouse,
					"expense_account": pi_item.expense_account,
					"cost_center": pi_item.cost_center,
					"project": pi_item.project
				}
				
				# Only add batch_no if item has batch tracking and batch is provided
				if item_doc.has_batch_no and item_row.batch_no:
					pr_item["batch_no"] = item_row.batch_no
					pr_item["use_serial_batch_fields"] = 1  # Use legacy batch fields for ERPNext v15
				
				# Add expiry date if provided
				if item_row.expiry_date:
					pr_item["expiry_date"] = item_row.expiry_date
				
				target_doc.append("items", pr_item)
	
	return target_doc

def on_purchase_receipt_submit(doc, method):
	"""Update linked Shipment when Purchase Receipt is submitted"""
	if doc.get("custom_shipment_ref"):
		frappe.db.set_value("Shipments", doc.custom_shipment_ref, {
			"received_at_warehouse": 1,
			"received_date": frappe.utils.now()
		})
		frappe.msgprint(f"Shipment {doc.custom_shipment_ref} status updated to Received at Warehouse.")