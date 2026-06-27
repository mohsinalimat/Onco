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

                if (frm.doc.taxes && frm.doc.taxes.length > 0) {
                    let first_row = frm.doc.taxes[0];
                    if (!first_row.expense_account && !first_row.description && !first_row.amount) {
                        frm.clear_table('taxes');
                    }
                }

                let current_taxes = frm.doc.taxes || [];
                let existing_invoices = current_taxes.map(t => t.custom_vendor_invoice);
                let added_to_taxes = 0;
                let added_to_vi = 0;

                r.message.forEach(invoice => {
                    if (invoice.remaining > 0) {
                        let vi_row = frm.add_child('vendor_invoices');
                        vi_row.vendor_invoice = invoice.name;
                        vi_row.amount = invoice.remaining;
                        added_to_vi++;
                    }

                    if (!existing_invoices.includes(invoice.name)) {
                        let child = frm.add_child('taxes');
                        child.description = invoice.description;
                        child.expense_account = invoice.expense_account;
                        child.amount = invoice.remaining;
                        child.custom_vendor_invoice = invoice.name;
                        child.custom_supplier_invoice_no = invoice.bill_no;
                        child.custom_posting_date = invoice.posting_date;
                        child.custom_allocated_to_shipment = invoice.allocated_to_shipment;
                        child.custom_already_used = invoice.already_used;
                        child.custom_remaining = invoice.remaining;
                        added_to_taxes++;
                    }
                });

                frm.refresh_field('vendor_invoices');
                frm.refresh_field('taxes');

                if (added_to_vi > 0) {
                    frappe.show_alert({message: `Added ${added_to_vi} vendor invoice(s) and ${added_to_taxes} tax row(s).`, indicator: 'green'});
                }

                let exhausted = r.message.filter(inv => inv.remaining <= 0);
                if (exhausted.length > 0) {
                    frappe.msgprint({
                        title: 'Notice',
                        indicator: 'orange',
                        message: `${exhausted.length} invoice(s) have no remaining balance to allocate. They were skipped.`
                    });
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
