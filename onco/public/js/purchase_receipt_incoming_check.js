// Add custom button to Purchase Receipt to create Incoming Check Report

frappe.ui.form.on('Purchase Receipt', {
    refresh: function (frm) {
        // Add button only if Purchase Receipt is submitted
        if (frm.doc.docstatus === 1) {
            // Check if Incoming Check Report already exists for this Purchase Receipt
            frappe.db.get_value('Incoming Check Report',
                { 'purchase_receipt': frm.doc.name, 'docstatus': ['!=', 2] },
                'name',
                (r) => {
                    if (!r || !r.name) {
                        // No Incoming Check Report exists, show button
                        frm.add_custom_button(__('Create Incoming Check Report'), function () {
                            frappe.model.open_mapped_doc({
                                method: "onco.onco.doctype.incoming_check_report.incoming_check_report.make_incoming_check_report_from_pr",
                                frm: frm
                            });
                        }, __('Create'));
                    } else {
                        // Incoming Check Report exists, show view button
                        frm.add_custom_button(__('View Incoming Check Report'), function () {
                            frappe.set_route('Form', 'Incoming Check Report', r.name);
                        }, __('View'));
                    }
                }
            );
        }
    }
});
