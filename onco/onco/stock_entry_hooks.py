import frappe

def before_save(doc, method):
    """Auto-populate custom_purchase_receipt and custom_shipment_ref on Stock Entry when created from Purchase Receipt."""
    if doc.custom_purchase_receipt:
        # If Purchase Receipt is already set, ensure Shipment is also set
        if not doc.custom_shipment_ref:
            shipment_ref = frappe.db.get_value("Purchase Receipt", doc.custom_purchase_receipt, "custom_shipment_ref")
            if shipment_ref:
                doc.custom_shipment_ref = shipment_ref
        return  # Already set

    # Check if any Stock Entry item has a purchase_receipt reference
    # ERPNext sets this field on Stock Entry Detail when SE is created from PR
    for item in doc.items:
        pr_name = item.get("purchase_receipt")
        if pr_name:
            doc.custom_purchase_receipt = pr_name
            # Also fetch and set the shipment reference
            shipment_ref = frappe.db.get_value("Purchase Receipt", pr_name, "custom_shipment_ref")
            if shipment_ref:
                doc.custom_shipment_ref = shipment_ref
            frappe.msgprint(f"Purchase Receipt {pr_name} linked to Stock Entry", alert=True)
            break
    
    # If still not found, check if this Stock Entry was created from a Purchase Receipt
    # by checking the source warehouse items
    if not doc.custom_purchase_receipt and doc.items:
        # Try to find Purchase Receipt from the item's batch or warehouse history
        for item in doc.items:
            if item.s_warehouse:  # Source warehouse exists
                # Query for recent Purchase Receipt that has this item in this warehouse
                pr_list = frappe.db.sql("""
                    SELECT DISTINCT pr.name, pr.custom_shipment_ref
                    FROM `tabPurchase Receipt` pr
                    INNER JOIN `tabPurchase Receipt Item` pri ON pri.parent = pr.name
                    WHERE pr.docstatus = 1
                    AND pri.item_code = %(item_code)s
                    AND pri.warehouse = %(warehouse)s
                    AND pr.posting_date <= %(posting_date)s
                    ORDER BY pr.posting_date DESC, pr.creation DESC
                    LIMIT 1
                """, {
                    'item_code': item.item_code,
                    'warehouse': item.s_warehouse,
                    'posting_date': doc.posting_date
                }, as_dict=True)
                
                if pr_list:
                    doc.custom_purchase_receipt = pr_list[0].name
                    if pr_list[0].custom_shipment_ref:
                        doc.custom_shipment_ref = pr_list[0].custom_shipment_ref
                    frappe.msgprint(f"Purchase Receipt {pr_list[0].name} auto-linked based on warehouse and item", alert=True)
                    break
