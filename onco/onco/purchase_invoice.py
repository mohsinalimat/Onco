import frappe
from frappe import _

def validate(doc, method):
    """
    Validate Purchase Invoice before save
    Ensure batch numbers are provided for items that require them
    """
    # Bypass strict stock and batch validation during historical Data Imports
    if frappe.flags.in_import:
        return

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
