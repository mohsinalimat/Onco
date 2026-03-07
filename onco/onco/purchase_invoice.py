import frappe
from frappe import _

def validate(doc, method):
    """
    Validate Purchase Invoice before save
    Ensure batch numbers are provided for items that require them
    """
    # Ensure update_stock is set to 1 for importation cycle
    if not doc.update_stock:
        doc.update_stock = 1
    
    # Set use_serial_batch_fields for all items when update_stock is enabled
    if doc.update_stock:
        for item in doc.items:
            if not item.use_serial_batch_fields:
                item.use_serial_batch_fields = 1
    
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
    # Set update_stock to 1 by default
    if not doc.update_stock:
        doc.update_stock = 1
    
    # Set use_serial_batch_fields for all items
    for item in doc.items:
        if not item.use_serial_batch_fields:
            item.use_serial_batch_fields = 1
