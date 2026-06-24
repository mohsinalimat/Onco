import json

import frappe


@frappe.whitelist()
def filter_pharma_items_by_supplier(doctype, txt, searchfield, start, page_len, filters):
    if isinstance(filters, str):
        filters = json.loads(filters)
    supplier = filters.get("supplier")

    return frappe.db.sql("""
        SELECT DISTINCT i.name, i.item_name
        FROM `tabItem` i
        LEFT JOIN `tabItem Supplier` s ON s.parent = i.name AND s.parenttype = 'Item'
        WHERE i.custom_pharmaceutical_item = 1
        AND i.disabled = 0
        AND (i.default_supplier = %(supplier)s OR s.supplier = %(supplier)s)
        AND (i.name LIKE %(txt)s OR i.item_name LIKE %(txt)s)
        ORDER BY i.name
        LIMIT %(page_len)s
    """, {
        "supplier": supplier,
        "txt": f"%{txt}%",
        "page_len": int(page_len)
    })


@frappe.whitelist()
def filter_items_by_supplier(doctype, txt, searchfield, start, page_len, filters):
    if isinstance(filters, str):
        filters = json.loads(filters)
    supplier = filters.get("supplier")

    return frappe.db.sql("""
        SELECT DISTINCT i.name, i.item_name
        FROM `tabItem` i
        LEFT JOIN `tabItem Supplier` s ON s.parent = i.name AND s.parenttype = 'Item'
        WHERE i.disabled = 0
        AND (i.default_supplier = %(supplier)s OR s.supplier = %(supplier)s)
        AND (i.name LIKE %(txt)s OR i.item_name LIKE %(txt)s)
        ORDER BY i.name
        LIMIT %(page_len)s
    """, {
        "supplier": supplier,
        "txt": f"%{txt}%",
        "page_len": int(page_len)
    })
