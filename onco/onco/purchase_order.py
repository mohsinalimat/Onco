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
		Format: PO-LOC-YYYY-XXXX-ZZZ or PO-IMP-YYYY-XXXX-ZZZ
		- XXXX: Sequential count of POs in that year for this prefix (4 digits)
		- ZZZ: Count of how many times this item has appeared in any PO (3 digits)
		"""
		# Validate that there is at least one item
		if not self.items or len(self.items) == 0:
			frappe.throw(_("Purchase Order must contain at least one item."))
		
		# Get the item code from the first item
		item_code = self.items[0].item_code
		if not item_code:
			frappe.throw(_("Item code is required in Purchase Order items."))
		
		# Get the year from transaction_date field (or schedule_date as fallback)
		date_field = self.transaction_date or self.schedule_date
		if not date_field:
			frappe.throw(_("Transaction Date or Schedule Date is required for Purchase Order naming."))
		
		year = getdate(date_field).year
		
		# Determine if this is local or imported purchase
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
		year_counter = self.get_next_counter(prefix, year)
		
		# Get the item counter (how many times this item has appeared in any PO)
		item_counter = self.get_item_counter(item_code)
		
		# Generate name in format: PO-LOC-YYYY-XXXX-ZZZ or PO-IMP-YYYY-XXXX-ZZZ
		# Examples: PO-LOC-2026-0001-001, PO-IMP-2026-0001-001
		self.name = f"{prefix}-{year}-{year_counter:04d}-{item_counter:03d}"
	
	def get_next_counter(self, prefix, year):
		"""Get auto-incremented global counter counting all POs with this prefix (year-independent)"""
		result = frappe.db.sql("""
			SELECT COUNT(*) + 1
			FROM `tabPurchase Order`
			WHERE name LIKE %s
			AND docstatus < 2
		""", (f"{prefix}-%-%-%",))
		
		return result[0][0] if result else 1
	
	def get_item_counter(self, item_code):
		"""Get auto-incremented counter for how many times this item has appeared in any PO"""
		# Query all Purchase Orders (across all years) that have this item
		item_count = frappe.db.sql("""
			SELECT COUNT(DISTINCT poi.parent)
			FROM `tabPurchase Order Item` poi
			INNER JOIN `tabPurchase Order` po ON poi.parent = po.name
			WHERE poi.item_code = %s
			AND po.docstatus < 2
		""", (item_code,))[0][0] or 0
		
		# Increment for this new PO
		return item_count + 1
