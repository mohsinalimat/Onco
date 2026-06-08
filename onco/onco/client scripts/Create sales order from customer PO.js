/*******************************************************
 * Customer Purchase Order
 * Sales Order Creation (Fixed)
 *******************************************************/

frappe.ui.form.on("Customer Purchase Order", {
    refresh(frm) {
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
});

/***********************
 * Validation
 ***********************/

function has_remaining_qty(frm) {
    return (frm.doc.customer_po_items || []).some(
        row => flt(row.ordered_qty) < flt(row.quantity)
    );
}

/***********************
 * Dialog
 ***********************/

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

/***********************
 * Sales Order Creation
 ***********************/

function create_sales_order(frm, items, dialog) {
    const so_items = [];

    items.forEach(row => {
        if (flt(row.qty) > 0) {
            if (flt(row.qty) > flt(row.max_qty)) {
                frappe.throw(
                    __("Qty for item {0} exceeds remaining quantity", [row.item_code])
                );
            }

            so_items.push({
                item_code: row.item_code,
                qty: row.qty,
                delivery_date: frm.doc.delivery_date   // ✅ FIX
            });
        }
    });

    if (!so_items.length) {
        frappe.msgprint("Please enter at least one valid quantity.");
        return;
    }

    frappe.call({
        method: "frappe.client.insert",
        args: {
            doc: {
                doctype: "Sales Order",
                customer: frm.doc.customer,
                transaction_date: frm.doc.date,
                delivery_date: frm.doc.delivery_date, // ✅ FIX
                po_no: frm.doc.customer_purchase_order_number,
                items: so_items,
                implemented_by: frm.doc.implemented_by,
                customer_type: frm.doc.customer_type,
                custom_customer_po: frm.doc.name,
                po_date: frm.doc.date,
                order_type: frm.doc.sales_type,
                custom_order_type_1: frm.doc.order_type,
                requested_to_: frm.doc.requested_to,
                selling_price_list: frm.doc.price_list

            }
        },
        callback(r) {
            if (r.message) {
                update_ordered_qty(frm, items);
                dialog.hide();
                frappe.msgprint("Sales Order created successfully.");
            }
        }
    });
}

/***********************
 * Update Ordered Qty
 ***********************/

function update_ordered_qty(frm, items) {
    items.forEach(d => {
        if (!d.qty) return;

        const row = frm.doc.customer_po_items.find(
            r => r.item === d.item_code
        );

        if (row) {
            row.ordered_qty = flt(row.ordered_qty) + flt(d.qty);
        }
    });

    frm.save("Update");
}
