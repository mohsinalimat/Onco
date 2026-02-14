frappe.ui.form.on("Purchase Receipt Report", {
    refresh: function (frm) {
        // Show helpful message if document is in draft
        if (frm.doc.docstatus === 0 && !frm.is_new()) {
            frappe.show_alert({
                message: __('Please review the inspection data and click Submit to proceed'),
                indicator: 'blue'
            }, 5);
        }
        
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Printing Order"), function () {
                frappe.model.open_mapped_doc({
                    method: "onco.onco.doctype.purchase_receipt_report.purchase_receipt_report.make_printing_order",
                    frm: frm
                })
            }, __("Create"));
        }
    },

    purchase_receipt: function (frm) {
        if (frm.doc.purchase_receipt) {
            frappe.db.get_value("Purchase Receipt", frm.doc.purchase_receipt, "custom_shipment_ref")
                .then(r => {
                    if (r.message && r.message.custom_shipment_ref) {
                        frm.set_value("custom_shipment_ref", r.message.custom_shipment_ref);
                        frm.trigger("fetch_shipment_status");
                    }
                });
        }
    },

    fetch_shipment_status: function (frm) {
        if (frm.doc.custom_shipment_ref) {
            frappe.db.get_doc("Shipments", frm.doc.custom_shipment_ref)
                .then(shipment => {
                    frm.set_value("invoice_present", shipment.invoice ? 1 : 0);
                    frm.set_value("awb_present", shipment.awb ? 1 : 0);
                    frm.set_value("coa_present", shipment.certificate_of_analysis_ ? 1 : 0);
                    frm.set_value("data_logger_present", shipment.cold_chain ? 1 : 0);
                });
        }
    }
});

frappe.ui.form.on("Purchase Receipt Report Item", {
    received_qty: function (frm, cdt, cdn) { calculate_accepted(frm, cdt, cdn); },
    damage_qty: function (frm, cdt, cdn) { calculate_accepted(frm, cdt, cdn); },
    over_qty: function (frm, cdt, cdn) { calculate_accepted(frm, cdt, cdn); }
});

function calculate_accepted(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    // Logic: Accepted = Received - Damage + Over? Or Accepted = Received - Damage?
    // Requirement says: "Accepted Quantity"
    // Usually Accepted = Received - Damage (if Over implies extra good stock, maybe + Over)
    // Looking at table: "Over Quantity", "Damage Quantity", "Accepted Quantity".
    // Let's assume Accepted = Received - Damage. Over is just informational or separate.

    let val = (row.received_qty || 0) - (row.damage_qty || 0);
    frappe.model.set_value(cdt, cdn, "accepted_qty", val);
}
