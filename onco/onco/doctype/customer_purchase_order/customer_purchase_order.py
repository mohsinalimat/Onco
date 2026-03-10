# Copyright (c) 2025, ds and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class CustomerPurchaseOrder(Document):
	def autoname(self):
		"""Generate naming series based on order type with year from date field"""
		if not self.order_type:
			frappe.throw(_("Order Type is required for naming"))
		
		# Get year from the date field (not current date)
		if not self.date:
			frappe.throw(_("Date is required for naming"))
		
		year = frappe.utils.getdate(self.date).year
		
		# Determine prefix based on order type
		prefix_map = {
			'Private Direct Order': 'CPO-PRV-DIR',
			'Private Tenders Order': 'CPO-PRV-TEN',
			'UPA Tender Order': 'CPO-UPA-TEN',
			'UPA Direct Order': 'CPO-UPA-DIR',
			'UPA Distributor Order': 'CPO-UPA-DIS'
		}
		
		prefix = prefix_map.get(self.order_type)
		if not prefix:
			frappe.throw(_("Invalid Order Type: {0}").format(self.order_type))
		
		# Get the next counter for this prefix and year combination
		counter = self.get_next_counter(prefix, year)
		
		# Generate name in format: {PREFIX}-{YYYY}-{XXXXX}-{customer_purchase_order_number}
		# Examples: 
		# - CPO-PRV-DIR-2020-00001-PO123
		# - CPO-UPA-TEN-2024-00001-PO456
		base_name = f"{prefix}-{year}-{counter:05d}"
		
		# Append customer purchase order number if provided
		if self.customer_purchase_order_number:
			self.name = f"{base_name}-{self.customer_purchase_order_number}"
		else:
			self.name = base_name
	
	def get_next_counter(self, prefix, year):
		"""Get auto-incremented counter for naming series specific to year"""
		# Query Customer Purchase Order documents with name like "{prefix}-{year}-%"
		existing = frappe.get_all(
			"Customer Purchase Order",
			filters={
				"name": ["like", f"{prefix}-{year}-%"]
			},
			fields=["name"],
			order_by="name desc",
			limit=1
		)
		
		if existing:
			# Extract counter from name (format: PREFIX-YYYY-XXXXX or PREFIX-YYYY-XXXXX-PONUM)
			# Counter is after the year part
			parts = existing[0].name.split("-")
			if len(parts) >= 4:
				try:
					# The counter should be the 4th part (index 3)
					# Example: CPO-PRV-DIR-2020-00001-PO123
					#          [0] [1] [2] [3]  [4]   [5]
					last_counter = int(parts[3])
					return last_counter + 1
				except (ValueError, IndexError):
					# If counter is not a valid integer, start from 1
					pass
		
		# Return 1 if no existing documents or extraction failed
		return 1
