// Copyright (c) 2026, Onco and contributors
// For license information, please see license.txt

frappe.ui.form.on('Authority Good Release', {
    refresh: function (frm) {
        // Add custom buttons
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Fetch Items from Purchase Receipt Report'), function () {
                fetch_items_from_purchase_receipt_report(frm);
            });
        }

        // Add manual stock entry creation button if document is submitted and auto-create is disabled
        if (frm.doc.docstatus === 1 && !frm.doc.create_stock_entry && !frm.doc.stock_entry_created) {
            frm.add_custom_button(__('Create Stock Entries'), function () {
                frappe.confirm(
                    __('Are you sure you want to create stock entries for this Authority Good Release?'),
                    function () {
                        // User confirmed
                        frappe.call({
                            method: 'create_stock_entries_manually',
                            doc: frm.doc,
                            callback: function (r) {
                                if (r.message && r.message.length > 0) {
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }, __('Actions'));
        }

        // Show/hide fields based on release type
        toggle_fields_based_on_release_type(frm);
    },

    create_stock_entry: function (frm) {
        // Show warning if disabling auto-create on a draft document
        if (!frm.doc.create_stock_entry && frm.doc.docstatus === 0) {
            frappe.msgprint({
                title: __('Manual Stock Entry Mode'),
                message: __('Stock entries will NOT be created automatically on submit. You will need to manually create them using the "Create Stock Entries" button after submission.'),
                indicator: 'orange'
            });
        }
    },

    release_type: function (frm) {
        toggle_fields_based_on_release_type(frm);

        // Clear subtype when release type changes
        frm.set_value('lrb_subtype', '');
        frm.set_value('abi_subtype', '');
    },

    shipment_no: function (frm) {
        if (frm.doc.shipment_no) {
            // Fetch invoice number from shipment
            frappe.db.get_value('Shipments', frm.doc.shipment_no, 'custom_invoices')
                .then(r => {
                    if (r.message && r.message.custom_invoices) {
                        // This would need to be enhanced to get the actual invoice number
                        // from the shipment invoice child table
                    }
                });
        }
    },

    before_submit: function (frm) {
        // Validate quantities
        let has_items = false;
        frm.doc.items.forEach(function (item) {
            if (item.released_qty > 0) {
                has_items = true;
            }

            // Validate released quantity doesn't exceed requested quantity
            if (item.released_qty > item.requested_qty) {
                frappe.throw(__(`Released quantity for ${item.item_code} cannot exceed requested quantity`));
            }
        });

        if (!has_items) {
            frappe.throw(__('Please add at least one item with released quantity'));
        }

        // Validate sample quantities for analysis batch
        if (frm.doc.release_type === 'Analysis Batch Inspection' &&
            frm.doc.abi_subtype &&
            frm.doc.abi_subtype.includes('Withdrawal Sample')) {

            let has_samples = false;
            frm.doc.items.forEach(function (item) {
                if (item.withdrew_sample_qty > 0) {
                    has_samples = true;
                }
            });

            if (!has_samples) {
                frappe.throw(__('Sample quantities are required for Analysis Batch with Withdrawal Sample'));
            }
        }
    }
});

frappe.ui.form.on('Authority Good Release Item', {
    released_qty: function (frm, cdt, cdn) {
        calculate_remaining_qty(frm, cdt, cdn);
        calculate_net_released_qty(frm, cdt, cdn);
        calculate_totals(frm);
    },

    requested_qty: function (frm, cdt, cdn) {
        calculate_remaining_qty(frm, cdt, cdn);
        calculate_totals(frm);
    },

    shortage_control_qty: function (frm, cdt, cdn) {
        calculate_net_released_qty(frm, cdt, cdn);
        calculate_totals(frm);
    },

    withdrew_sample_qty: function (frm) {
        calculate_totals(frm);
    },

    items_remove: function (frm) {
        calculate_totals(frm);
    }
});

function calculate_remaining_qty(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let remaining = (row.requested_qty || 0) - (row.released_qty || 0);
    frappe.model.set_value(cdt, cdn, 'remaining_qty', Math.max(0, remaining));
}

function toggle_fields_based_on_release_type(frm) {
    if (frm.doc.release_type === 'Lot Release Batch') {
        frm.set_df_property('lrb_subtype', 'hidden', 0);
        frm.set_df_property('abi_subtype', 'hidden', 1);
    } else if (frm.doc.release_type === 'Analysis Batch Inspection') {
        frm.set_df_property('lrb_subtype', 'hidden', 1);
        frm.set_df_property('abi_subtype', 'hidden', 0);
    } else {
        frm.set_df_property('lrb_subtype', 'hidden', 1);
        frm.set_df_property('abi_subtype', 'hidden', 1);
    }
}

function calculate_net_released_qty(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let net_released = (row.released_qty || 0) - (row.shortage_control_qty || 0);
    frappe.model.set_value(cdt, cdn, 'net_released_qty', Math.max(0, net_released));
}

function calculate_totals(frm) {
    let total_requested = 0;
    let total_released = 0;
    let total_actual = 0;
    let total_net_released = 0;
    let total_shortage_control = 0;
    let total_sample = 0;
    let total_remaining = 0;

    frm.doc.items.forEach(function (item) {
        total_requested += item.requested_qty || 0;
        total_released += item.released_qty || 0;
        total_actual += item.actual_quantity || 0;  // Changed from actual_qty to actual_quantity
        total_net_released += item.net_released_qty || 0;
        total_shortage_control += item.shortage_control_qty || 0;
        total_sample += item.withdrew_sample_qty || 0;
        total_remaining += item.remaining_qty || 0;
    });

    frm.set_value('total_requested_qty', total_requested);
    frm.set_value('total_released_qty', total_released);
    frm.set_value('total_actual_qty', total_actual);
    frm.set_value('total_net_released_qty', total_net_released);
    frm.set_value('total_shortage_control_qty', total_shortage_control);
    frm.set_value('total_sample_qty', total_sample);
    frm.set_value('total_remaining_qty', total_remaining);
}

function fetch_items_from_purchase_receipt_report(frm) {
    if (!frm.doc.shipment_no) {
        frappe.throw(__('Please select a Shipment first'));
    }

    frappe.call({
        method: "onco.onco.doctype.authority_good_release.authority_good_release.fetch_items_from_purchase_receipt_report",
        args: {
            shipment_no: frm.doc.shipment_no
        },
        callback: function (r) {
            if (r.message) {
                // Clear existing items
                frm.clear_table('items');

                // Add items from Purchase Receipt Report
                r.message.forEach(function (item) {
                    let child = frm.add_child('items');
                    child.item_code = item.item_code;
                    child.item_name = item.item_name;
                    child.batch_no = item.batch_no;
                    child.serial_no = item.serial_no;
                    child.serial_and_batch_bundle = item.serial_and_batch_bundle;
                    child.use_serial_batch_fields = item.use_serial_batch_fields;
                    child.manufacturing_date = item.manufacturing_date;
                    child.expiry_date = item.expiry_date;
                    child.actual_quantity = item.actual_quantity;
                    child.requested_qty = item.actual_quantity; // Auto-populate from actual_quantity
                    child.released_qty = 0; // User will edit this before submission
                });

                frm.refresh_field('items');
                calculate_totals(frm);
                frappe.msgprint(__('Items fetched successfully'));
            }
        }
    });
}