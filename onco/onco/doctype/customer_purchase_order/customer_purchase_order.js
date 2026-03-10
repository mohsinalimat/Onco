// Copyright (c) 2025, ds and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Purchase Order", {
	refresh(frm) {
		// Document uses custom autoname() method in Python
		// Naming is automatically generated based on order_type and date year
		// Format: CPO-{TYPE}-{YYYY}-{XXXXX}-{customer_purchase_order_number}
	},
	
	order_type(frm) {
		// Document uses custom autoname() method based on order_type and date
		// No need to manually set naming_series as it's handled by Python autoname()
	},
	
	onload(frm) {
		// Document uses custom autoname() method in Python
		// Naming is automatically generated on save
	}
});

// Override any Client Script that tries to set naming_series
// This prevents errors since naming_series field no longer exists
function set_naming_series(frm) {
	// Do nothing - naming is handled by Python autoname() method
	// This function exists only to prevent errors from Client Scripts
	return;
}
