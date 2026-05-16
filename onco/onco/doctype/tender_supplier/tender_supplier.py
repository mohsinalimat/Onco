# Copyright (c) 2025, ds and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TenderSupplier(Document):
	pass


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_local_pharmaceutical_customers(doctype, txt, searchfield, start, page_len, filters):
	"""
	Filter customers to show only those in 'Pharmaceuticals Local Distributors Companies' group
	"""
	return frappe.db.sql("""
		SELECT name, customer_name, customer_group
		FROM `tabCustomer`
		WHERE customer_group = 'Pharmaceuticals Local Distributors Companies'
		AND (name LIKE %(txt)s OR customer_name LIKE %(txt)s)
		AND disabled = 0
		AND docstatus < 2
		ORDER BY
			CASE WHEN name LIKE %(txt)s THEN 0 ELSE 1 END,
			CASE WHEN customer_name LIKE %(txt)s THEN 0 ELSE 1 END,
			name
		LIMIT %(page_len)s OFFSET %(start)s
	""", {
		'txt': "%%%s%%" % txt,
		'start': start,
		'page_len': page_len
	})
