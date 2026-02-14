# Copyright (c) 2026, ds and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import _

class PurchaseReceiptReport(Document):
	def validate(self):
		"""Validate Purchase Receipt Report before save/submit"""
		if not self.items or len(self.items) == 0:
			frappe.throw(_("Cannot save Purchase Receipt Report without items. Please add at least one item."))
		
		# Validate that we have a purchase receipt reference
		if not self.purchase_receipt:
			frappe.msgprint(
				_("Warning: No Purchase Receipt linked. This may cause issues in downstream processes."),
				indicator='orange',
				title=_('Missing Purchase Receipt')
			)

@frappe.whitelist()
def make_printing_order(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.date = frappe.utils.nowdate()
		# Carry over Shipment No
		if source.custom_shipment_ref:
			target.shipment_no = source.custom_shipment_ref
		
	doc = get_mapped_doc("Purchase Receipt Report", source_name, {
		"Purchase Receipt Report": {
			"doctype": "Printing Order",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Purchase Receipt Report Item": {
			"doctype": "Printing Order Item",
			"field_map": {
				"accepted_qty": "qty_in_stock",
				"item_code": "item_code", 
				"item_name": "item_name",
				"batch_no": "batch_no",
				"expiry_date": "expiry_date"
			}
		}
	}, target_doc, set_missing_values)
	return doc

@frappe.whitelist()
def make_purchase_receipt_report(source_name, target_doc=None):
	doc = get_mapped_doc("Purchase Receipt", source_name, {
		"Purchase Receipt": {
			"doctype": "Purchase Receipt Report",
			"validation": {
				"docstatus": ["=", 1]
			},
			"field_map": {
				"custom_shipment_ref": "custom_shipment_ref"
			}
		},
		"Purchase Receipt Item": {
			"doctype": "Purchase Receipt Report Item",
			"field_map": {
				"qty": "received_qty", 
				"item_code": "item_code",
				"item_name": "item_name",
				"batch_no": "batch_no"
			}
		}
	}, target_doc)
	return doc
