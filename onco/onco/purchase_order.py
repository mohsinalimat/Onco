# Copyright (c) 2025, ds and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate
from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder


class CustomPurchaseOrder(PurchaseOrder):
	"""
	Custom Purchase Order class to override autoname method
	Format: 
	- Local: PO-LOC-YYYY-#####
	- Imported: PO-IMP-YYYY-#####
	"""
	
	def autoname(self):
		"""
		Custom autoname method for Purchase Order with local/imported distinction
		Format: PO-LOC-YYYY-##### or PO-IMP-YYYY-#####
		"""
		# Get the year from transaction_date field (or schedule_date as fallback)
		date_field = self.transaction_date or self.schedule_date
		if not date_field:
			frappe.throw(_("Transaction Date or Schedule Date is required for Purchase Order naming."))
		
		year = getdate(date_field).year
		
		# Determine if this is local or imported purchase
		# Check custom_purchase_order_type or custom_importation_approval
		is_imported = False
		
		if self.custom_purchase_order_type == "Imported Purchase":
			is_imported = True
		elif self.custom_importation_approval:
			is_imported = True
		elif self.custom_purchase_order_type == "Local Purchase":
			is_imported = False
		else:
			# Default to local if not specified
			is_imported = False
		
		# Set prefix based on type
		prefix = "PO-IMP" if is_imported else "PO-LOC"
		
		# Get the next counter for this prefix and year
		counter = self.get_next_counter(prefix, year)
		
		# Generate name in format: PO-LOC-YYYY-##### or PO-IMP-YYYY-#####
		# Examples: PO-LOC-2026-00001, PO-IMP-2026-00001
		self.name = f"{prefix}-{year}-{counter:05d}"
	
	def get_next_counter(self, prefix, year):
		"""Get auto-incremented counter for naming series specific to prefix and year"""
		# Query Purchase Order documents with name like "{prefix}-{year}-%"
		existing = frappe.get_all(
			"Purchase Order",
			filters={
				"name": ["like", f"{prefix}-{year}-%"]
			},
			fields=["name"],
			order_by="name desc",
			limit=1
		)
		
		if existing:
			# Extract counter from name (format: PO-LOC-YYYY-##### or PO-IMP-YYYY-#####)
			# Counter is the last component after splitting by "-"
			parts = existing[0].name.split("-")
			if len(parts) >= 4:
				try:
					# Get the last part which should be the counter
					last_counter = int(parts[-1])
					return last_counter + 1
				except ValueError:
					# If counter is not a valid integer, start from 1
					pass
		
		# Return 1 if no existing documents or extraction failed
		return 1
