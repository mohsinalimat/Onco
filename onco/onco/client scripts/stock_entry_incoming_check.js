// Add custom button to Stock Entry to create Incoming Check Report

frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        // Add button only if Stock Entry is submitted and purpose is Material Transfer
        if (frm.doc.docstatus === 1 && frm.doc.purpose === 'Material Transfer') {
            // Check if Incoming Check Report already exists
            frappe.db.get_value('Incoming Check Report', 
                {'stock_entry': frm.doc.name}, 
                'name',
                (r) => {
                    if (!r || !r.name) {
                        // No Incoming Check Report exists, show button
                        frm.add_custom_button(__('Create Incoming Check Report'), function() {
                            frappe.model.open_mapped_doc({
                                method: "onco.onco.doctype.incoming_check_report.incoming_check_report.make_incoming_check_report",
                                frm: frm
                            });
                        }, __('Create'));
                    } else {
                        // Incoming Check Report exists, show view button
                        frm.add_custom_button(__('View Incoming Check Report'), function() {
                            frappe.set_route('Form', 'Incoming Check Report', r.name);
                        }, __('View'));
                    }
                }
            );
        }
    }
});
