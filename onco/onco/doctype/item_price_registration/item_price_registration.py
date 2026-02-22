# Copyright (c) 2026, Onco and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ItemPriceRegistration(Document):
	def validate(self):
		"""
		Ensure only the last row is Active and all others are Archived
		This is called before save
		"""
		if not self.parent or not self.parenttype:
			return
		
		# Get the parent document
		parent_doc = frappe.get_doc(self.parenttype, self.parent)
		
		# Get all price registration rows
		if hasattr(parent_doc, 'custom_price_registration'):
			price_rows = parent_doc.custom_price_registration
			
			# If there are multiple rows, ensure only the last one is Active
			if len(price_rows) > 1:
				# Find the current row index
				current_idx = None
				for idx, row in enumerate(price_rows):
					if row.name == self.name:
						current_idx = idx
						break
				
				# If this is not the last row, set it to Archived
				if current_idx is not None and current_idx < len(price_rows) - 1:
					self.status = "Archived"
				# If this is the last row, set it to Active
				elif current_idx == len(price_rows) - 1:
					self.status = "Active"
					
					# Set all previous rows to Archived
					for idx, row in enumerate(price_rows):
						if idx < current_idx and row.status != "Archived":
							frappe.db.set_value(
								"Item Price Registration",
								row.name,
								"status",
								"Archived",
								update_modified=False
							)

