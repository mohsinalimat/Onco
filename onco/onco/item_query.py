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
@frappe.validate_and_sanitize_search_inputs
def filter_apply_price_lists(doctype, txt, searchfield, start, page_len, filters):
    if isinstance(filters, str):
        filters = json.loads(filters)
    customer = filters.get("customer")
    customer_group = None

    if customer:
        customer_group = frappe.db.get_value("Customer", customer, "customer_group")

    return frappe.db.sql("""
        SELECT DISTINCT pl.name, pl.price_list_name
        FROM `tabPrice List` pl
        WHERE pl.enabled = 1
        AND pl.selling = 1
        AND (pl.name LIKE %(txt)s OR pl.price_list_name LIKE %(txt)s)
        AND (
            -- No restrictions: show for everyone
            (NOT EXISTS (
                SELECT 1 FROM `tabApply for Customers` ac
                WHERE ac.parent = pl.name AND ac.parenttype = 'Price List'
            )
            AND NOT EXISTS (
                SELECT 1 FROM `tabApply for Customer Groups` acg
                WHERE acg.parent = pl.name AND acg.parenttype = 'Price List'
            ))
            -- Customer match
            OR (%(customer)s IS NOT NULL AND EXISTS (
                SELECT 1 FROM `tabApply for Customers` ac
                WHERE ac.parent = pl.name AND ac.parenttype = 'Price List'
                AND ac.customer = %(customer)s
            ))
            -- Customer group match
            OR (%(customer_group)s IS NOT NULL AND EXISTS (
                SELECT 1 FROM `tabApply for Customer Groups` acg
                WHERE acg.parent = pl.name AND acg.parenttype = 'Price List'
                AND acg.customer_group = %(customer_group)s
            ))
        )
        ORDER BY pl.name
        LIMIT %(page_len)s
    """, {
        "customer": customer or "",
        "customer_group": customer_group or "",
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
