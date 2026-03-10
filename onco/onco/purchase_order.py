# Copyright (c) 2025, ds and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate
from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder


class CustomPurchaseOrder(PurchaseOrder):
	"""
	Custom Purchase Order class to override autoname method
	Format: PO-YYYY-XXXXX
	- YYYY: Year from transaction_date (or schedule_date if transaction_date is not set)
	- XXXXX: Sequential count of POs in that year (5 digits, year-specific counter)
	"""
	
	def autoname(self):
		"""
		Custom autoname method for Purchase Order with year-based naming
		Format: PO-YYYY-XXXXX
		"""
		# Get the year from transaction_date field (or schedule_date as fallback)
		date_field = self.transaction_date or self.schedule_date
		if not date_field:
			frappe.throw(_("Transaction Date or Schedule Date is required for Purchase Order naming."))
		
		year = getdate(date_field).year
		
		# Get the next counter for this year
		counter = self.get_next_counter(year)
		
		# Generate name in format: PO-{YYYY}-{XXXXX}
		# Example: PO-2020-00001, PO-2024-00001
		self.name = f"PO-{year}-{counter:05d}"
	
	def get_next_counter(self, year):
		"""Get auto-incremented counter for naming series specific to year"""
		# Query Purchase Order documents with name like "PO-{year}-%"
		existing = frappe.get_all(
			"Purchase Order",
			filters={
				"name": ["like", f"PO-{year}-%"]
			},
			fields=["name"],
			order_by="name desc",
			limit=1
		)
		
		if existing:
			# Extract counter from name (format: PO-YYYY-XXXXX)
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
