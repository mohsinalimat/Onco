import frappe

def before_save(doc, method):
    """Auto-populate custom_purchase_receipt on Stock Entry when created from Purchase Receipt."""
    if doc.custom_purchase_receipt:
        return  # Already set

    # Check if any Stock Entry item has a purchase_receipt reference
    # ERPNext sets this field on Stock Entry Detail when SE is created from PR
    for item in doc.items:
        pr_name = item.get("purchase_receipt")
        if pr_name:
            doc.custom_purchase_receipt = pr_name
            break
