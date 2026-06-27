frappe.ui.form.on('Landed Cost Voucher', {
    onload: function(frm) {
        frm.set_query('receipt_document', 'purchase_receipts', function(doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            if (child.receipt_document_type === 'Purchase Invoice') {
                return {
                    filters: {
                        docstatus: 1,
                        company: doc.company
                    }
                };
            }
        });
    },
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
                        fetch_vendor_invoices(frm, r.message);
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
                frm.clear_table('vendor_invoices');
                let added_count = 0;

                r.message.forEach(invoice => {
                    if (invoice.remaining > 0) {
                        let row = frm.add_child('vendor_invoices');
                        row.vendor_invoice = invoice.name;
                        row.amount = invoice.remaining;
                        added_count++;
                    }
                });

                if (added_count > 0) {
                    frm.refresh_field('vendor_invoices');
                    frappe.show_alert({message: `Added ${added_count} vendor invoice(s) with remaining allocation.`, indicator: 'green'});

                    let exhausted = r.message.filter(inv => inv.remaining <= 0);
                    if (exhausted.length > 0) {
                        frappe.msgprint({
                            title: 'Notice',
                            indicator: 'orange',
                            message: `${exhausted.length} invoice(s) have no remaining balance to allocate. They were skipped.`
                        });
                    }
                } else {
                    frappe.msgprint(`All vendor invoices for Shipment ID ${shipment_id} have been fully consumed.`);
                }

                if (frm.doc.purchase_receipts && frm.doc.purchase_receipts.length > 0) {
                    setTimeout(() => {
                        frappe.call({
                            method: "get_items_from_purchase_receipts",
                            doc: frm.doc,
                            callback: function(r2) {
                                if (!r2.exc) {
                                    if (frm.doc.items && frm.doc.items.length > 0 && !frm.doc.items[0].item_code) {
                                        frm.doc.items.shift();
                                    }
                                    frm.refresh_field("items");
                                }
                            }
                        });
                    }, 500);
                }
            } else {
                frappe.msgprint(`No submitted vendor service invoices found for Shipment ID: ${shipment_id}`);
            }
        }
    });
}
