// Copyright (c) 2026, Onco and contributors
// For license information, please see license.txt

// List View Settings
frappe.listview_settings['Importation Approvals'] = {
    add_fields: ["approval_type", "date", "valid_date", "docstatus"],
    get_indicator: function(doc) {
        if (doc.docstatus === 1) {
            return [__("Submitted"), "green", "docstatus,=,1"];
        } else if (doc.docstatus === 2) {
            return [__("Cancelled"), "red", "docstatus,=,2"];
        } else {
            return [__("Draft"), "gray", "docstatus,=,0"];
        }
    }
};

frappe.ui.form.on('Importation Approvals', {
    refresh: function(frm) {
        // Add custom buttons based on document status
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Create Purchase Order'), function() {
                create_purchase_order(frm);
            }, __('Create'));
            
            frm.add_custom_button(__('Create Modification'), function() {
                create_modification(frm);
            }, __('Create'));
            
            frm.add_custom_button(__('Create Extension'), function() {
                create_extension(frm);
            }, __('Create'));
        }
    },
    
    approval_type: function(frm) {
        // Clear importation approval request when approval type changes
        if (frm.doc.importation_approval_request) {
            frm.set_value('importation_approval_request', '');
            frm.clear_table('items');
            frm.refresh_field('items');
        }
        
        // Update filter for importation approval request
        frm.set_query('importation_approval_request', function() {
            let filters = {
                'docstatus': 1  // Only submitted requests
            };
            
            if (frm.doc.approval_type === 'Special Importation (SPIMA)') {
                filters['request_type'] = 'Special Importation (SPIMR)';
            } else if (frm.doc.approval_type === 'Annual Importation (APIMA)') {
                filters['request_type'] = 'Annual Importation (APIMR)';
            }
            
            return {
                filters: filters
            };
        });
    },
    
    importation_approval_request: function(frm) {
        if (frm.doc.importation_approval_request) {
            // Fetch items from the linked request
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Importation Approval Request",
                    name: frm.doc.importation_approval_request
                },
                callback: function(r) {
                    if (r.message) {
                        let request_doc = r.message;
                        
                        // Set approval type based on request type
                        if (request_doc.request_type === 'Special Importation (SPIMR)') {
                            frm.set_value('approval_type', 'Special Importation (SPIMA)');
                        } else if (request_doc.request_type === 'Annual Importation (APIMR)') {
                            frm.set_value('approval_type', 'Annual Importation (APIMA)');
                        }
                        
                        // Clear existing items and add from request
                        frm.clear_table('items');
                        
                        if (request_doc.items && request_doc.items.length > 0) {
                            request_doc.items.forEach(function(item) {
                                // Add all items from request, not just approved ones
                                let child = frm.add_child('items');
                                child.item_code = item.item_code;
                                child.item_name = item.item_name;
                                child.supplier = item.supplier;
                                child.requested_qty = item.requested_qty;
                                // Set approved_qty to requested_qty as per HTML requirement
                                // "QUANTIY: AUTIMATICALLY FROM PERVIOUS STEP"
                                child.approved_qty = item.requested_qty;
                                child.status = 'Approved';
                            });
                            
                            frm.refresh_field('items');
                            frappe.msgprint(__('Items loaded successfully from Importation Approval Request'));
                        } else {
                            frappe.msgprint(__('No items found in the selected Importation Approval Request'));
                        }
                    }
                }
            });
        } else {
            // Clear items when request is cleared
            frm.clear_table('items');
            frm.refresh_field('items');
        }
    },
    
    onload: function(frm) {
        // Set up filtration for importation approval request based on type
        frm.set_query('importation_approval_request', function() {
            let filters = {
                'docstatus': 1  // Only submitted requests
            };
            
            // Filter based on approval type if already set
            if (frm.doc.approval_type) {
                if (frm.doc.approval_type === 'Special Importation (SPIMA)') {
                    filters['request_type'] = 'Special Importation (SPIMR)';
                } else if (frm.doc.approval_type === 'Annual Importation (APIMA)') {
                    filters['request_type'] = 'Annual Importation (APIMR)';
                }
            }
            
            return {
                filters: filters
            };
        });
        
        // Set up item filtration based on pharmaceutical configuration
        if (frm.fields_dict.items && frm.fields_dict.items.grid) {
            frm.fields_dict.items.grid.get_field('item_code').get_query = function() {
                let filters = {};
                
                // Filter for pharmaceutical items as per HTML requirements
                filters['custom_pharmaceutical_item'] = 1;
                filters['disabled'] = 0;  // Only active items
                
                // Additional filtration based on approval type and pharmaceutical configuration
                if (frm.doc.approval_type === 'Annual Importation (APIMA)') {
                    // For annual approvals, only registered pharmaceutical items
                    filters['custom_registered'] = 1;
                } else if (frm.doc.approval_type === 'Special Importation (SPIMA)') {
                    // For special approvals, allow all pharmaceutical items
                }
                
                return {
                    filters: filters
                };
            };
        }
        
        // Make quantity fields read-only after submission
        if (frm.doc.docstatus === 1) {
            frm.fields_dict.items.grid.get_field('approved_qty').read_only = 1;
            frm.refresh_field('items');
        }
    },
    
    before_submit: function(frm) {
        // Validate that items table is not empty
        if (!frm.doc.items || frm.doc.items.length === 0) {
            frappe.throw(__('Items table cannot be empty. Please ensure items are loaded from the Importation Approval Request.'));
        }
        
        // Validate that all items have approved quantities (can be 0 for refused items)
        let has_valid_items = false;
        frm.doc.items.forEach(function(item) {
            if (item.approved_qty >= 0) {  // Allow 0 for refused items
                has_valid_items = true;
            }
        });
        
        if (!has_valid_items) {
            frappe.throw(__('Please ensure all items have valid approved quantities (can be 0 for refused items)'));
        }
        
        // Validate valid date is in the future
        if (frm.doc.valid_date && frm.doc.valid_date <= frappe.datetime.get_today()) {
            frappe.throw(__('Valid Date must be in the future'));
        }
    }
});

frappe.ui.form.on('Importation Approvals Item', {
    approved_qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        // Validate approved quantity doesn't exceed requested quantity
        if (row.approved_qty > row.requested_qty) {
            frappe.model.set_value(cdt, cdn, 'approved_qty', row.requested_qty);
            frappe.msgprint(__('Approved quantity cannot exceed requested quantity'));
        }
        
        // Update status based on approved quantity
        if (row.approved_qty === 0) {
            frappe.model.set_value(cdt, cdn, 'status', 'Refused');
        } else if (row.approved_qty === row.requested_qty) {
            frappe.model.set_value(cdt, cdn, 'status', 'Approved');
        } else {
            frappe.model.set_value(cdt, cdn, 'status', 'Partially Approved');
        }
    },
    
    items_add: function(frm, cdt, cdn) {
        // Prevent adding items if document is submitted
        if (frm.doc.docstatus === 1) {
            frappe.throw(__('Cannot add items to submitted document'));
        }
    }
});

// Prevent editing of quantities after submission
frappe.ui.form.on('Importation Approvals', {
    onload: function(frm) {
        if (frm.doc.docstatus === 1) {
            // Make quantity fields read-only after submission
            frm.fields_dict.items.grid.get_field('approved_qty').read_only = 1;
            frm.refresh_field('items');
        }
    }
});

function create_purchase_order(frm) {
    // Critical validation: Check document status before creating Purchase Order
    if (frm.doc.docstatus !== 1) {
        frappe.throw(__('Document must be submitted before creating Purchase Order'));
        return;
    }
    
    // Critical validation: Check if document is closed due to modification/extension
    if (frm.doc.docstatus === 2) {
        frappe.throw(__('Cannot create Purchase Order from closed document. This document has been modified or extended. Please use the latest version.'));
        return;
    }
    
    // Check if this document has been superseded by a newer version
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Importation Approvals',
            filters: {
                'original_document': frm.doc.name,
                'docstatus': ['!=', 2]
            },
            fields: ['name', 'creation']
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                frappe.throw(__('Cannot create Purchase Order. This document has been superseded by newer versions. Please use the latest version.'));
                return;
            }
            
            // If all validations pass, create the Purchase Order
            frappe.model.open_mapped_doc({
                method: "onco.onco.doctype.importation_approvals.importation_approvals.make_purchase_order",
                frm: frm
            });
        }
    });
}

function create_modification(frm) {
    frappe.prompt([
        {
            label: 'Modification Reason',
            fieldname: 'modification_reason',
            fieldtype: 'Select',
            options: '\nError\nChange data and conditions',
            reqd: 1
        },
        {
            label: 'Requested Modification',
            fieldname: 'requested_modification',
            fieldtype: 'Text',
            reqd: 1
        },
        {
            label: 'New Conditions',
            fieldname: 'new_conditions',
            fieldtype: 'Text'
        }
    ], function(values) {
        frappe.call({
            method: "onco.onco.doctype.importation_approvals.importation_approvals.create_modification",
            args: {
                source_name: frm.doc.name,
                modification_reason: values.modification_reason,
                requested_modification: values.requested_modification,
                new_conditions: values.new_conditions
            },
            callback: function(r) {
                if (r.message) {
                    frappe.set_route('Form', 'Importation Approvals', r.message);
                }
            }
        });
    }, __('Create Modification'), __('Create'));
}

function create_extension(frm) {
    frappe.prompt([
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
            fieldtype: 'Text',
            reqd: 1
        },
        {
            label: 'New Validation Date',
            fieldname: 'new_validation_date',
            fieldtype: 'Date',
            reqd: 1
        },
        {
            label: 'New Quantity',
            fieldname: 'new_quantity',
            fieldtype: 'Float'
        }
    ], function(values) {
        frappe.call({
            method: "onco.onco.doctype.importation_approvals.importation_approvals.create_extension",
            args: {
                source_name: frm.doc.name,
                extension_reason: values.extension_reason,
                extension_details: values.extension_details,
                new_validation_date: values.new_validation_date,
                new_quantity: values.new_quantity
            },
            callback: function(r) {
                if (r.message) {
                    frappe.set_route('Form', 'Importation Approvals', r.message);
                }
            }
        });
    }, __('Create Extension'), __('Create'));
}