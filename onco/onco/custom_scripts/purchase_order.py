# Copyright (c) 2026, Onco and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def validate(doc, method):
	"""
	Validate Purchase Order against Importation Approval quantities
	Ensures that cumulative ordered quantities don't exceed approved quantities
	"""
	if not doc.custom_importation_approval:
		return
	
	# Get the Importation Approval document
	try:
		approval_doc = frappe.get_doc("Importation Approvals", doc.custom_importation_approval)
	except frappe.DoesNotExistError:
		frappe.throw(_("Importation Approval {0} does not exist").format(doc.custom_importation_approval))
		return
	
	# Check each item in the Purchase Order
	for po_item in doc.items:
		# Find the corresponding item in the Importation Approval
		approval_item = None
		for appr_item in approval_doc.items:
			if appr_item.item_code == po_item.item_code:
				approval_item = appr_item
				break
		
		if not approval_item:
			frappe.throw(
				_("Item {0} is not in the Importation Approval {1}").format(
					po_item.item_code,
					doc.custom_importation_approval
				)
			)
		
		# Calculate cumulative ordered quantity for this item
		# Get all submitted Purchase Orders linked to this Importation Approval (excluding current PO)
		cumulative_ordered = get_cumulative_ordered_qty(
			doc.custom_importation_approval,
			po_item.item_code,
			exclude_po=doc.name if doc.docstatus == 1 else None
		)
		
		# Add current PO item quantity
		total_ordered = cumulative_ordered + po_item.qty
		
		# Check if total ordered exceeds approved quantity
		if total_ordered > approval_item.approved_qty:
			frappe.throw(
				_("Item {0}: Total ordered quantity ({1}) exceeds approved quantity ({2}). "
				  "Already ordered: {3}, Current order: {4}, Approved: {5}").format(
					po_item.item_code,
					total_ordered,
					approval_item.approved_qty,
					cumulative_ordered,
					po_item.qty,
					approval_item.approved_qty
				)
			)
		
		# Set the importation approval reference on the item
		po_item.custom_importation_approval = doc.custom_importation_approval


def on_submit(doc, method):
	"""
	Update ordered quantities in Importation Approval when Purchase Order is submitted
	"""
	if not doc.custom_importation_approval:
		return
	
	update_importation_approval_quantities(doc.custom_importation_approval)


def on_cancel(doc, method):
	"""
	Update ordered quantities in Importation Approval when Purchase Order is cancelled
	"""
	if not doc.custom_importation_approval:
		return
	
	update_importation_approval_quantities(doc.custom_importation_approval)


def get_cumulative_ordered_qty(importation_approval, item_code, exclude_po=None):
	"""
	Get the cumulative ordered quantity for an item across all Purchase Orders
	linked to the Importation Approval
	
	Args:
		importation_approval (str): Name of the Importation Approval document
		item_code (str): Item code to check
		exclude_po (str, optional): Purchase Order name to exclude from calculation
	
	Returns:
		float: Cumulative ordered quantity
	"""
	filters = {
		"custom_importation_approval": importation_approval,
		"item_code": item_code,
		"docstatus": 1  # Only submitted Purchase Orders
	}
	
	if exclude_po:
		filters["parent"] = ["!=", exclude_po]
	
	result = frappe.db.sql("""
		SELECT SUM(qty) as total_qty
		FROM `tabPurchase Order Item`
		WHERE custom_importation_approval = %(importation_approval)s
		AND item_code = %(item_code)s
		AND docstatus = 1
		{exclude_clause}
	""".format(
		exclude_clause="AND parent != %(exclude_po)s" if exclude_po else ""
	), {
		"importation_approval": importation_approval,
		"item_code": item_code,
		"exclude_po": exclude_po
	}, as_dict=True)
	
	return result[0].total_qty or 0 if result else 0


def update_importation_approval_quantities(importation_approval_name):
	"""
	Update the ordered_qty and remaining_qty fields in Importation Approval items
	
	Args:
		importation_approval_name (str): Name of the Importation Approval document
	"""
	try:
		approval_doc = frappe.get_doc("Importation Approvals", importation_approval_name)
		
		for item in approval_doc.items:
			# Calculate cumulative ordered quantity
			cumulative_ordered = get_cumulative_ordered_qty(
				importation_approval_name,
				item.item_code
			)
			
			# Update ordered_qty and remaining_qty
			item.ordered_qty = cumulative_ordered
			item.remaining_qty = item.approved_qty - cumulative_ordered
		
		# Save the document (bypass validation to avoid recursion)
		approval_doc.flags.ignore_validate = True
		approval_doc.flags.ignore_mandatory = True
		approval_doc.save()
		
		frappe.msgprint(
			_("Importation Approval {0} quantities updated").format(importation_approval_name),
			alert=True,
			indicator='green'
		)
		
	except Exception as e:
		frappe.log_error(
			message=f"Failed to update Importation Approval quantities: {str(e)}",
			title="Purchase Order - Update Importation Approval Failed"
		)
		# Don't throw error here, just log it
