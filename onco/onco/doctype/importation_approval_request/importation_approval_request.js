// Copyright (c) 2026, Onco and contributors
// For license information, please see license.txt

// List View Settings
frappe.listview_settings['Importation Approval Request'] = {
    add_fields: ["request_type", "status", "date", "docstatus"],
    get_indicator: function (doc) {
        if (doc.status === "Totally Approved") {
            return [__("Totally Approved"), "green", "status,=,Totally Approved"];
        } else if (doc.status === "Partially Approved") {
            return [__("Partially Approved"), "orange", "status,=,Partially Approved"];
        } else if (doc.status === "Refused") {
            return [__("Refused"), "red", "status,=,Refused"];
        } else if (doc.status === "Pending") {
            return [__("Pending"), "blue", "status,=,Pending"];
        } else if (doc.status === "Closed - Modified") {
            return [__("Closed - Modified"), "gray", "status,=,Closed - Modified"];
        } else if (doc.status === "Closed - Extended") {
            return [__("Closed - Extended"), "gray", "status,=,Closed - Extended"];
        } else {
            return [__("Draft"), "gray", "docstatus,=,0"];
        }
    }
};

frappe.ui.form.on('Importation Approval Request', {
    refresh: function (frm) {
        // Add custom buttons based on document status
        if (frm.doc.docstatus === 1) {
            // Only show approval buttons if status is still Pending
            if (frm.doc.status === "Pending") {
                frm.add_custom_button(__('Approve Request'), function () {
                    show_approval_dialog(frm);
                }, __('Actions'));

                frm.add_custom_button(__('Refuse Request'), function () {
                    frappe.confirm(
                        __('Are you sure you want to refuse this request?'),
                        function () {
                            frappe.call({
                                method: "onco.onco.doctype.importation_approval_request.importation_approval_request.approve_request",
                                args: {
                                    docname: frm.doc.name,
                                    approval_type: "Refused"
                                },
                                callback: function (r) {
                                    frm.reload_doc();
                                }
                            });
                        }
                    );
                }, __('Actions'));
            }

            // Show create buttons only if approved
            if (frm.doc.status === "Totally Approved" || frm.doc.status === "Partially Approved") {
                frm.add_custom_button(__('Create Importation Approval'), function () {
                    create_importation_approval(frm);
                }, __('Create'));
            }

            frm.add_custom_button(__('Create Modification'), function () {
                create_modification(frm);
            }, __('Create'));

            frm.add_custom_button(__('Create Extension'), function () {
                create_extension(frm);
            }, __('Create'));
        }
    },

    request_type: function (frm) {
        // Clear items when request type changes to ensure proper filtration
        if (frm.doc.items && frm.doc.items.length > 0) {
            frm.clear_table('items');
            frm.refresh_field('items');
        }
    },

    onload: function (frm) {
        // Set up item filtration based on request type and pharmaceutical requirements
        frm.fields_dict.items.grid.get_field('item_code').get_query = function () {
            let filters = {};

            // Filter for pharmaceutical items as per HTML requirements
            filters['custom_pharmaceutical_item'] = 1;
            filters['disabled'] = 0;  // Only active items

            // Critical filtration based on pharmaceutical item configuration
            if (frm.doc.request_type === 'Annual Importation (APIMR)') {
                // For annual requests, only registered pharmaceutical items with complete data
                // Based on HTML requirement: registered items need batch, manufacturing date, expiry date
                filters['custom_registered'] = 1;
                // Could add additional filters to ensure complete pharmaceutical data
                // filters['custom_batch_no'] = ['!=', ''];
                // filters['custom_manufacturing_date'] = ['!=', ''];
                // filters['custom_expiry_date'] = ['!=', ''];
            } else if (frm.doc.request_type === 'Special Importation (SPIMR)') {
                // For special requests, allow both registered and non-registered pharmaceutical items
                // This gives more flexibility for special/emergency importations
                // No additional filters beyond pharmaceutical_item = 1
            }

            return {
                filters: filters
            };
        };
    },

    before_submit: function (frm) {
        // Validate that all items have requested quantities
        let has_items = false;
        frm.doc.items.forEach(function (item) {
            if (item.requested_qty > 0) {
                has_items = true;
            }
        });

        if (!has_items) {
            frappe.throw(__('Please add at least one item with requested quantity'));
        }
    }
});

frappe.ui.form.on('Importation Approval Request Item', {
    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            // Validate pharmaceutical item requirements
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Item',
                    name: row.item_code
                },
                callback: function (r) {
                    if (r.message) {
                        let item = r.message;

                        // Fetch supplier from Item's supplier_items child table
                        if (item.supplier_items && item.supplier_items.length > 0) {
                            frappe.model.set_value(cdt, cdn, 'supplier', item.supplier_items[0].supplier);
                        } else {
                            frappe.model.set_value(cdt, cdn, 'supplier', '');
                        }

                        // Check if it's a pharmaceutical item
                        if (item.custom_pharmaceutical_item) {
                            // Show pharmaceutical item information
                            let info_msg = `<strong>Pharmaceutical Item Details:</strong><br>`;
                            info_msg += `Strength: ${item.strength || 'Not specified'}<br>`;
                            info_msg += `Batch No: ${item.custom_batch_no || 'Not specified'}<br>`;
                            info_msg += `Manufacturing Date: ${item.custom_manufacturing_date || 'Not specified'}<br>`;
                            info_msg += `Expiry Date: ${item.custom_expiry_date || 'Not specified'}<br>`;
                            info_msg += `Registered: ${item.custom_registered ? 'Yes' : 'No'}<br>`;

                            // Check for missing required fields
                            if (item.custom_registered) {
                                let missing = [];
                                if (!item.custom_manufacturing_date) missing.push('Manufacturing Date');
                                if (!item.custom_expiry_date) missing.push('Expiry Date');
                                if (!item.custom_batch_no) missing.push('Batch No');
                                if (!item.strength) missing.push('Strength');

                                if (missing.length > 0) {
                                    info_msg += `<br><span style="color: red;"><strong>Missing Required Fields:</strong> ${missing.join(', ')}</span>`;
                                    frappe.msgprint({
                                        title: 'Pharmaceutical Item Validation',
                                        message: info_msg,
                                        indicator: 'orange'
                                    });
                                } else {
                                    // Check expiry date
                                    if (item.custom_expiry_date && item.custom_expiry_date <= frappe.datetime.get_today()) {
                                        info_msg += `<br><span style="color: red;"><strong>Warning:</strong> Item has expired!</span>`;
                                        frappe.msgprint({
                                            title: 'Pharmaceutical Item Validation',
                                            message: info_msg,
                                            indicator: 'red'
                                        });
                                    } else {
                                        frappe.msgprint({
                                            title: 'Pharmaceutical Item Information',
                                            message: info_msg,
                                            indicator: 'green'
                                        });
                                    }
                                }
                            }
                        }
                    }
                }
            });
        }
    },

    requested_qty: function (frm) {
        calculate_totals(frm);
    },

    approved_qty: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Critical validation: "لا يمكن الكتابة في الكميات الا في حاله الموافقة الجزئية"
        // (Can only edit quantities in partial approval case)

        // If document is submitted, prevent any quantity editing
        if (frm.doc.docstatus === 1) {
            frappe.msgprint(__('Cannot edit quantities in submitted document'));
            frappe.model.set_value(cdt, cdn, 'approved_qty', row.approved_qty || 0);
            return;
        }

        // Enforce quantity editing restrictions based on approval status
        if (frm.doc.approval_status === 'Totally Approved') {
            // In total approval, quantity transfers automatically
            frappe.model.set_value(cdt, cdn, 'approved_qty', row.requested_qty);
            frappe.msgprint(__('In total approval, quantity transfers automatically. Cannot edit approved quantity.'));
            return;
        }

        if (frm.doc.approval_status === 'Refused') {
            // In refused status, quantity must be 0
            frappe.model.set_value(cdt, cdn, 'approved_qty', 0);
            frappe.msgprint(__('Cannot edit quantities for refused requests.'));
            return;
        }

        // Only allow editing in partial approval or pending status
        if (frm.doc.approval_status &&
            frm.doc.approval_status !== 'Partially Approved' &&
            frm.doc.approval_status !== 'Pending' &&
            frm.doc.approval_status !== '') {
            frappe.msgprint(__('Quantity editing is only allowed in partial approval cases or pending status.'));
            // Revert to previous value
            frappe.model.set_value(cdt, cdn, 'approved_qty', row.approved_qty || 0);
            return;
        }

        // Validate approved quantity doesn't exceed requested quantity
        if (row.approved_qty > row.requested_qty) {
            frappe.msgprint(__('Approved quantity cannot exceed requested quantity'));
            frappe.model.set_value(cdt, cdn, 'approved_qty', row.requested_qty);
            return;
        }

        calculate_totals(frm);
    },

    items_remove: function (frm) {
        calculate_totals(frm);
    }
});

function calculate_totals(frm) {
    let total_requested = 0;
    let total_approved = 0;

    frm.doc.items.forEach(function (item) {
        total_requested += item.requested_qty || 0;
        total_approved += item.approved_qty || 0;
    });

    frm.set_value('total_requested_qty', total_requested);
    frm.set_value('total_approved_qty', total_approved);
}

function create_importation_approval(frm) {
    frappe.model.open_mapped_doc({
        method: "onco.onco.doctype.importation_approval_request.importation_approval_request.make_importation_approval",
        frm: frm
    });
}

function create_modification(frm) {
    // Show current items for reference
    let items_html = '<table class="table table-bordered"><thead><tr><th>Item</th><th>Current Qty</th><th>New Qty</th></tr></thead><tbody>';
    frm.doc.items.forEach(function (item) {
        items_html += `<tr><td>${item.item_code}</td><td>${item.requested_qty}</td><td><input type="number" class="form-control" data-item="${item.item_code}" value="${item.requested_qty}"></td></tr>`;
    });
    items_html += '</tbody></table>';

    let d = new frappe.ui.Dialog({
        title: __('Create Modification'),
        fields: [
            {
                label: 'Modification Reason',
                fieldname: 'modification_reason',
                fieldtype: 'Select',
                options: '\nError\nChange data and conditions',
                reqd: 1
            },
            {
                label: 'Requested Modification Details',
                fieldname: 'requested_modification',
                fieldtype: 'Small Text',
                reqd: 1,
                description: 'Describe what needs to be modified'
            },
            {
                label: 'Modify Item Quantities',
                fieldname: 'items_section',
                fieldtype: 'HTML',
                options: items_html
            }
        ],
        primary_action_label: __('Create Modification'),
        primary_action: function (values) {
            // Collect modified quantities
            let items_to_modify = {};
            d.$wrapper.find('input[data-item]').each(function () {
                let item_code = $(this).data('item');
                let new_qty = parseFloat($(this).val()) || 0;
                items_to_modify[item_code] = { new_qty: new_qty };
            });

            frappe.call({
                method: "onco.onco.doctype.importation_approval_request.importation_approval_request.create_modification",
                args: {
                    source_name: frm.doc.name,
                    modification_reason: values.modification_reason,
                    requested_modification: values.requested_modification,
                    items_to_modify: JSON.stringify(items_to_modify)
                },
                callback: function (r) {
                    if (r.message) {
                        d.hide();
                        frappe.msgprint(__('Modification created successfully'));
                        frappe.set_route('Form', 'Importation Approval Request', r.message);
                    }
                }
            });
        }
    });

    d.show();
}

function create_extension(frm) {
    // Show current items for reference
    let items_html = '<table class="table table-bordered"><thead><tr><th>Item</th><th>Current Qty</th><th>Additional Qty</th></tr></thead><tbody>';
    frm.doc.items.forEach(function (item) {
        items_html += `<tr><td>${item.item_code}</td><td>${item.requested_qty}</td><td><input type="number" class="form-control" data-item="${item.item_code}" value="0" min="0"></td></tr>`;
    });
    items_html += '</tbody></table>';

    let d = new frappe.ui.Dialog({
        title: __('Create Extension'),
        fields: [
            {
                label: 'Extension Reason',
                fieldname: 'extension_reason',
                fieldtype: 'Select',
                options: '\nValidation\nOther',
                reqd: 1
            },
            {
                label: 'Extension Details',
                fieldname: 'extension_details',
                fieldtype: 'Small Text',
                reqd: 1,
                description: 'Describe why extension is needed'
            },
            {
                label: 'New Validation Date',
                fieldname: 'new_validation_date',
                fieldtype: 'Date',
                description: 'Optional: Set new validation date'
            },
            {
                label: 'Add Additional Quantities',
                fieldname: 'items_section',
                fieldtype: 'HTML',
                options: items_html
            }
        ],
        primary_action_label: __('Create Extension'),
        primary_action: function (values) {
            // Collect additional quantities
            let additional_qty = {};
            d.$wrapper.find('input[data-item]').each(function () {
                let item_code = $(this).data('item');
                let add_qty = parseFloat($(this).val()) || 0;
                if (add_qty > 0) {
                    additional_qty[item_code] = { additional_qty: add_qty };
                }
            });

            frappe.call({
                method: "onco.onco.doctype.importation_approval_request.importation_approval_request.create_extension",
                args: {
                    source_name: frm.doc.name,
                    extension_reason: values.extension_reason,
                    extension_details: values.extension_details,
                    new_validation_date: values.new_validation_date,
                    additional_qty: JSON.stringify(additional_qty)
                },
                callback: function (r) {
                    if (r.message) {
                        d.hide();
                        frappe.msgprint(__('Extension created successfully'));
                        frappe.set_route('Form', 'Importation Approval Request', r.message);
                    }
                }
            });
        }
    });

    d.show();
}


function show_approval_dialog(frm) {
    // Prepare items HTML for the dialog
    let items_html = `
        <div id="approval_items_container" style="display: none;">
            <div style="margin-bottom: 10px; font-weight: bold;" id="approval_summary_text">
                Total Requested: ${frm.doc.total_requested_qty || 0} | Total Approved: <span id="dialog_total_approved">0</span>
            </div>
            <div style="max-height: 300px; overflow-y: auto;">
                <table class="table table-bordered table-condensed">
                    <thead>
                        <tr>
                            <th style="width: 40%">${__("Item")}</th>
                            <th style="width: 30%">${__("Requested Qty")}</th>
                            <th style="width: 30%">${__("Approved Qty")}</th>
                        </tr>
                    </thead>
                    <tbody>`;

    frm.doc.items.forEach(function (item) {
        items_html += `
            <tr>
                <td>${item.item_code}</td>
                <td class="text-right">${item.requested_qty}</td>
                <td>
                    <input type="number" class="form-control input-sm text-right approved-qty-input" 
                           data-item="${item.item_code}" 
                           data-requested="${item.requested_qty}"
                           value="${item.requested_qty}" 
                           min="0" 
                           max="${item.requested_qty}">
                </td>
            </tr>`;
    });

    items_html += `
                    </tbody>
                </table>
            </div>
        </div>`;

    let d = new frappe.ui.Dialog({
        title: __('Approve Request'),
        fields: [
            {
                label: 'Approval Type',
                fieldname: 'approval_type',
                fieldtype: 'Select',
                options: 'Totally Approved\nPartially Approved\nRefused',
                default: 'Totally Approved',
                reqd: 1,
                onchange: function () {
                    let approval_type = d.get_value('approval_type');
                    let $container = d.$wrapper.find('#approval_items_container');

                    if (approval_type === 'Partially Approved') {
                        $container.show();
                        // Reset inputs to requested qty initially or 0? 
                        // User manual behavior implies we might start with full or empty. 
                        // Let's start with requested qty to make it easier to just reduce some.
                        d.$wrapper.find('.approved-qty-input').each(function () {
                            $(this).val($(this).data('requested')).prop('disabled', false);
                        });
                        update_dialog_totals();
                    } else if (approval_type === 'Totally Approved') {
                        $container.hide();
                    } else if (approval_type === 'Refused') {
                        $container.hide();
                    }
                }
            },
            {
                fieldname: 'items_section',
                fieldtype: 'HTML',
                options: items_html
            },
            {
                label: 'Note',
                fieldname: 'note',
                fieldtype: 'Small Text'
            }
        ],
        primary_action_label: __('Approve'),
        primary_action: function (values) {
            let items_data = {};

            if (values.approval_type === 'Partially Approved') {
                let total_approved = 0;
                d.$wrapper.find('.approved-qty-input').each(function () {
                    let item_code = $(this).data('item');
                    let qty = parseFloat($(this).val()) || 0;
                    let max_qty = parseFloat($(this).data('requested'));

                    if (qty > max_qty) {
                        frappe.msgprint(__("Approved quantity for {0} cannot exceed requested quantity: {1}", [item_code, max_qty]));
                        throw "Invalid Quantity";
                    }

                    items_data[item_code] = qty;
                    total_approved += qty;
                });

                if (total_approved === 0 && values.approval_type === 'Partially Approved') {
                    // Maybe warn if all are zero? But hypothetically valid if they want to approve 0 items but keep it open?
                    // Actually user request implies we want to specify quantities.
                }
            } else if (values.approval_type === 'Totally Approved') {
                // No specific item data needed, server handles it, 
                // BUT current server logic for 'Totally Approved' loops over doc.items.
                // We don't strictly pass items_data for Total/Refused unless we want to be explicit.
            }

            frappe.call({
                method: "onco.onco.doctype.importation_approval_request.importation_approval_request.approve_request",
                args: {
                    docname: frm.doc.name,
                    approval_type: values.approval_type,
                    items_data: values.approval_type === 'Partially Approved' ? JSON.stringify(items_data) : null
                },
                freeze: true,
                callback: function (r) {
                    d.hide();
                    frm.reload_doc();
                }
            });
        }
    });

    // Helper functionality for the dialog
    function update_dialog_totals() {
        let total = 0;
        d.$wrapper.find('.approved-qty-input').each(function () {
            total += parseFloat($(this).val()) || 0;
        });
        d.$wrapper.find('#dialog_total_approved').text(total);
    }

    // Bind change event to inputs
    d.$wrapper.on('change input', '.approved-qty-input', function () {
        update_dialog_totals();
    });

    d.show();

    // Initial state trigger
    d.$wrapper.find('#approval_items_container').hide(); // Hidden by default for Totally Approved
}
