frappe.ui.form.on('Landed Cost Voucher', {
    setup: function(frm) {
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
            console.log("Purchase Invoice selected: " + row.receipt_document);
            frappe.call({
                method: 'onco.onco.custom_scripts.landed_cost_voucher.get_shipment_from_purchase_invoice',
                args: { purchase_invoice: row.receipt_document },
                callback: function(r) {
                    if (r && r.message) {
                        console.log("Shipment ID fetched: " + r.message);
                        frm.set_value('custom_shipment_id', r.message);
                        // The custom_shipment_id trigger above will handle the fetching
                    } else {
                        console.log("No Shipment ID returned from backend for invoice: " + row.receipt_document);
                    }
                },
                error: function(e) {
                    console.error("Error fetching shipment ID:", e);
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
                // Clean up default empty rows safely using Frappe UI API
                if (frm.doc.taxes && frm.doc.taxes.length > 0) {
                    let first_row = frm.doc.taxes[0];
                    if (!first_row.expense_account && !first_row.description && !first_row.amount) {
                        frm.clear_table('taxes');
                    }
                }

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

                // Auto-fetch receipt items properly
                if (frm.doc.purchase_receipts && frm.doc.purchase_receipts.length > 0) {
                    setTimeout(() => {
                        frappe.call({
                            method: "get_items_from_purchase_receipts",
                            doc: frm.doc,
                            callback: function(r2) {
                                if (!r2.exc) {
                                    // Remove the blank default item row if the backend didn't
                                    if (frm.doc.items && frm.doc.items.length > 0 && !frm.doc.items[0].item_code) {
                                        frm.doc.items.shift();
                                    }
                                    frm.refresh_field("items");
                                }
                            }
                        });
                    }, 500); // Slight delay ensures Frappe's model is synced before backend call
                }

            } else {
                frappe.msgprint(`No submitted vendor service invoices found for Shipment ID: ${shipment_id}`);
            }
        },
        error: function(e) {
            console.error("Error fetching vendor invoices:", e);
        }
    });
}
