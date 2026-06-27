# Copyright (c) 2025, ds and contributors
# For license information, please see license.txt
import json
import re

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt


class CustomerPurchaseOrder(Document):
	def validate(self):
		self.calculate_totals()
		self.fetch_item_prices()

	def calculate_totals(self):
		total_qty = 0
		total_amount = 0
		for row in self.get("customer_po_items") or []:
			total_qty += flt(row.quantity)
			row.amount = flt(row.quantity) * flt(row.price)
			total_amount += flt(row.amount)
		self.total_qty = total_qty
		self.total_amount = total_amount

	def fetch_item_prices(self):
		if not self.price_list:
			return
		for row in self.get("customer_po_items") or []:
			if not row.item:
				continue
			price = frappe.get_value(
				"Item Price",
				{"item_code": row.item, "price_list": self.price_list},
				"price_list_rate"
			)
			if price and flt(row.price) != flt(price):
				row.price = flt(price)

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
			if len(parts) >= 5:
				try:
					# Counter is at index 4 (after 3 prefix segments + year)
					# Example: CPO-PRV-DIR-2020-00001-PO123
					#          [0] [1] [2] [3]  [4]   [5]
					last_counter = int(parts[4])
					return last_counter + 1
				except (ValueError, IndexError):
					# If counter is not a valid integer, start from 1
					pass
		
		# Return 1 if no existing documents or extraction failed
		return 1


@frappe.whitelist()
def get_applicable_price_lists(customer):
	"""Return list of price list names applicable to this customer or their group."""
	if not customer:
		return []

	customer_group = frappe.get_value("Customer", customer, "customer_group")

	all_price_lists = frappe.get_all(
		"Price List",
		filters={"selling": 1, "enabled": 1},
		pluck="name"
	)

	applicable = []
	for pl in all_price_lists:
		pl_doc = frappe.get_cached_doc("Price List", pl)
		# Check custom_apply_for_customers
		if pl_doc.get("custom_apply_for_customers"):
			for row in pl_doc.custom_apply_for_customers:
				if row.customer == customer:
					applicable.append(pl)
					break
		else:
			# Check custom_apply_for_customer_groups
			if pl_doc.get("custom_apply_for_customer_groups") and customer_group:
				for row in pl_doc.custom_apply_for_customer_groups:
					if row.customer_group == customer_group:
						applicable.append(pl)
						break

	return applicable


@frappe.whitelist()
def create_sales_order(cpo_name, items_data):
	"""Create Sales Order from a Customer Purchase Order.
	items_data: JSON string or list of {item_code, qty}"""
	cpo = frappe.get_doc("Customer Purchase Order", cpo_name)

	if isinstance(items_data, str):
		items_data = json.loads(items_data)

	so_items = []
	for d in items_data:
		qty = flt(d.get("qty"))
		if qty <= 0:
			continue

		cpo_row = next(
			(r for r in cpo.customer_po_items if r.item == d.get("item_code")),
			None
		)
		if not cpo_row:
			continue

		remaining = flt(cpo_row.quantity) - flt(cpo_row.ordered_qty)
		if qty > remaining:
			frappe.throw(_(
				"Qty {0} for item {1} exceeds remaining quantity {2}"
			).format(qty, d["item_code"], remaining))

		so_items.append({
			"item_code": d["item_code"],
			"qty": qty,
			"rate": flt(cpo_row.price),
			"delivery_date": cpo.delivery_date
		})

	if not so_items:
		frappe.throw(_("No items with valid quantities provided"))

	pl_name = cpo.price_list
	if not pl_name and cpo.customer:
		customer_pl = frappe.db.get_value(
			"Item Price",
			{"selling": 1, "customer": cpo.customer},
			"price_list",
			order_by="creation desc"
		)
		if not customer_pl:
			customer_pl = frappe.db.get_value(
				"Item Price",
				{"selling": 1},
				"price_list",
				order_by="creation desc"
			)
		pl_name = customer_pl or "Standard Selling"

	pl_currency = frappe.db.get_value("Price List", pl_name, "currency") or ""

	series_map = {
		"Private Direct Order": "SAL-ORD-PRV-DIR-.YYYY.-.#####",
		"Private Tenders Order": "SAL-ORD-PRV-TEN-.YYYY.-.#####",
		"UPA Tender Order": "SAL-ORD-UPA-TEN-.YYYY.-.#####",
		"UPA Direct Order": "SAL-ORD-UPA-DIR-.YYYY.-.#####",
		"UPA Distributor Order": "SAL-ORD-UPA-DIS-.YYYY.-.#####",
	}

	so = frappe.get_doc({
		"doctype": "Sales Order",
		"customer": cpo.customer,
		"transaction_date": cpo.date,
		"delivery_date": cpo.delivery_date,
		"po_no": cpo.customer_purchase_order_number,
		"po_date": cpo.date,
		"items": so_items,
		"naming_series": series_map.get(cpo.order_type, ""),
		"custom_order_type_1": cpo.order_type,
		"implemented_by": cpo.implemented_by,
		"customer_type": cpo.customer_type,
		"requested_to_": cpo.requested_to,
		"selling_price_list": pl_name,
		"price_list_currency": pl_currency,
		"plc_conversion_rate": 1.0,
		"custom_customer_po": cpo.name,
		"custom_tender": cpo.tender if cpo.tender else None
	})

	so.insert(ignore_permissions=True)
	so.submit()

	# Update ordered_qty on CPO items
	for d in items_data:
		qty = flt(d.get("qty"))
		if qty <= 0:
			continue
		for cpo_row in cpo.customer_po_items:
			if cpo_row.item == d.get("item_code"):
				cpo_row.ordered_qty = flt(cpo_row.ordered_qty) + qty
				break

	cpo.save(ignore_permissions=True)

	return so.name
