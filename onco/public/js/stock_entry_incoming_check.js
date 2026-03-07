// Stock Entry - Incoming Check Report button REMOVED
// Incoming Check Report creation has been moved to Purchase Receipt
// This file is kept for backward compatibility but no longer adds the button

frappe.ui.form.on('Stock Entry', {
    custom_purchase_receipt: function (frm) {
        // When Purchase Receipt is set, auto-fetch Shipment reference
        if (frm.doc.custom_purchase_receipt && !frm.doc.custom_shipment_ref) {
            frappe.db.get_value('Purchase Receipt', frm.doc.custom_purchase_receipt, 'custom_shipment_ref', (r) => {
                if (r && r.custom_shipment_ref) {
                    frm.set_value('custom_shipment_ref', r.custom_shipment_ref);
                }
            });
        }
    }
});
