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
	- Local: LOC{po_counter}{ddmmyyy}{item_counter}
	- Imported: IMP{po_counter}{ddmmyyy}{item_counter}
	"""

	def autoname(self):
		if not self.items or len(self.items) == 0:
			frappe.throw(_("Purchase Order must contain at least one item."))

		item_code = self.items[0].item_code
		if not item_code:
			frappe.throw(_("Item code is required in Purchase Order items."))

		date_field = self.transaction_date or self.schedule_date
		if not date_field:
			frappe.throw(_("Transaction Date or Schedule Date is required for Purchase Order naming."))

		d = getdate(date_field)
		dd = f"{d.day:02d}"
		mm = f"{d.month:02d}"
		yyy = str(d.year)[-3:]
		date_str = f"{dd}{mm}{yyy}"

		is_imported = False

		if self.custom_purchase_order_type == "Imported Purchase":
			is_imported = True
		elif self.custom_importation_approval:
			is_imported = True
		elif self.custom_purchase_order_type == "Local Purchase":
			is_imported = False
		else:
			is_imported = False

		prefix = "IMP" if is_imported else "LOC"

		po_counter = self.get_next_po_counter(prefix)
		item_counter = self.get_item_counter(item_code)

		self.name = f"{prefix}{po_counter}{date_str}{item_counter}"

	def get_next_po_counter(self, prefix):
		"""Get auto-incremented PO counter across both old and new naming formats"""
		count = frappe.db.sql("""
			SELECT COUNT(*)
			FROM `tabPurchase Order`
			WHERE (name LIKE %s OR name LIKE %s)
			AND docstatus < 2
		""", (f"PO-{prefix}-%-%-%", f"{prefix}%",))

		return (count[0][0] or 0) + 1

	def get_item_counter(self, item_code):
		"""Get auto-incremented counter for how many times this item has appeared in any PO"""
		item_count = frappe.db.sql("""
			SELECT COUNT(DISTINCT poi.parent)
			FROM `tabPurchase Order Item` poi
			INNER JOIN `tabPurchase Order` po ON poi.parent = po.name
			WHERE poi.item_code = %s
			AND po.docstatus < 2
		""", (item_code,))[0][0] or 0

		return item_count + 1
