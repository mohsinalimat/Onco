import frappe
from frappe import _
from frappe.utils import flt

def validate(doc, method):
    """
    Validate Purchase Invoice before save
    Ensure batch numbers are provided for items that require them
    """
    frappe.throw(_("TEST: purchase_invoice.validate is firing!"))

    # Set use_serial_batch_fields for all items when update_stock is enabled
    if doc.update_stock:
        for item in doc.items:
            if not item.use_serial_batch_fields:
                item.use_serial_batch_fields = 1
            
            # Set warehouse to Incoming Warehouse if not set (for batch creation)
            # Note: 2 spaces after "Imported", 1 space before dash
            if not item.warehouse:
                item.warehouse = "Imported  Finished Phr Incoming Warehouse - Onco"
    
    # Validate batch numbers for items that require them
    for item in doc.items:
        if item.item_code:
            item_doc = frappe.get_cached_doc('Item', item.item_code)
            if item_doc.has_batch_no and doc.update_stock:
                if not item.batch_no and not item.serial_and_batch_bundle:
                    frappe.throw(
                        _("Row #{0}: Batch Number is mandatory for item {1}").format(
                            item.idx, item.item_code
                        )
                    )

    # Validate custom_shipment_allocation doesn't exceed items total
    if doc.get("custom_shipment_allocation"):
        total_allocated = sum(flt(row.amount) for row in doc.custom_shipment_allocation)
        total_items = sum(flt(item.amount) for item in doc.items)
        frappe.log_error(f"DEBUG allocation: total_allocated={total_allocated}, total_items={total_items}", "PI Validation Debug")
        if total_allocated > total_items:
            frappe.throw(_(
                "Total Shipment Allocation amount ({0}) cannot exceed "
                "the total Items amount ({1})"
            ).format(
                frappe.format_value(total_allocated, "Currency"),
                frappe.format_value(total_items, "Currency")
            ))

def on_submit(doc, method):
    """
    Actions to perform after Purchase Invoice is submitted
    """
    pass

def before_insert(doc, method):
    """
    Actions to perform before inserting a new Purchase Invoice
    """
    # Bypass forcing stock updates during historical Data Imports
    if frappe.flags.in_import:
        return

    # Removed automatic update_stock enforcement as per user request
    # if not doc.update_stock:
    #     doc.update_stock = 1
    
    # Set use_serial_batch_fields for all items when update_stock is enabled
    if doc.update_stock:
        for item in doc.items:
            if not item.use_serial_batch_fields:
                item.use_serial_batch_fields = 1
