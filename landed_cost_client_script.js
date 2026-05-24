// Copy this entire script into:
// Landed Cost Voucher → Menu (3 dots) → Customize → Client Script tab

frappe.ui.form.on('Landed Cost Voucher Item', {
    receipt_document: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.receipt_document && row.receipt_document_type === 'Purchase Invoice') {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Purchase Invoice',
                    filters: { name: row.receipt_document },
                    fieldname: ['custom_shipments']
                },
                callback: function(r) {
                    if (r.message) {
                        let shipment_id = r.message.custom_shipments;
                        if (shipment_id) {
                            frm.set_value('custom_shipment_id', shipment_id);
                            // Auto-fetch immediately
                            fetch_vendor_invoices(frm, shipment_id);
                        }
                    }
                }
            });
        }
    }
});

function fetch_vendor_invoices(frm, shipment_id) {
    frappe.call({
        method: 'onco.onco.custom_scripts.landed_cost_voucher.get_vendor_invoices_for_shipment',
        args: {
            shipment_id: shipment_id,
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                frm.clear_table('taxes');
                r.message.forEach(function(invoice) {
                    let row = frm.add_child('taxes');
                    row.description = invoice.description;
                    row.expense_account = invoice.expense_account;
                    row.amount = invoice.remaining;
                    row.custom_vendor_invoice = invoice.name;
                    row.custom_supplier_invoice_no = invoice.bill_no;
                    row.custom_posting_date = invoice.posting_date;
                    row.custom_allocated_to_shipment = invoice.allocated_to_shipment;
                    row.custom_already_used = invoice.already_used;
                    row.custom_remaining = invoice.remaining;
                });
                frm.refresh_field('applicable_charges');
                frappe.show_alert({message: __('Loaded {0} vendor invoices', [r.message.length]), indicator: 'green'});
            } else {
                frappe.show_alert({message: __('No vendor invoices found'), indicator: 'orange'});
            }
        }
    });
}
