// Copyright (c) 2026, Onco and contributors
// For license information, please see license.txt

frappe.ui.form.on('Incoming Check Report', {
    refresh: function (frm) {
        // Calculate totals on refresh
        calculate_totals(frm);

        // Set default inspector if not set
        if (!frm.doc.inspector_name && frappe.session.user) {
            frm.set_value('inspector_name', frappe.session.user);
        }
        
        // Add button to view created Stock Entries if submitted
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('View Stock Entries'), function() {
                frappe.route_options = {
                    "custom_purchase_receipt": frm.doc.purchase_receipt,
                    "docstatus": 1,
                    "posting_date": [">=", frm.doc.inspection_date]
                };
                frappe.set_route("List", "Stock Entry");
            }, __('View'));
            
            // Add button to create Purchase Receipt Report
            frappe.db.get_value('Purchase Receipt Report', 
                {'purchase_receipt': frm.doc.purchase_receipt}, 
                'name',
                (r) => {
                    if (!r || !r.name) {
                        // No Purchase Receipt Report exists, show create button
                        frm.add_custom_button(__('Create Purchase Receipt Report'), function() {
                            frappe.model.open_mapped_doc({
                                method: "onco.onco.doctype.incoming_check_report.incoming_check_report.make_purchase_receipt_report",
                                frm: frm
                            });
                        }, __('Create'));
                    } else {
                        // Purchase Receipt Report exists, show view button
                        frm.add_custom_button(__('View Purchase Receipt Report'), function() {
                            frappe.set_route('Form', 'Purchase Receipt Report', r.name);
                        }, __('View'));
                    }
                }
            );
            
            // Add button to create Authority Good Release
            frm.add_custom_button(__('Create Authority Good Release'), function() {
                frappe.model.open_mapped_doc({
                    method: "onco.onco.doctype.incoming_check_report.incoming_check_report.make_authority_good_release",
                    frm: frm
                });
            }, __('Create'));
        }
    },

    stock_entry: function (frm) {
        if (frm.doc.stock_entry) {
            // Fetch all reference data from Stock Entry
            fetch_reference_data(frm);

            // Fetch items from Stock Entry
            fetch_items_from_stock_entry(frm);
        }
    },

    data_logger_present: function (frm) {
        // Show/hide temperature fields based on data logger presence
        if (frm.doc.data_logger_present === 'No') {
            frm.set_value('temperature_range_status', '');
            frm.set_value('out_of_range_action', '');
            frm.set_value('acceptance_reason', '');
        }
    },

    temperature_range_status: function (frm) {
        // Clear out-of-range action if in-range
        if (frm.doc.temperature_range_status === 'In-Range') {
            frm.set_value('out_of_range_action', '');
            frm.set_value('acceptance_reason', '');
        }
    },

    out_of_range_action: function (frm) {
        // Clear acceptance reason if quarantine selected
        if (frm.doc.out_of_range_action === 'Quarantine and Notify QA') {
            frm.set_value('acceptance_reason', '');
        }
    },

    inspection_result: function (frm) {
        // Auto-set inspection result based on checks
        update_inspection_result(frm);
    },

    send_shipment_receipt_notification: function (frm) {
        // Auto-populate email from supplier if not set
        if (frm.doc.send_shipment_receipt_notification && !frm.doc.notification_email) {
            if (frm.doc.purchase_invoice) {
                frappe.db.get_value('Purchase Invoice', frm.doc.purchase_invoice, 'supplier')
                    .then(r => {
                        if (r.message && r.message.supplier) {
                            frappe.db.get_value('Supplier', r.message.supplier, 'email_id')
                                .then(email_r => {
                                    if (email_r.message && email_r.message.email_id) {
                                        frm.set_value('notification_email', email_r.message.email_id);
                                    }
                                });
                        }
                    });
            }
        }
    },

    before_submit: function (frm) {
        // Validate all required checks before submission
        validate_inspection_completion(frm);
    }
});

// Item table events
frappe.ui.form.on('Incoming Check Report Item', {
    received_quantity: function (frm, cdt, cdn) {
        calculate_accepted_quantity(frm, cdt, cdn);
        calculate_totals(frm);
    },

    invoice_quantity: function (frm, cdt, cdn) {
        calculate_totals(frm);
    },

    over_quantity: function (frm, cdt, cdn) {
        calculate_accepted_quantity(frm, cdt, cdn);
        calculate_totals(frm);
    },

    damage_quantity: function (frm, cdt, cdn) {
        calculate_accepted_quantity(frm, cdt, cdn);
        calculate_totals(frm);
    },

    item_code: function (frm, cdt, cdn) {
        // Fetch item name when item code changes
        let row = locals[cdt][cdn];
        if (row.item_code) {
            frappe.db.get_value('Item', row.item_code, 'item_name', (r) => {
                if (r && r.item_name) {
                    frappe.model.set_value(cdt, cdn, 'item_name', r.item_name);
                }
            });
        }
    },

    items_remove: function (frm) {
        calculate_totals(frm);
    }
});

// Helper Functions

function fetch_reference_data(frm) {
    if (!frm.doc.stock_entry) return;

    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Stock Entry',
            name: frm.doc.stock_entry
        },
        callback: function (r) {
            if (r.message) {
                let stock_entry = r.message;

                // Set inspection warehouse from to_warehouse
                if (stock_entry.to_warehouse) {
                    frm.set_value('inspection_warehouse', stock_entry.to_warehouse);
                }

                // Try to get Purchase Receipt
                let purchase_receipt = stock_entry.purchase_receipt || stock_entry.custom_purchase_receipt;

                if (purchase_receipt) {
                    frm.set_value('purchase_receipt', purchase_receipt);

                    // Fetch Shipment from Purchase Receipt
                    frappe.db.get_value('Purchase Receipt', purchase_receipt, 'custom_shipment_ref')
                        .then(ship_r => {
                            if (ship_r.message && ship_r.message.custom_shipment_ref) {
                                frm.set_value('shipment', ship_r.message.custom_shipment_ref);

                                // Fetch Purchase Invoice from Shipment
                                frappe.call({
                                    method: 'frappe.client.get',
                                    args: {
                                        doctype: 'Shipments',
                                        name: ship_r.message.custom_shipment_ref
                                    },
                                    callback: function (ship_doc_r) {
                                        if (ship_doc_r.message && ship_doc_r.message.custom_invoices) {
                                            let invoices = ship_doc_r.message.custom_invoices;
                                            if (invoices.length > 0) {
                                                let invoice = invoices[0].purchase_invoice;
                                                frm.set_value('purchase_invoice', invoice);

                                                // Fetch Importation Approval from Purchase Invoice
                                                frappe.db.get_value('Purchase Invoice', invoice, 'custom_importation_approval')
                                                    .then(imp_r => {
                                                        if (imp_r.message && imp_r.message.custom_importation_approval) {
                                                            frm.set_value('importation_approval', imp_r.message.custom_importation_approval);
                                                        }
                                                    });
                                            }
                                        }
                                    }
                                });
                            }
                        });
                }
            }
        }
    });
}

function fetch_items_from_stock_entry(frm) {
    if (!frm.doc.stock_entry) return;

    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Stock Entry',
            name: frm.doc.stock_entry
        },
        callback: function (r) {
            if (r.message && r.message.items) {
                // Clear existing items
                frm.clear_table('items');

                r.message.items.forEach(function (se_item) {
                    let item_code = se_item.item_code;
                    let batch_no = se_item.batch_no;
                    let qty = se_item.qty;

                    // Get item name
                    frappe.db.get_value('Item', item_code, 'item_name', (item_r) => {
                        let item_name = item_r.message ? item_r.message.item_name : '';

                        // Get batch details if batch exists
                        let manufacturing_date = null;
                        let expiry_date = null;

                        if (batch_no) {
                            frappe.db.get_value('Batch', batch_no, ['manufacturing_date', 'expiry_date'], (batch_r) => {
                                if (batch_r.message) {
                                    manufacturing_date = batch_r.message.manufacturing_date;
                                    expiry_date = batch_r.message.expiry_date;
                                }
                            });
                        }

                        // Add item to table
                        let row = frm.add_child('items');
                        row.item_code = item_code;
                        row.item_name = item_name;
                        row.batch_no = batch_no;
                        row.invoice_quantity = qty;
                        row.received_quantity = qty;
                        row.shortage_quantity = 0;
                        row.over_quantity = 0;
                        row.damage_quantity = 0;
                        row.accepted_quantity = qty;
                        row.manufacturing_date = manufacturing_date;
                        row.expiry_date = expiry_date;

                        // Try to get shipment and purchase receipt info
                        if (frm.doc.shipment) {
                            row.shipment_no = frm.doc.shipment;
                        }
                        if (frm.doc.purchase_receipt) {
                            row.invoice_no = frm.doc.purchase_receipt;
                        }

                        frm.refresh_field('items');
                        calculate_totals(frm);
                    });
                });
            }
        }
    });
}

function calculate_shortage_quantity(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    let invoice = row.invoice_quantity || 0;
    let received = row.received_quantity || 0;

    // Shortage = Invoice - Received (if positive)
    row.shortage_quantity = Math.max(0, invoice - received);

    frm.refresh_field('items');
}

function calculate_accepted_quantity(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    let received = row.received_quantity || 0;
    let over = row.over_quantity || 0;
    let damage = row.damage_quantity || 0;

    row.accepted_quantity = received - over - damage;

    // Ensure accepted quantity is not negative
    if (row.accepted_quantity < 0) {
        row.accepted_quantity = 0;
    }

    frm.refresh_field('items');
}

function calculate_totals(frm) {
    let total_invoice = 0;
    let total_received = 0;
    let total_over = 0;
    let total_damage = 0;
    let total_accepted = 0;
    let total_shortage = 0;

    if (frm.doc.items) {
        frm.doc.items.forEach(function (item) {
            total_invoice += item.invoice_quantity || 0;
            total_received += item.received_quantity || 0;
            total_over += item.over_quantity || 0;
            total_damage += item.damage_quantity || 0;
            total_accepted += item.accepted_quantity || 0;
            total_shortage += item.shortage_quantity || 0;
        });
    }

    frm.set_value('total_invoice_qty', total_invoice);
    frm.set_value('total_received_qty', total_received);
    frm.set_value('total_over_qty', total_over);
    frm.set_value('total_damage_qty', total_damage);
    frm.set_value('total_accepted_qty', total_accepted);
    frm.set_value('total_shortage_qty', total_shortage);
}

function update_inspection_result(frm) {
    // Auto-determine inspection result based on checks
    if (frm.doc.out_of_range_action === 'Quarantine and Notify QA') {
        frm.set_value('inspection_result', 'Quarantined');
        return;
    }

    // Check if any physical checks failed
    let physical_checks_ok = (
        frm.doc.seal_integrity_verified &&
        frm.doc.package_condition_ok &&
        frm.doc.labels_verified &&
        frm.doc.quantity_verified
    );

    // Check if all documents are present
    let documents_ok = (
        frm.doc.commercial_invoice_present &&
        frm.doc.packing_list_present &&
        frm.doc.bill_of_lading_present &&
        frm.doc.certificate_of_analysis_present &&
        frm.doc.all_documents_consistent
    );

    if (!physical_checks_ok || !documents_ok) {
        if (!frm.doc.inspection_result || frm.doc.inspection_result === 'Passed') {
            frappe.msgprint(__('Some inspection checks have failed. Please review before setting inspection result.'));
        }
    }
}

function validate_inspection_completion(frm) {
    // Validate that all required inspections are completed

    // Check temperature control if data logger present
    if (frm.doc.data_logger_present === 'Yes') {
        if (!frm.doc.temperature_range_status) {
            frappe.throw(__('Temperature Range Status is required when Data Logger is present'));
        }

        if (frm.doc.temperature_range_status === 'Out-of-Range') {
            if (!frm.doc.out_of_range_action) {
                frappe.throw(__('Out-of-range action is required when temperature is out of range'));
            }

            if (frm.doc.out_of_range_action === 'Accept with Reason' && !frm.doc.acceptance_reason) {
                frappe.throw(__('Acceptance reason is required when accepting out-of-range temperature'));
            }
        }
    }

    // Check inspection result
    if (!frm.doc.inspection_result) {
        frappe.throw(__('Inspection Result is required before submission'));
    }

    // Check warehouse assignment
    if (frm.doc.inspection_result === 'Passed' && !frm.doc.accepted_warehouse) {
        frappe.throw(__('Accepted Warehouse is required when inspection passes'));
    }

    if ((frm.doc.inspection_result === 'Failed' || frm.doc.inspection_result === 'Quarantined') && !frm.doc.rejected_warehouse) {
        frappe.throw(__('Rejected Warehouse is required when inspection fails or goods are quarantined'));
    }

    return true;
}
