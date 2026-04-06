frappe.ui.form.on('Purchase Invoice', {
    refresh: function(frm) {
        // Ensure update_stock is checked by default
        // if (frm.is_new() && !frm.doc.update_stock) {
        //     frm.set_value('update_stock', 1);
        // }
    },
    
    onload: function(frm) {
        // When loading a Purchase Invoice, ensure update_stock is set
        // if (!frm.doc.update_stock) {
        //     frm.set_value('update_stock', 1);
        // }
    },
    
    update_stock: function(frm) {
        // When update_stock changes, update use_serial_batch_fields for all items
        if (frm.doc.items) {
            frm.doc.items.forEach(function(item) {
                if (frm.doc.update_stock === 1) {
                    frappe.model.set_value(item.doctype, item.name, 'use_serial_batch_fields', 1);
                }
            });
            frm.refresh_field('items');
        }
    }
});

frappe.ui.form.on('Purchase Invoice Item', {
    items_add: function(frm, cdt, cdn) {
        // When a new item is added, set use_serial_batch_fields to 1 if update_stock is 1
        let row = locals[cdt][cdn];
        if (frm.doc.update_stock === 1) {
            frappe.model.set_value(cdt, cdn, 'use_serial_batch_fields', 1);
        }
    },
    
    item_code: function(frm, cdt, cdn) {
        // When item_code changes, ensure use_serial_batch_fields is set
        let row = locals[cdt][cdn];
        if (frm.doc.update_stock === 1) {
            frappe.model.set_value(cdt, cdn, 'use_serial_batch_fields', 1);
        }
        
        // Check if item has batch enabled and show message
        if (row.item_code) {
            frappe.db.get_value('Item', row.item_code, 'has_batch_no', function(r) {
                if (r && r.has_batch_no) {
                    frappe.show_alert({
                        message: __('This item requires a batch number'),
                        indicator: 'blue'
                    }, 5);
                }
            });
        }
    }
});
