frappe.ui.form.on('Purchase Order', {
    refresh: function (frm) {
        if (frm.doc.docstatus === 0) {
            // Remove incorrect/singular button if it likely exists from other scripts
            frm.remove_custom_button('Importation Approval', 'Get Items From');

            frm.add_custom_button(__('Importation Approvals'), function () {
                erpnext.utils.map_current_doc({
                    method: "onco.onco.doctype.importation_approvals.importation_approvals.make_purchase_order",
                    source_doctype: "Importation Approvals",
                    target: frm,
                    setters: {
                        supplier: frm.doc.supplier,
                        schedule_date: undefined
                    },
                    get_query: function () {
                        return {
                            filters: {
                                docstatus: 1
                            }
                        };
                    }
                })
            }, __("Get Items From"));

            frm.add_custom_button(__('Importation Approval Request'), function () {
                erpnext.utils.map_current_doc({
                    method: "onco.onco.doctype.importation_approval_request.importation_approval_request.make_purchase_order",
                    source_doctype: "Importation Approval Request",
                    target: frm,
                    setters: {
                        supplier: frm.doc.supplier,
                        schedule_date: undefined
                    },
                    get_query: function () {
                        return {
                            filters: {
                                docstatus: 1
                            }
                        };
                    }
                })
            }, __("Get Items From"));
        }

        // Optional: Filter the Link field to show only 'Approved' Supplier Quotations or specific series
        if (frm.fields_dict['custom_importation_approval']) {
            frm.set_query('custom_importation_approval', function () {
                return {
                    filters: [
                        ['Supplier Quotation', 'naming_series', 'in', ['EDA-SPIMA-.YYYY.-', 'EDA-APIMA-.YYYY.-']],
                        ['Supplier Quotation', 'docstatus', '!=', 2] // Not cancelled
                    ]
                };
            });
        }

        // Filter item_code in child table to only pharmaceutical items matching PO supplier
        if (frm.doc.supplier && frm.fields_dict.items && frm.fields_dict.items.grid) {
            frm.fields_dict.items.grid.get_field('item_code').get_query = function () {
                return {
                    filters: [
                        ['Item', 'custom_pharmaceutical_item', '=', 1],
                        ['Item', 'disabled', '=', 0],
                        [
                            ['Item', 'default_supplier', '=', frm.doc.supplier],
                            'OR',
                            ['Item Supplier', 'supplier', '=', frm.doc.supplier]
                        ]
                    ]
                };
            };
        }
    },

    supplier: function (frm) {
        if (frm.doc.supplier && frm.fields_dict.items && frm.fields_dict.items.grid) {
            frm.fields_dict.items.grid.get_field('item_code').get_query = function () {
                return {
                    filters: [
                        ['Item', 'custom_pharmaceutical_item', '=', 1],
                        ['Item', 'disabled', '=', 0],
                        [
                            ['Item', 'default_supplier', '=', frm.doc.supplier],
                            'OR',
                            ['Item Supplier', 'supplier', '=', frm.doc.supplier]
                        ]
                    ]
                };
            };
        }
    },

    custom_importation_approval: function (frm) {
        if (frm.doc.custom_importation_approval) {
            // Auto-fill IMP No (aian) with the ID of the selected Approval
            // Assuming 'aian' is the field for IMP No as per previous analysis
            frm.set_value('aian', frm.doc.custom_importation_approval);

            // Optionally fetch other details if needed, e.g. Supplier
            frappe.db.get_value('Supplier Quotation', frm.doc.custom_importation_approval, 'supplier')
                .then(r => {
                    if (r.message && r.message.supplier && !frm.doc.supplier) {
                        frm.set_value('supplier', r.message.supplier);
                    }
                });
        } else {
            frm.set_value('aian', '');
        }
    }
});
