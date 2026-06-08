frappe.ui.form.on("Customer Purchase Order", {
    refresh(frm) {
        set_customer_main_group_query(frm);
        apply_price_list_filter(frm);
        show_create_sales_order_button(frm);
    },

    onload(frm) {
        set_customer_main_group_query(frm);
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
