// Copyright (c) 2026, Onco and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Price Registration', {
	// When a new row is added
	before_items_add: function(frm, cdt, cdn) {
		// Archive all existing rows before adding a new one
		if (frm.doc.custom_price_registration) {
			frm.doc.custom_price_registration.forEach(function(row) {
				frappe.model.set_value(row.doctype, row.name, 'status', 'Archived');
			});
		}
	},
	
	// After a row is added, set it to Active
	items_add: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, 'status', 'Active');
		
		frappe.show_alert({
			message: __('New price registration added as Active. Previous registrations archived.'),
			indicator: 'green'
		}, 5);
	}
});
