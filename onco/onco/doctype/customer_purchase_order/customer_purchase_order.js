frappe.ui.form.on("Customer Purchase Order", {
    refresh(frm) {
        set_customer_main_group_query(frm);
        apply_price_list_filter(frm);
        show_create_sales_order_button(frm);
    },

    onload(frm) {
        set_customer_main_group_query(frm);
    },

    tender(frm) {
        if (!frm.doc.tender || frm.doc.customer_po_items.length > 0) return;
        populate_from_tender(frm);
    },

    customer_main_group(frm) {
        frm.set_value("customer_group", "");
        frm.set_value("customer", "");
        frm.set_query("customer_group", function () {
            if (frm.doc.customer_main_group) {
                return {
                    filters: { "parent_customer_group": frm.doc.customer_main_group }
                };
            }
            return {
                filters: { "is_group": 1 }
            };
        });
    },

    customer_group(frm) {
        frm.set_value("customer", "");
        frm.set_query("customer", function () {
            if (frm.doc.customer_group) {
                return {
                    filters: { "customer_group": frm.doc.customer_group }
                };
            }
        });
    },

    customer(frm) {
        apply_price_list_filter(frm);
    },

    price_list(frm) {
        if (frm.doc.docstatus !== 0) return;
        frappe.call({
            method: "onco.onco.doctype.customer_purchase_order.customer_purchase_order.get_applicable_price_lists",
            args: { customer: frm.doc.customer },
            callback: function () {
                frm.doc.customer_po_items.forEach(row => {
                    fetch_item_price(frm, row);
                });
            }
        });
    }
});

frappe.ui.form.on("Customer PO Items", {
    item(frm, cdt, cdn) {
        if (frm.doc.docstatus !== 0) return;
        const row = locals[cdt][cdn];
        fetch_item_price(frm, row);
    },

    quantity(frm, cdt, cdn) {
        if (frm.doc.docstatus !== 0) return;
        const row = locals[cdt][cdn];
        calculate_row_amount(row);
        calculate_totals(frm);
    },

    price(frm, cdt, cdn) {
        if (frm.doc.docstatus !== 0) return;
        const row = locals[cdt][cdn];
        calculate_row_amount(row);
        calculate_totals(frm);
    },

    customer_po_items_remove(frm) {
        if (frm.doc.docstatus !== 0) return;
        calculate_totals(frm);
    }
});

// ========== Customer Group Filters ==========

function set_customer_main_group_query(frm) {
    frm.set_query("customer_main_group", function () {
        return {
            filters: { "is_group": 1 }
        };
    });
}

function apply_price_list_filter(frm) {
    if (!frm.doc.customer) {
        frm.set_query("price_list", function () {
            return { filters: { selling: 1, enabled: 1 } };
        });
        return;
    }

    frappe.call({
        method: "onco.onco.doctype.customer_purchase_order.customer_purchase_order.get_applicable_price_lists",
        args: { customer: frm.doc.customer },
        callback(r) {
            let price_lists = r.message || [];
            frm.set_query("price_list", function () {
                if (price_lists.length > 0) {
                    return {
                        filters: {
                            name: ["in", price_lists],
                            selling: 1,
                            enabled: 1
                        }
                    };
                }
                return { filters: { name: ["in", []] } };
            });
            frm.refresh_field("price_list");

            if (price_lists.length === 0 && frm.doc.customer) {
                frappe.msgprint({
                    title: __("No Price List Available"),
                    indicator: "orange",
                    message: __(
                        "No price list is configured for customer <b>{0}</b>.<br><br>Please configure price lists in the Price List master by adding this customer or customer group to the applicable price lists.",
                        [frm.doc.customer]
                    )
                });
            }
        }
    });
}

// ========== Item Pricing ==========

function fetch_item_price(frm, row) {
    if (!row.item || !frm.doc.price_list) return;

    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "Item Price",
            filters: { item_code: row.item, price_list: frm.doc.price_list },
            fieldname: ["price_list_rate"]
        },
        callback(r) {
            if (!r.message) return;
            let new_price = flt(r.message.price_list_rate || 0);
            if (flt(row.price) !== new_price) {
                row.price = new_price;
                calculate_row_amount(row);
                frm.refresh_field("customer_po_items");
                calculate_totals(frm);
            }
        }
    });
}

function calculate_row_amount(row) {
    row.amount = flt(row.quantity) * flt(row.price);
}

function calculate_totals(frm) {
    let total_qty = 0;
    let total_amount = 0;
    (frm.doc.customer_po_items || []).forEach(row => {
        total_qty += flt(row.quantity);
        total_amount += flt(row.amount);
    });
    frm.set_value("total_qty", total_qty);
    frm.set_value("total_amount", total_amount);
}

// ========== Populate from Tender ==========

function populate_from_tender(frm) {
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Tenders",
            name: frm.doc.tender
        },
        callback(r) {
            let tender = r.message;
            if (!tender) return;

            let distributors = (tender.tender_supplier || [])
                .filter(row => row.supplier)
                .map(row => row.supplier);

            if (distributors.length === 0) {
                frappe.msgprint(__('No distributors found in the selected tender.'));
                return;
            }

            let dialog = new frappe.ui.Dialog({
                title: __('Select Distributor'),
                fields: [
                    {
                        fieldname: 'distributor',
                        fieldtype: 'Link',
                        label: 'Distributor',
                        options: 'Customer',
                        reqd: 1,
                        get_query: function() {
                            return { filters: [['name', 'in', distributors]] };
                        }
                    },
                    {
                        fieldname: 'delivery_date',
                        fieldtype: 'Date',
                        label: __('Delivery Date'),
                        reqd: 1,
                        default: tender.tender_end_date
                    }
                ],
                primary_action_label: __('Populate'),
                primary_action(values) {
                    let allocations = (tender.tender_supplier_allocations || [])
                        .filter(row => row.distributor === values.distributor);

                    if (allocations.length === 0) {
                        frappe.msgprint(__('No item allocations found for distributor {0}. Please allocate items first.', [values.distributor]));
                        return;
                    }

                    let price_list_row = (tender.tender_price_list || [])
                        .find(row => row.distributor === values.distributor);

                    frm.set_value("sales_type", "Sales");
                    frm.set_value("order_type", tender.category === "Private Tender" ? "Private Tenders Order" : "UPA Tender Order");
                    frm.set_value("requested_to", "ONCO");
                    frm.set_value("implemented_by", "Onco");
                    frm.set_value("customer_type", "Distributor");
                    frm.set_value("delivery_date", values.delivery_date);

                    dialog.hide();

                    frappe.call({
                        method: "frappe.client.get",
                        args: {
                            doctype: "Customer",
                            name: values.distributor
                        },
                        callback(r) {
                            let customer = r.message;
                            if (!customer) return;

                            let customer_group = customer.customer_group || "";
                            let customer_tax_id = customer.tax_id || "";

                            if (!customer_group) {
                                frappe.msgprint(__('Customer group not found for distributor {0}.', [values.distributor]));
                                return;
                            }

                            frappe.call({
                                method: "frappe.client.get_value",
                                args: {
                                    doctype: "Customer Group",
                                    fieldname: "parent_customer_group",
                                    filters: { name: customer_group }
                                },
                                callback(pr) {
                                    let customer_main_group = pr.message ? pr.message.parent_customer_group : "";

                                    frm.set_value("customer_main_group", customer_main_group);
                                    frm.set_value("customer_group", customer_group);
                                    frm.set_value("tax_id", customer_tax_id);
                                    frm.set_value("customer", values.distributor);
                                    frm.set_value("price_list", price_list_row ? price_list_row.price_list : "");

                                    frm.clear_table("customer_po_items");
                                    allocations.forEach(a => {
                                        let row = frm.add_child("customer_po_items");
                                        row.item = a.item;
                                        row.item_name = a.item_name;
                                        row.quantity = a.supply_qty;
                                        row.price = 0;
                                        row.amount = 0;
                                        row.ordered_qty = 0;
                                    });
                                    frm.refresh_field("customer_po_items");
                                    frm.dirty();
                                    frappe.show_alert({ message: __("Customer Purchase Order populated from tender"), indicator: "green" });
                                }
                            });
                        }
                    });
                }
            });
            dialog.show();
        }
    });
}

// ========== Create Sales Order ==========

function show_create_sales_order_button(frm) {
    if (
        frm.doc.docstatus === 1 &&
        frm.doc.implemented_by === "Onco" &&
        has_remaining_qty(frm)
    ) {
        frm.add_custom_button("Create Sales Order", () => {
            open_sales_order_dialog(frm);
        });
    }
}

function has_remaining_qty(frm) {
    return (frm.doc.customer_po_items || []).some(
        row => flt(row.ordered_qty) < flt(row.quantity)
    );
}

function open_sales_order_dialog(frm) {
    const items = frm.doc.customer_po_items
        .filter(row => flt(row.ordered_qty) < flt(row.quantity))
        .map(row => ({
            item_code: row.item,
            item_name: row.item_name || "",
            max_qty: flt(row.quantity) - flt(row.ordered_qty),
            qty: 0
        }));

    const dialog = new frappe.ui.Dialog({
        title: "Create Sales Order",
        size: "large",
        fields: [
            {
                fieldtype: "Table",
                fieldname: "items",
                label: "Items",
                cannot_add_rows: true,
                data: items,
                fields: [
                    {
                        fieldtype: "Data",
                        fieldname: "item_code",
                        label: "Item Code",
                        read_only: 1,
                        in_list_view: 1
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "item_name",
                        label: "Item Name",
                        read_only: 1,
                        in_list_view: 1
                    },
                    {
                        fieldtype: "Float",
                        fieldname: "max_qty",
                        label: "Remaining Qty",
                        read_only: 1,
                        in_list_view: 1
                    },
                    {
                        fieldtype: "Float",
                        fieldname: "qty",
                        label: "Sales Qty",
                        in_list_view: 1
                    }
                ]
            }
        ],
        primary_action_label: "Create Sales Order",
        primary_action(values) {
            create_sales_order(frm, values.items, dialog);
        }
    });
    dialog.show();
}

function create_sales_order(frm, items, dialog) {
    const valid_items = items.filter(d => flt(d.qty) > 0);
    if (!valid_items.length) {
        frappe.msgprint("Please enter at least one valid quantity.");
        return;
    }

    frappe.call({
        method: "onco.onco.doctype.customer_purchase_order.customer_purchase_order.create_sales_order",
        args: {
            cpo_name: frm.doc.name,
            items_data: valid_items
        },
        callback(r) {
            if (r.message) {
                dialog.hide();
                frappe.msgprint(__("Sales Order created: {0}", [r.message]));
                frm.reload_doc();
            }
        }
    });
}
