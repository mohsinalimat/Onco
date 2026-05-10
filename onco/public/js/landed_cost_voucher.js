frappe.ui.form.on('Landed Cost Voucher', {
    custom_shipment_id: function(frm) {
        if (frm.doc.custom_shipment_id) {
            frappe.show_alert({message: `Fetching vendor invoices for Shipment ID ${frm.doc.custom_shipment_id}...`, indicator: 'green'});
            fetch_vendor_invoices(frm, frm.doc.custom_shipment_id);
        }
    }
});

frappe.ui.form.on('Landed Cost Purchase Receipt', {
    receipt_document: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.receipt_document_type === 'Purchase Invoice' && row.receipt_document) {
            frappe.call({
                method: 'onco.onco.custom_scripts.landed_cost_voucher.get_shipment_from_purchase_invoice',
                args: { purchase_invoice: row.receipt_document },
                callback: function(r) {
                    if (r && r.message) {
                        frm.set_value('custom_shipment_id', r.message);
                        // The custom_shipment_id trigger above will handle the fetching
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
            if (r && r.message && r.message.length > 0) {
                let current_taxes = frm.doc.taxes || [];
                let existing_descriptions = current_taxes.map(t => t.description);
                let added_count = 0;

                r.message.forEach(invoice => {
                    // Prevent duplicates based on description (which contains invoice ID)
                    if (!existing_descriptions.includes(invoice.description)) {
                        let child = frm.add_child('taxes');
                        child.description = invoice.description;
                        child.expense_account = invoice.expense_account;
                        child.amount = invoice.grand_total;
                        added_count++;
                    }
                });

                if (added_count > 0) {
                    frm.refresh_field('taxes');
                    frappe.show_alert({message: `Added ${added_count} vendor invoices to Taxes and Charges automatically.`, indicator: 'green'});
                } else {
                    frappe.show_alert({message: `Vendor invoices for Shipment ID ${shipment_id} are already in the table.`, indicator: 'orange'});
                }
            } else {
                frappe.msgprint(`No submitted vendor service invoices found for Shipment ID: ${shipment_id}`);
            }
        }
    });
}
