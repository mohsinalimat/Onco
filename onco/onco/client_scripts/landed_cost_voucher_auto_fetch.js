/**
 * Landed Cost Voucher - Auto-fetch Vendor Invoices
 * 
 * This client script automatically:
 * 1. Detects Shipment ID from selected Purchase Receipt/Invoice
 * 2. Fetches all vendor service invoices linked to the same Shipment
 * 3. Populates the Landed Cost Voucher with vendor costs
 * 4. Uses expense accounts from vendor invoices for cost distribution
 */

frappe.ui.form.on('Landed Cost Voucher', {
    refresh: function(frm) {
        // Add custom button to manually trigger auto-fetch
        if (!frm.doc.__islocal && frm.doc.custom_shipment_id && !frm.doc.docstatus) {
            frm.add_custom_button(__('Fetch Vendor Invoices'), function() {
                fetch_vendor_invoices(frm);
            });
        }
    },

    custom_auto_fetch_vendor_invoices: function(frm) {
        // When checkbox is enabled, trigger auto-fetch
        if (frm.doc.custom_auto_fetch_vendor_invoices && frm.doc.custom_shipment_id) {
            fetch_vendor_invoices(frm);
        }
    },

    custom_shipment_id: function(frm) {
        // When Shipment ID changes and auto-fetch is enabled
        if (frm.doc.custom_auto_fetch_vendor_invoices && frm.doc.custom_shipment_id) {
            fetch_vendor_invoices(frm);
        }
    }
});

// Monitor Vouchers table for changes (Purchase Invoices in v16)
frappe.ui.form.on('Landed Cost Voucher', {
    vouchers_add: function(frm, cdt, cdn) {
        // When a new voucher row is added, wait for it to be populated
        setTimeout(() => {
            let row = locals[cdt][cdn];
            if (row.receipt_document && row.receipt_document_type === 'Purchase Invoice') {
                detect_shipment_from_invoice(frm, row.receipt_document);
            }
        }, 500);
    }
});

frappe.ui.form.on('Landed Cost Voucher Item', {
    receipt_document: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.receipt_document && row.receipt_document_type === 'Purchase Invoice') {
            detect_shipment_from_invoice(frm, row.receipt_document);
        }
    },
    
    vouchers_remove: function(frm) {
        // If all vouchers removed, clear shipment
        if (!frm.doc.vouchers || frm.doc.vouchers.length === 0) {
            frm.set_value('custom_shipment_id', null);
        }
    }
});

/**
 * Detect Shipment ID from Purchase Invoice
 */
function detect_shipment_from_invoice(frm, purchase_invoice) {
    if (!purchase_invoice) return;
    
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Purchase Invoice',
            filters: { name: purchase_invoice },
            fieldname: ['custom_shipments', 'custom_shipment_id_dimension']
        },
        callback: function(r) {
            if (r.message) {
                // Try custom_shipments first (foreign supplier invoice), then custom_shipment_id_dimension (vendor invoice)
                let shipment_id = r.message.custom_shipments || r.message.custom_shipment_id_dimension;
                
                if (shipment_id) {
                    frm.set_value('custom_shipment_id', shipment_id);
                    
                    if (frm.doc.custom_auto_fetch_vendor_invoices) {
                        fetch_vendor_invoices(frm);
                    } else {
                        frappe.msgprint({
                            title: __('Shipment Detected'),
                            message: __('Shipment ID {0} detected. Enable "Auto-fetch Vendor Invoices" to automatically load vendor costs.', [shipment_id]),
                            indicator: 'blue'
                        });
                    }
                }
            }
        }
    });
}

/**
 * Fetch vendor invoices linked to the same Shipment ID
 */
function fetch_vendor_invoices(frm) {
    if (!frm.doc.custom_shipment_id) {
        frappe.msgprint(__('No Shipment ID found. Please select a Purchase Receipt first.'));
        return;
    }

    frappe.call({
        method: 'onco.onco.custom_scripts.landed_cost_voucher.get_vendor_invoices_for_shipment',
        args: {
            shipment_id: frm.doc.custom_shipment_id,
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                populate_vendor_invoices(frm, r.message);
                frappe.msgprint({
                    title: __('Vendor Invoices Loaded'),
                    message: __('Found {0} vendor invoice(s) for Shipment {1}', [r.message.length, frm.doc.custom_shipment_id]),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('No Vendor Invoices Found'),
                    message: __('No vendor service invoices found for Shipment {0}. Make sure vendor invoices have the Shipment ID dimension set.', [frm.doc.custom_shipment_id]),
                    indicator: 'orange'
                });
            }
        }
    });
}

/**
 * Populate Landed Cost Taxes and Charges table with vendor invoices
 */
function populate_vendor_invoices(frm, vendor_invoices) {
    // Clear existing applicable charges (optional - ask user first)
    if (frm.doc.applicable_charges && frm.doc.applicable_charges.length > 0) {
        frappe.confirm(
            __('This will replace existing charges. Continue?'),
            function() {
                add_vendor_charges(frm, vendor_invoices);
            }
        );
    } else {
        add_vendor_charges(frm, vendor_invoices);
    }
}

/**
 * Add vendor charges to the Landed Cost Voucher
 */
function add_vendor_charges(frm, vendor_invoices) {
    // Clear existing charges in "applicable_charges" table (Landed Cost section)
    frm.clear_table('applicable_charges');
    
    vendor_invoices.forEach(function(invoice) {
        let row = frm.add_child('applicable_charges');
        row.description = invoice.description || `Vendor Invoice: ${invoice.name}`;
        row.expense_account = invoice.expense_account;
        row.amount = invoice.grand_total;
        row.account_currency = invoice.currency;
    });
    
    frm.refresh_field('applicable_charges');
    
    // Trigger calculation
    frm.trigger('calculate_applicable_charges');
}
