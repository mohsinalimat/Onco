/*******************************************************
 * Customer Purchase Order
 * Items Pricing + Totals Calculation (FIXED)
 *******************************************************/

frappe.ui.form.on("Customer Purchase Order", {
    price_list(frm) {
        if (frm.doc.docstatus !== 0) return;

        (frm.doc.customer_po_items || []).forEach(row => {
            fetch_item_price(frm, row);
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

/***********************
 * Helper Functions
 ***********************/

function fetch_item_price(frm, row) {
    if (!row.item || !frm.doc.price_list) return;

    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "Item Price",
            filters: {
                item_code: row.item,
                price_list: frm.doc.price_list
            },
            fieldname: ["price_list_rate"]
        },
        callback(r) {
            if (!r.message) return;

            const new_price = flt(r.message.price_list_rate || 0);

            // ✅ update only if changed
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
    const new_amount = flt(row.quantity) * flt(row.price);

    // ✅ update only if changed
    if (flt(row.amount) !== new_amount) {
        row.amount = new_amount;
    }
}

function calculate_totals(frm) {
    let total_qty = 0;
    let total_amount = 0;

    (frm.doc.customer_po_items || []).forEach(row => {
        total_qty += flt(row.quantity);
        total_amount += flt(row.amount);
    });

    // ✅ set only if value changed
    if (flt(frm.doc.total_qty) !== total_qty) {
        frm.set_value("total_qty", total_qty);
    }

    if (flt(frm.doc.total_amount) !== total_amount) {
        frm.set_value("total_amount", total_amount);
    }
}
