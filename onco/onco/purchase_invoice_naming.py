# Copyright (c) 2026, ds and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice


class CustomPurchaseInvoice(PurchaseInvoice):
	"""
	Custom Purchase Invoice class to override autoname method
	Format based on purchase type:
	- Local Pharma: PHR-LOC-PINV-YYYY-#####-{supplier_invoice_no}
	- Imported Pharma: PHR-IMP-PINV-YYYY-#####-{supplier_invoice_no}
	- General Purchase: GEN-PINV-YYYY-#####-{supplier_invoice_no}
	"""
	
	def autoname(self):
		"""
		Custom autoname method for Purchase Invoice with type-based naming
		"""
		# Get the year from posting_date
		if not self.posting_date:
			frappe.throw(_("Posting Date is required for Purchase Invoice naming."))
		
		year = getdate(self.posting_date).year
		
		# Determine purchase type
		purchase_type = self.determine_purchase_type()
		
		# Set prefix based on type
		if purchase_type == "local_pharma":
			prefix = "PHR-LOC-PINV"
		elif purchase_type == "imported_pharma":
			prefix = "PHR-IMP-PINV"
		elif purchase_type == "general":
			prefix = "GEN-PINV"
		else:
			# Fallback to general if type cannot be determined
			prefix = "GEN-PINV"
		
		# Get the next counter for this prefix and year
		counter = self.get_next_counter(prefix, year)
		
		# Get supplier invoice number (bill_no field)
		supplier_invoice_no = self.bill_no or ""
		
		# Generate name in format: {PREFIX}-YYYY-#####-{supplier_invoice_no}
		# Examples: 
		# - PHR-LOC-PINV-2026-00001-INV123
		# - PHR-IMP-PINV-2026-00001-INV456
		# - GEN-PINV-2026-00001-INV789
		base_name = f"{prefix}-{year}-{counter:05d}"
		
		if supplier_invoice_no:
			self.name = f"{base_name}-{supplier_invoice_no}"
		else:
			self.name = base_name
	
	def determine_purchase_type(self):
		"""
		Determine if this is local pharma, imported pharma, or general purchase
		Logic:
		1. Check custom_purchase_type field (manual selection)
		2. Check if linked to Purchase Order with importation approval -> imported pharma
		3. Check if linked to Purchase Order naming (PO-IMP or PO-LOC)
		4. Check if items are pharmaceutical
		5. Default to general
		"""
		# Priority 1: Check custom_purchase_type field (manual override)
		if hasattr(self, 'custom_purchase_type') and self.custom_purchase_type:
			if self.custom_purchase_type == "Imported Pharma":
				return "imported_pharma"
			elif self.custom_purchase_type == "Local Pharma":
				return "local_pharma"
			elif self.custom_purchase_type == "General Purchase":
				return "general"
		
		# Priority 2: Check if linked to Purchase Order
		if self.items:
			for item in self.items:
				if item.purchase_order:
					po = frappe.get_doc("Purchase Order", item.purchase_order)
					
					# Check if PO has importation approval
					if po.custom_importation_approval:
						return "imported_pharma"
					
					# Check PO naming pattern (PO-IMP/IMP or PO-LOC/LOC)
					if item.purchase_order.startswith("PO-IMP") or item.purchase_order.startswith("IMP"):
						return "imported_pharma"
					elif item.purchase_order.startswith("PO-LOC") or item.purchase_order.startswith("LOC"):
						# Check if items are pharmaceutical
						if self.has_pharmaceutical_items():
							return "local_pharma"
						else:
							return "general"
					
					# Check PO type field (legacy)
					if hasattr(po, 'custom_purchase_order_type'):
						if po.custom_purchase_order_type == "Imported Purchase":
							return "imported_pharma"
						elif po.custom_purchase_order_type == "Local Purchase":
							# Check if items are pharmaceutical
							if self.has_pharmaceutical_items():
								return "local_pharma"
							else:
								return "general"
		
		# Priority 3: Check if items are pharmaceutical (no PO link)
		if self.has_pharmaceutical_items():
			# If no PO link, assume local pharma
			return "local_pharma"
		
		# Default to general purchase
		return "general"
	
	def has_pharmaceutical_items(self):
		"""Check if any items in the invoice are pharmaceutical"""
		if not self.items:
			return False
		
		for item in self.items:
			if item.item_code:
				is_pharma = frappe.db.get_value("Item", item.item_code, "custom_pharmaceutical_item")
				if is_pharma:
					return True
		
		return False
	
	def get_next_counter(self, prefix, year):
		"""Get auto-incremented counter for naming series specific to prefix and year"""
		# Query Purchase Invoice documents with name like "{prefix}-{year}-%"
		existing = frappe.get_all(
			"Purchase Invoice",
			filters={
				"name": ["like", f"{prefix}-{year}-%"]
			},
			fields=["name"],
			order_by="creation desc",
			limit=100
		)
		
		if existing:
			# Extract counter from all matching names and find the maximum
			max_counter = 0
			
			for doc in existing:
				# Extract counter from name
				# Format: PHR-LOC-PINV-YYYY-#####-{supplier_invoice_no}
				# or: PHR-LOC-PINV-YYYY-#####
				# Counter is always after the year, so we need to extract it carefully
				
				# Remove the prefix and year first
				name_without_prefix = doc.name.replace(f"{prefix}-{year}-", "", 1)
				
				# The counter is the first part before any hyphen (or the whole string if no hyphen)
				counter_str = name_without_prefix.split("-")[0]
				
				try:
					counter = int(counter_str)
					if counter > max_counter:
						max_counter = counter
				except (ValueError, IndexError):
					# Skip if counter is not a valid integer
					continue
			
			if max_counter > 0:
				return max_counter + 1
		
		# Return 1 if no existing documents or extraction failed
		return 1
