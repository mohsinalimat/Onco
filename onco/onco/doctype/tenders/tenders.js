// Copyright (c) 2026, ds and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tenders", {
	refresh(frm) {
		// Control Tender Type options:
		// Only allow creating physical new documents for the two starting points.
		if (frm.is_new()) {
			frm.set_df_property('tender_type', 'options', [
				"Tenders for market data",
				"Awarded Tenders"
			].join('\n'));
			frm.set_df_property('tender_type', 'read_only', 0);
		} else {
			frm.set_df_property('tender_type', 'options', [
				"Tenders for market data",
				"Awarded Tenders",
				"Tender Submission",
				"Accepted Tenders"
			].join('\n'));
			frm.set_df_property('tender_type', 'read_only', 1);
		}

		// Add custom buttons based on tender_type
		if (frm.doc.docstatus === 1) {

			// === AWARDED TENDERS ===
			// Only show Mark as Submission when it hasn't been submitted yet
			if (frm.doc.tender_type === "Awarded Tenders") {
				if (!frm.doc.workflow_status || frm.doc.workflow_status === "Awarded") {
					frm.add_custom_button(__('Mark as Submission'), function () {
						mark_as_submission(frm);
					}, __('Workflow'));
				}
			}

			// === TENDER SUBMISSION ===
			// Show Create Accepted Tender button
			if (frm.doc.tender_type === "Tender Submission") {
				if (!frm.doc.workflow_status || frm.doc.workflow_status !== "Accepted") {
					frm.add_custom_button(__('Create Accepted Tender'), function () {
						create_accepted_tender(frm);
					}, __('Workflow'));
				}

				// Offers can be entered at submission stage
				frm.add_custom_button(__('Add Price Offer'), function () {
					open_add_price_offer_dialog(frm);
				}, __('Offers'));

				frm.add_custom_button(__('Add Technical Offer'), function () {
					open_add_technical_offer_dialog(frm);
				}, __('Offers'));
			}

			// === ACCEPTED TENDERS ===
			// Show actions specific to accepted tenders
			if (frm.doc.tender_type === "Accepted Tenders") {
				// Create Sales Order from accepted tender
				frm.add_custom_button(__('Create Sales Order'), function () {
					create_sales_order_from_tender(frm);
				}, __('Actions'));

				// Update fulfillment status from Sales Orders
				frm.add_custom_button(__('Update Status from Sales Orders'), function () {
					update_status_from_orders(frm);
				}, __('Actions'));

				// Approve price deviations if any
				if (frm.doc.tender_price_deviation && frm.doc.tender_price_deviation.length > 0) {
					frm.add_custom_button(__('Approve All Price Deviations'), function () {
						approve_all_deviations(frm);
					}, __('Actions'));
				}

				// Allow inserting Technical/Price offers onto submitted Accepted Tenders
				frm.add_custom_button(__('Add Price Offer'), function () {
					open_add_price_offer_dialog(frm);
				}, __('Offers'));

				frm.add_custom_button(__('Add Technical Offer'), function () {
					open_add_technical_offer_dialog(frm);
				}, __('Offers'));

				// Extension amendment button — visible when rules are configured but not yet applied
				if ((frm.doc.apply_extra_quantities || frm.doc.apply_extended_time) && !frm.doc.applying_rules) {
					frm.add_custom_button(__('Amend Item Extensions'), function () {
						open_item_extension_dialog(frm);
					}, __('Actions'));
				}
			}

			// === SHARED ACTIONS (Awarded + Submission) ===
			if (["Awarded Tenders", "Tender Submission"].includes(frm.doc.tender_type)) {
				if (frm.doc.tender_price_deviation && frm.doc.tender_price_deviation.length > 0) {
					frm.add_custom_button(__('Approve All Price Deviations'), function () {
						approve_all_deviations(frm);
					}, __('Actions'));
				}

				frm.add_custom_button(__('Approve Rule Change'), function () {
					approve_rule_change(frm);
				}, __('Approvals'));
			}
		}

		// Add Upload Data button for FMD (draft only)
		if (frm.doc.tender_type === "Tenders for market data" && !frm.doc.__islocal && frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Upload FMD Data'), function () {
				upload_fmd_data(frm);
			});
		}

		// Set conditional field visibility
		toggle_tender_rules_fields(frm);
		toggle_item_tables(frm);
		toggle_offer_sections(frm);
		set_naming_series_options(frm);

		// Display deviation summary if deviations exist
		if (frm.doc.tender_price_deviation && frm.doc.tender_price_deviation.length > 0) {
			show_deviation_summary(frm);
		}

		// Display fulfillment status
		if (frm.doc.tender_status && frm.doc.tender_status.length > 0) {
			show_fulfillment_status(frm);
		}

		// Add filter for Tender Supplier
		frm.set_query("supplier", "tender_supplier", function () {
			return {
				filters: {
					"customer_group": "Pharmaceuticals Local Distributors Companies"
				}
			};
		});

		// Add filter for Tender Customer Name - should be from Tender Customers group
		frm.set_query("hospitalagent_name", function () {
			return {
				filters: {
					"customer_group": ["in", ["Tender Customers", "Hospitals", "Government Entities"]]
				}
			};
		});

		// Filter price lists in tender_price_list
		frm.set_query("price_list", "tender_price_list", function (doc, cdt, cdn) {
			return {
				filters: {
					"custom_price_list_type": "Tender Price List ",
					"buying": 1,
					"enabled": 1
				}
			};
		});

		// Filter price lists in price_list_for_tender
		frm.set_query("price_list", "tender_price_list", function (doc, cdt, cdn) {
			return {
				filters: {
					"custom_price_list_type": "Tender Price List ",
					"buying": 1,
					"enabled": 1
				}
			};
		});

		// Add filter for distributor in price_list_for_tender - should be from Pharmaceuticals Local Distributors Companies
		frm.set_query("distributor", "tender_price_list", function () {
			return {
				filters: {
					"customer_group": "Pharmaceuticals Local Distributors Companies"
				}
			};
		});

		// Add filters for Price Offers items (filtered by item group)
		frm.set_query("item", "onco_price_offer", function (doc, cdt, cdn) {
			let row = locals[cdt][cdn];
			if (row.item_group) {
				return { filters: { "item_group": row.item_group } };
			}
		});
		frm.set_query("item", "distributors_price_offer", function (doc, cdt, cdn) {
			let row = locals[cdt][cdn];
			if (row.item_group) {
				return { filters: { "item_group": row.item_group } };
			}
		});

		// Add filters for Distributors in the Distributor Offers tables
		let get_valid_distributors = function () {
			let valid_distributors = (frm.doc.tender_supplier || [])
				.map(row => row.supplier)
				.filter(sup => sup);
			if (valid_distributors.length > 0) {
				return { filters: [['name', 'in', valid_distributors]] };
			}
			return { filters: { "customer_group": "Pharmaceuticals Local Distributors Companies" } };
		};

		frm.set_query("distributor", "distributors_price_offer", get_valid_distributors);
		frm.set_query("distributor", "distributors_technical_offer", get_valid_distributors);
	},

	before_load(frm) {
		// Ensure naming series is set correctly on form load
		set_naming_series_options(frm);
	},

	tender_type(frm) {
		// Reset rules if switching to market data tenders
		if (frm.doc.tender_type === "Tenders for market data") {
			frm.set_value("apply_extended_time", 0);
			frm.set_value("apply_extra_quantities", 0);
		}
		toggle_item_tables(frm);
		toggle_offer_sections(frm);
		set_naming_series_options(frm);
	},

	category(frm) {
		set_naming_series_options(frm);
	},

	supplying_by(frm) {
		toggle_offer_sections(frm);

		// Auto-populate Oncopharm in tender supplier table
		if (frm.doc.supplying_by && frm.doc.supplying_by.includes("Oncopharm")) {
			let exists = (frm.doc.tender_supplier || []).some(row => row.supplying_by === "By Oncopharm Only");
			if (!exists) {
				let row = frm.add_child("tender_supplier");
				row.supplying_by = "By Oncopharm Only";
				// Supplier name will be filled by the user or can default to Oncopharm if exists
				frm.refresh_field("tender_supplier");
			}

			// Auto-populate onco_price_offer from item_tender
			if (frm.doc.item_tender && frm.doc.item_tender.length > 0) {
				frm.doc.item_tender.forEach(item => {
					let offer_exists = (frm.doc.onco_price_offer || []).some(offer => offer.item === item.item_code);
					if (!offer_exists) {
						let new_offer = frm.add_child("onco_price_offer");
						new_offer.item = item.item_code;
						new_offer.item_group = item.item_group;
						new_offer.quantity = item.tender_qty;
						new_offer.start_date = item.tender_start_date;
						new_offer.end_date = item.tender_end_date;
					}
				});
				frm.refresh_field("onco_price_offer");
			}
		}
	},

	number_of_distributors(frm) {
		if (frm.doc.number_of_distributors > 0) {
			let existing_rows = (frm.doc.tender_supplier || []).filter(row => row.supplying_by === "By Distributor Only").length;
			let rows_to_add = frm.doc.number_of_distributors - existing_rows;

			if (rows_to_add > 0) {
				for (let i = 0; i < rows_to_add; i++) {
					let row = frm.add_child("tender_supplier");
					row.supplying_by = "By Distributor Only";
				}
				frm.refresh_field("tender_supplier");
				frappe.msgprint(__(`Added ${rows_to_add} distributor placeholder(s) to Tender Supplier table. Please select their names.`));
			}
		}
	},

	apply_extra_quantities(frm) {
		toggle_tender_rules_fields(frm);
		frm.refresh_field("extra_quantities_column");
	},

	apply_extended_time(frm) {
		toggle_tender_rules_fields(frm);
		frm.refresh_field("extended_time_column");
	},

	// applying_rules is the master switch that triggers per-item extension
	// Because the parent doc may be submitted (docstatus=1), we cannot do a normal save.
	// We instead call a whitelisted server method that writes the child rows directly.
	applying_rules(frm) {
		if (!frm.doc.applying_rules) {
			// User unchecked — nothing to do, server will skip logic on next save
			return;
		}

		let has_qty_rule = frm.doc.apply_extra_quantities && frm.doc.extra_qty_type && frm.doc.extra_qty_value;
		let has_time_rule = frm.doc.apply_extended_time && frm.doc.extended_start_date && frm.doc.extended_end_date;

		if (!has_qty_rule && !has_time_rule) {
			frappe.msgprint(__("Please configure the extension rules (quantity type/value or extended dates) before activating."));
			frm.set_value("applying_rules", 0);
			return;
		}

		if (!frm.doc.item_tender || frm.doc.item_tender.length === 0) {
			frappe.msgprint(__("No items found in the tender to configure extensions for."));
			frm.set_value("applying_rules", 0);
			return;
		}

		open_item_extension_dialog(frm);
	},

	extra_qty_type(frm) {
		if (frm.doc.apply_extra_quantities && frm.doc.extra_qty_type) {
			if (frm.doc.extra_qty_type === "Percent") {
				frm.set_df_property("extra_qty_value", "label", "Extra Quantity Percent (%)");
			} else if (frm.doc.extra_qty_type === "Quantity") {
				frm.set_df_property("extra_qty_value", "label", "Extra Quantity Value");
			}
		}
	},

	tender_status_onchange(frm) {
		// Auto-calculate remaining quantity and fulfillment percent
		frm.doc.tender_status.forEach(row => {
			if (row.tender_quantity && row.supplied_quantity !== undefined) {
				row.remaining_quantity = row.tender_quantity - row.supplied_quantity;
				row.fulfillment_percent = (row.supplied_quantity / row.tender_quantity) * 100;
			}
		});
		frm.refresh_field("tender_status");
	}
});

// Real-time tender status population from item_tender
frappe.ui.form.on("Tender Supplier", {
	allocate_items(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let distributor_name = row.supplying_by === 'By Oncopharm Only' ? 'Oncopharm' : row.supplier;

		if (!distributor_name) {
			frappe.msgprint(__('Please select a Distributor first.'));
			return;
		}
		if (!frm.doc.item_tender || frm.doc.item_tender.length === 0) {
			frappe.msgprint(__('Please add items to the Tender first.'));
			return;
		}

		let mock_row = Object.assign({}, row);
		mock_row.supplier = distributor_name;
		open_supplier_allocation_dialog(frm, mock_row);
	},

	supplier(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// When a distributor is selected, copy items to the distributors price offer table for them
		if (row.supplying_by === "By Distributor Only" && row.supplier && frm.doc.item_tender && frm.doc.item_tender.length > 0) {
			frm.doc.item_tender.forEach(item => {
				// check if offer already exists for this distributor AND this item
				let offer_exists = (frm.doc.distributors_price_offer || []).some(
					offer => offer.item === item.item_code && offer.distributor === row.supplier
				);
				if (!offer_exists) {
					let new_offer = frm.add_child("distributors_price_offer");
					new_offer.distributor = row.supplier;
					new_offer.item = item.item_code;
					new_offer.item_group = item.item_group;
					new_offer.quantity = item.tender_qty;
					new_offer.start_date = item.tender_start_date;
					new_offer.end_date = item.tender_end_date;
				}
			});
			frm.refresh_field("distributors_price_offer");
			frappe.show_alert({ message: __(`Auto-populated price offer lines for ${row.supplier}`), indicator: 'green' });
		}
	}
});

frappe.ui.form.on("Item Tender", {
	item_tender_add(frm, cdt, cdn) {
		populate_tender_status_realtime(frm);
	},

	item_tender_remove(frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		// Remove corresponding tender_status row
		if (child.item_code) {
			let status_rows = frm.doc.tender_status || [];
			for (let i = status_rows.length - 1; i >= 0; i--) {
				if (status_rows[i].item_name === child.item_code) {
					frm.get_field("tender_status").grid.grid_rows[i].remove();
					break;
				}
			}
		}
		frm.refresh_field("tender_status");
	},

	item_code(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			if (!row.tender_start_date && frm.doc.tender_start_date) {
				frappe.model.set_value(cdt, cdn, "tender_start_date", frm.doc.tender_start_date);
			}
			if (!row.tender_end_date && frm.doc.tender_end_date) {
				frappe.model.set_value(cdt, cdn, "tender_end_date", frm.doc.tender_end_date);
			}
		}
		populate_tender_status_realtime(frm);
	},

	tender_qty(frm, cdt, cdn) {
		populate_tender_status_realtime(frm);
	}
});

frappe.ui.form.on('Distributors Price Offer', {
	item: function(frm, cdt, cdn) {
		archive_previous_offers(frm, locals[cdt][cdn]);
	},
	distributor: function(frm, cdt, cdn) {
		archive_previous_offers(frm, locals[cdt][cdn]);
	}
});

function archive_previous_offers(frm, new_row) {
	if (!new_row.item || !new_row.distributor) return;
	
	let changed = false;
	(frm.doc.distributors_price_offer || []).forEach(r => {
		if (r.name !== new_row.name && r.item === new_row.item && r.distributor === new_row.distributor && r.status !== 'Archived') {
			frappe.model.set_value(r.doctype, r.name, 'status', 'Archived');
			changed = true;
		}
	});
}

function populate_tender_status_realtime(frm) {
	if (!frm.doc.item_tender || frm.doc.item_tender.length === 0) {
		return;
	}

	// Map existing status rows by item_name
	let existing_status = {};
	(frm.doc.tender_status || []).forEach(row => {
		if (row.item_name) {
			existing_status[row.item_name] = row;
		}
	});

	// Track items we've seen
	let seen_items = new Set();

	// Process each item_tender row
	frm.doc.item_tender.forEach(item_row => {
		if (!item_row.item_code || seen_items.has(item_row.item_code)) {
			return;
		}

		seen_items.add(item_row.item_code);

		let tender_qty = item_row.tender_qty || 0;

		if (existing_status[item_row.item_code]) {
			// Update existing row
			let status_row = existing_status[item_row.item_code];
			status_row.tender_quantity = tender_qty;
			status_row.remaining_quantity = tender_qty - (status_row.supplied_quantity || 0);
			status_row.fulfillment_percent = tender_qty > 0 ? ((status_row.supplied_quantity || 0) / tender_qty * 100) : 0;
		} else {
			// Create new row
			let new_row = frm.add_child("tender_status");
			new_row.item_name = item_row.item_code;
			new_row.tender_quantity = tender_qty;
			new_row.supplied_quantity = 0;
			new_row.remaining_quantity = tender_qty;
			new_row.fulfillment_percent = 0;
		}
	});

	frm.refresh_field("tender_status");
}

// Price List for Tender - filter by distributor and tender type
frappe.ui.form.on("Price List for Tender", {
	distributor(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// Clear price list when distributor changes
		frappe.model.set_value(cdt, cdn, "price_list", "");
	}
});

function toggle_item_tables(frm) {
	// Show/hide item tables based on tender type
	let show_items_fmd = frm.doc.tender_type === "Tenders for market data";
	let show_item_tender = ["Awarded Tenders", "Tender Submission", "Accepted Tenders"].includes(frm.doc.tender_type);
	let show_tender_supplier = ["Awarded Tenders", "Tender Submission", "Accepted Tenders"].includes(frm.doc.tender_type);

	frm.set_df_property("items_fmd", "hidden", !show_items_fmd);
	frm.set_df_property("item_tender", "hidden", !show_item_tender);
	frm.set_df_property("tender_supplier", "hidden", !show_tender_supplier);

	frm.refresh_field("items_fmd");
	frm.refresh_field("item_tender");
	frm.refresh_field("tender_supplier");
}

function toggle_offer_sections(frm) {
	const supplying_by = frm.doc.supplying_by;
	const is_onco = supplying_by === "By Oncopharm Only" || supplying_by === "By Oncopharm & Distributor";
	const is_distributor = supplying_by === "By Distributor Only" || supplying_by === "By Oncopharm & Distributor";

	frm.toggle_display("onco_offers_section", is_onco);
	frm.set_df_property("onco_price_offer", "hidden", !is_onco);
	frm.set_df_property("onco_technical_offer", "hidden", !is_onco);

	frm.toggle_display("distributors_offers_section", is_distributor);
	frm.set_df_property("distributors_price_offer", "hidden", !is_distributor);
	frm.set_df_property("distributors_technical_offer", "hidden", !is_distributor);
}

function set_naming_series_options(frm) {
	if (!frm.doc.tender_type) return;

	let options = [];
	const type = frm.doc.tender_type;
	const category = frm.doc.category;

	if (type === "Tenders for market data") {
		options = ["TNDR-FMD-.YYYY.-.####"];
	} else if (type === "Awarded Tenders") {
		if (category === "UPA Tender") options = ["TNDR-AWR-UPA-.YYYY.-.{tender_number}.-"];
		else if (category === "Private Tender") options = ["TNDR-AWR-PRV-.YYYY.-.{tender_number}.-"];
	} else if (type === "Tender Submission") {
		if (category === "UPA Tender") options = ["TNDR-SUB-UPA-.YYYY.-.{tender_number}.-"];
		else if (category === "Private Tender") options = ["TNDR-SUB-PRV-.YYYY.-.{tender_number}.-"];
	} else if (type === "Accepted Tenders") {
		if (category === "UPA Tender") options = ["TNDR-ACP-UPA-.YYYY.-.{tender_number}.-"];
		else if (category === "Private Tender") options = ["TNDR-ACP-PRV-.YYYY.-.{tender_number}.-"];
	}

	if (options.length > 0) {
		frm.set_df_property("naming_series", "options", options);
		if (!options.includes(frm.doc.naming_series)) {
			frm.set_value("naming_series", options[0]);
		}
	} else if (["Awarded Tenders", "Tender Submission", "Accepted Tenders"].includes(type) && !category) {
		// If type requires category but none selected, show message
		frappe.msgprint({
			title: __('Category Required'),
			indicator: 'orange',
			message: __('Please select a Category (UPA Tender or Private Tender) to set the correct naming series.')
		});
	}
}

function toggle_tender_rules_fields(frm) {
	// Let Frappe's native depends_on handle this. 
	// Double-toggling fields inside a column break via JS causes them to permanently disappear.
}

function open_item_extension_dialog(frm) {
	let items = frm.doc.item_tender || [];
	if (items.length === 0) {
		frappe.msgprint(__("No items found in the tender."));
		return;
	}

	let has_qty_rule = frm.doc.apply_extra_quantities && frm.doc.extra_qty_type && frm.doc.extra_qty_value;
	let has_time_rule = frm.doc.apply_extended_time && frm.doc.extended_start_date && frm.doc.extended_end_date;

	// Build description lines for context
	let desc_lines = [];
	if (has_qty_rule) {
		desc_lines.push(`Quantity extension: <b>${frm.doc.extra_qty_type === 'Percent' ? frm.doc.extra_qty_value + '%' : frm.doc.extra_qty_value + ' units'}</b> extra`);
	}
	if (has_time_rule) {
		desc_lines.push(`Time extension: <b>${frm.doc.extended_start_date}</b> &rarr; <b>${frm.doc.extended_end_date}</b>`);
	}

	// Build one row per item with qty and time checkboxes
	let dialog_fields = [
		{
			fieldtype: 'HTML',
			fieldname: 'description_html',
			options: `<div class="alert alert-info" style="margin-bottom:12px;">
				<b>Extension Rules Configured:</b><br>${desc_lines.join('<br>')}
				<br><small>Select which items to extend. Unchecked items keep their original quantities and dates.</small>
			</div>`
		}
	];

	items.forEach((item, idx) => {
		if (!item.item_code) return;
		dialog_fields.push({ fieldtype: 'Section Break', label: item.item_name || item.item_code });
		dialog_fields.push({
			fieldname: `ext_qty_${idx}`,
			fieldtype: 'Check',
			label: __('Extend Quantity?'),
			default: item.extend_qty || 0,
			hidden: has_qty_rule ? 0 : 1
		});
		dialog_fields.push({
			fieldname: `ext_time_${idx}`,
			fieldtype: 'Check',
			label: __('Extend Time?'),
			default: item.extend_time || 0,
			hidden: has_time_rule ? 0 : 1
		});
	});

	let dialog = new frappe.ui.Dialog({
		title: __('Select Items to Extend'),
		fields: dialog_fields,
		primary_action_label: __('Apply Extension Selections'),
		primary_action(values) {
			// Build list of {name, extend_qty, extend_time} for each item row
			let selections = [];
			items.forEach((item, idx) => {
				if (!item.item_code) return;
				selections.push({
					name: item.name,
					extend_qty: values[`ext_qty_${idx}`] ? 1 : 0,
					extend_time: values[`ext_time_${idx}`] ? 1 : 0
				});
			});

			frappe.call({
				method: 'onco.onco.doctype.tenders.tenders.save_item_extension_flags',
				args: {
					tender_name: frm.doc.name,
					selections: selections
				},
				freeze: true,
				freeze_message: __('Saving extension selections...'),
				callback: function(r) {
					if (!r.exc) {
						dialog.hide();
						frm.reload_doc();
						frappe.show_alert({
							message: __('Extension selections saved. Rules will apply on next validation.'),
							indicator: 'green'
						});
					}
				}
			});
		}
	});

	dialog.show();
}


function approve_all_deviations(frm) {

	frappe.confirm(
		__("Are you sure you want to approve all price deviations?"),
		function () {
			// Mark all deviations as approved
			frm.doc.tender_price_deviation.forEach(row => {
				row.deviation_status = "Approved";
			});
			frm.refresh_field("tender_price_deviation");
			frappe.call({
				method: 'frappe.client.set_value',
				args: {
					doctype: 'Tenders',
					name: frm.doc.name,
					fieldname: {
						tender_price_deviation: frm.doc.tender_price_deviation
					}
				},
				callback: function () {
					frappe.show_alert({
						message: __("All price deviations marked as Approved"),
						indicator: "green"
					});
					frm.refresh();
				}
			});
		}
	);
}

function open_add_price_offer_dialog(frm) {
	let supplying_by = frm.doc.supplying_by || "";
	let offer_for_options = [];
	if (supplying_by.includes("Oncopharm")) offer_for_options.push("Oncopharm");
	if (supplying_by.includes("Distributor")) offer_for_options.push("Distributor");

	if (offer_for_options.length === 0) {
		frappe.msgprint(__('Please set "Supplying By" first.'));
		return;
	}

	let valid_distributors = (frm.doc.tender_supplier || [])
		.map(row => row.supplier)
		.filter(sup => sup);

	let dialog_fields = [
		{
			fieldname: 'offer_for',
			fieldtype: 'Select',
			label: __('Offer For'),
			options: offer_for_options.join('\n'),
			reqd: 1,
			hidden: offer_for_options.length === 1 ? 1 : 0,
			default: offer_for_options[0]
		},
		{
			fieldname: 'distributor',
			fieldtype: 'Link',
			label: __('Distributor'),
			options: 'Customer',
			reqd: 1,
			depends_on: 'eval:doc.offer_for == "Distributor"',
			get_query: function () {
				if (valid_distributors.length > 0) {
					return { filters: [['name', 'in', valid_distributors]] };
				}
				return { filters: { "customer_group": "Pharmaceuticals Local Distributors Companies" } };
			}
		},
		{ fieldtype: 'Column Break' },
		{ fieldname: 'item_group', fieldtype: 'Link', label: __('Item Group'), options: 'Item Group', default: 'Finished Pharmaceutical Products Item', reqd: 1 },
		{
			fieldname: 'item', fieldtype: 'Link', label: __('Item Code'), options: 'Item', reqd: 1,
			get_query: function () {
				let ig = dialog.get_value('item_group');
				return ig ? { filters: { item_group: ig } } : {};
			}
		},
		{ fieldname: 'quantity', fieldtype: 'Float', label: __('Tender Quantity'), reqd: 1 },
		{ fieldname: 'price', fieldtype: 'Currency', label: __('Tender Price'), reqd: 1 },
		{ fieldname: 'amount', fieldtype: 'Currency', label: __('Amount'), read_only: 1 },
		{ fieldtype: 'Section Break' },
		{ fieldname: 'start_date', fieldtype: 'Date', label: __('Tender Start Date'), default: frm.doc.tender_start_date },
		{ fieldname: 'end_date', fieldtype: 'Date', label: __('Tender End Date'), default: frm.doc.tender_end_date },
		{ fieldtype: 'Column Break' },
		{ fieldname: 'discount_percent', fieldtype: 'Percent', label: __('Discount Percent'), depends_on: 'eval:doc.offer_for == "Distributor"' },
		{ fieldname: 'credit_limit', fieldtype: 'Currency', label: __('Credit Limit'), depends_on: 'eval:doc.offer_for == "Distributor"' },
		{ fieldname: 'attachment', fieldtype: 'Attach', label: __('Attachment') },
	];

	let dialog = new frappe.ui.Dialog({
		title: __('Add Price Offer'),
		fields: dialog_fields,
		primary_action_label: __('Add Price Offer'),
		primary_action(values) {
			values.amount = (values.quantity || 0) * (values.price || 0);

			if (values.offer_for === 'Oncopharm') {
				let row = frm.add_child('onco_price_offer');
				Object.assign(row, values);
			} else {
				(frm.doc.distributors_price_offer || []).forEach(r => {
					if (r.item === values.item && r.distributor === values.distributor && r.status !== 'Archived') {
						frappe.model.set_value(r.doctype, r.name, 'status', 'Archived');
					}
				});
				let row = frm.add_child('distributors_price_offer');
				Object.assign(row, values);
				row.status = 'Active';
			}
			frm.refresh_fields();
			dialog.hide();
			frm.save('Update');
			frappe.show_alert({ message: __('Price offer successfully submitted'), indicator: 'green' });
		}
	});

	// Auto-calculate amount
	dialog.fields_dict.quantity.df.onchange = () => {
		let q = dialog.get_value('quantity') || 0;
		let p = dialog.get_value('price') || 0;
		dialog.set_value('amount', q * p);
	};
	dialog.fields_dict.price.df.onchange = () => {
		let q = dialog.get_value('quantity') || 0;
		let p = dialog.get_value('price') || 0;
		dialog.set_value('amount', q * p);
	};

	dialog.show();
}

function open_add_technical_offer_dialog(frm) {
	let supplying_by = frm.doc.supplying_by || "";
	let offer_for_options = [];
	if (supplying_by.includes("Oncopharm")) offer_for_options.push("Oncopharm");
	if (supplying_by.includes("Distributor")) offer_for_options.push("Distributor");

	if (offer_for_options.length === 0) {
		frappe.msgprint(__('Please set "Supplying By" first.'));
		return;
	}

	let valid_distributors = (frm.doc.tender_supplier || [])
		.map(row => row.supplier)
		.filter(sup => sup);

	let dialog_fields = [
		{
			fieldname: 'offer_for',
			fieldtype: 'Select',
			label: __('Offer For'),
			options: offer_for_options.join('\n'),
			reqd: 1,
			hidden: offer_for_options.length === 1 ? 1 : 0,
			default: offer_for_options[0]
		},
		{
			fieldname: 'distributor',
			fieldtype: 'Link',
			label: __('Distributor'),
			options: 'Customer',
			reqd: 1,
			depends_on: 'eval:doc.offer_for == "Distributor"',
			get_query: function () {
				if (valid_distributors.length > 0) {
					return { filters: [['name', 'in', valid_distributors]] };
				}
				return { filters: { "customer_group": "Pharmaceuticals Local Distributors Companies" } };
			}
		},
		{ fieldtype: 'Column Break' },
		{ fieldname: 'date_of_submission', fieldtype: 'Date', label: __('Date of Submission'), default: frappe.datetime.nowdate(), reqd: 1 },
		{ fieldtype: 'Section Break' },
		{ fieldname: 'subject', fieldtype: 'Data', label: __('Subject'), reqd: 1 },
		{ fieldname: 'attachment', fieldtype: 'Attach', label: __('Attachment') }
	];

	let dialog = new frappe.ui.Dialog({
		title: __('Add Technical Offer'),
		fields: dialog_fields,
		primary_action_label: __('Add Technical Offer'),
		primary_action(values) {
			if (values.offer_for === 'Oncopharm') {
				let row = frm.add_child('onco_technical_offer');
				Object.assign(row, values);
			} else {
				let row = frm.add_child('distributors_technical_offer');
				Object.assign(row, values);
			}
			frm.refresh_fields();
			dialog.hide();
			frm.save('Update');
			frappe.show_alert({ message: __('Technical offer successfully submitted'), indicator: 'green' });
		}
	});

	dialog.show();
}

function update_status_from_orders(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Sales Order',
			filters: { 'custom_tender_ref': frm.doc.name, 'docstatus': 1 },
			fields: ['name']
		},
		callback: function (r) {
			if (r.message && r.message.length > 0) {
				// Reset all supplied quantities to 0 before recalculating
				frm.doc.tender_status.forEach(status_row => {
					status_row.supplied_quantity = 0;
					status_row.remaining_quantity = status_row.tender_quantity;
					status_row.fulfillment_percent = 0;
				});

				let processed = 0;
				let total = r.message.length;
				let updated = false;

				r.message.forEach(order => {
					// Get order items
					frappe.call({
						method: 'frappe.client.get',
						args: {
							doctype: 'Sales Order',
							name: order.name
						},
						callback: function (ord_response) {
							ord_response.message.items.forEach(item => {
								frm.doc.tender_status.forEach(status_row => {
									if (status_row.item_name === item.item_code) {
										status_row.supplied_quantity = (status_row.supplied_quantity || 0) + item.qty;
										status_row.remaining_quantity = status_row.tender_quantity - status_row.supplied_quantity;
										status_row.fulfillment_percent = (status_row.supplied_quantity / status_row.tender_quantity) * 100;
										updated = true;
									}
								});
							});

							processed++;
							if (processed === total && updated) {
								frm.refresh_field("tender_status");
								frm.dirty();
								frappe.show_alert({ message: __("Tender status updated from Sales Orders"), indicator: "green" });
							}
						}
					});
				});
			} else {
				frappe.msgprint(__("No submitted Sales Orders found for this tender"));
			}
		}
	});
}

function approve_rule_change(frm) {
	frappe.prompt({
		fieldtype: 'Data',
		fieldname: 'reason',
		label: 'Reason for approval',
		reqd: 1
	}, function (values) {
		frm.set_value({
			"custom_rule_change_approved": 1,
			"custom_rule_change_reason": values.reason
		});
		frappe.show_alert({ message: __("Rule change approved by Tender Manager"), indicator: "green" });
	});
}

function show_deviation_summary(frm) {
	let summary = {
		total_items: 0,
		total_deviation: 0,
		pending: 0,
		approved: 0
	};

	frm.doc.tender_price_deviation.forEach(row => {
		summary.total_items++;
		summary.total_deviation += row.deviation_amount || 0;
		if (row.deviation_status === "Pending Approval") {
			summary.pending++;
		} else if (row.deviation_status === "Approved") {
			summary.approved++;
		}
	});

	// Create summary HTML
	let summary_html = `
		<div class="alert alert-warning" style="margin-top: 10px;">
			<h5><b>Price Deviation Summary</b></h5>
			<p><b>Total Items with Deviation:</b> ${summary.total_items}</p>
			<p><b>Total Deviation Amount:</b> ${frappe.format(summary.total_deviation, { fieldtype: "Currency" })}</p>
			<p><b>Pending Approval:</b> ${summary.pending}</p>
			<p><b>Approved:</b> ${summary.approved}</p>
		</div>
	`;

	// Append to form
	if ($('.tender-deviation-summary').length === 0) {
		$(frm.form_layout.form_section[0]).after(summary_html).addClass('tender-deviation-summary');
	}
}

function show_fulfillment_status(frm) {
	let total_tender_qty = 0;
	let total_supplied_qty = 0;

	frm.doc.tender_status.forEach(row => {
		total_tender_qty += row.tender_quantity || 0;
		total_supplied_qty += row.supplied_quantity || 0;
	});

	let fulfillment_percent = total_tender_qty > 0 ? ((total_supplied_qty / total_tender_qty) * 100).toFixed(2) : 0;

	let status_html = `
		<div class="alert alert-info" style="margin-top: 10px;">
			<h5><b>Tender Fulfillment Status</b></h5>
			<p><b>Total Tender Quantity:</b> ${total_tender_qty}</p>
			<p><b>Total Supplied Quantity:</b> ${total_supplied_qty}</p>
			<p><b>Fulfillment Progress:</b> ${fulfillment_percent}%</p>
			<div class="progress" style="height: 25px; margin-top: 10px;">
				<div class="progress-bar ${fulfillment_percent >= 80 ? 'progress-bar-success' : (fulfillment_percent >= 50 ? 'progress-bar-warning' : 'progress-bar-danger')}" 
					role="progressbar" 
					style="width: ${Math.min(fulfillment_percent, 100)}%;">
					${fulfillment_percent}%
				</div>
			</div>
		</div>
	`;

	if ($('.tender-fulfillment-status').length === 0) {
		$(frm.form_layout.form_section[0]).after(status_html).addClass('tender-fulfillment-status');
	}
}


function create_sales_order_from_tender(frm) {
	frappe.prompt([
		{
			fieldtype: 'Link',
			fieldname: 'customer',
			label: 'Customer',
			options: 'Customer',
			reqd: 1,
			default: frm.doc.hospitalagent_name
		},
		{
			fieldtype: 'Date',
			fieldname: 'delivery_date',
			label: 'Delivery Date',
			reqd: 1,
			default: frm.doc.tender_end_date
		}
	], function (values) {
		if (!frm.doc.item_tender || frm.doc.item_tender.length === 0) {
			frappe.msgprint(__('No items found to create a Sales Order.'));
			return;
		}

		let items = frm.doc.item_tender.map(row => ({
			item_code: row.item_code,
			item_name: row.item_name,
			qty: row.tender_qty,
			delivery_date: values.delivery_date
		})).filter(i => i.item_code);

		frappe.call({
			method: 'frappe.client.insert',
			args: {
				doc: {
					doctype: 'Sales Order',
					customer: values.customer,
					delivery_date: values.delivery_date,
					custom_tender: frm.doc.name,
					items: items
				}
			},
			callback: function (r) {
				if (r.message) {
					frappe.set_route('Form', 'Sales Order', r.message.name);
					frappe.show_alert({ message: __('Sales Order created: ') + r.message.name, indicator: 'green' });
				}
			}
		});
	}, __('Create Sales Order'), __('Create'));
}


function upload_fmd_data(frm) {
	new frappe.ui.FileUploader({
		method: "onco.onco.doctype.tenders.tenders.upload_fmd_items",
		args: {
			parent: frm.doc.name
		},
		on_success: (file) => {
			frm.reload_doc();
			frappe.show_alert({ message: __("Items uploaded successfully"), indicator: "green" });
		}
	});
}

function mark_as_submission(frm) {
	frappe.confirm(
		__("Mark this Awarded Tender as Submission? This will create a new Submission tender with SUB series."),
		function () {
			frappe.call({
				method: 'onco.onco.doctype.tenders.tenders.create_submission_from_awarded',
				args: {
					source_name: frm.doc.name
				},
				callback: function (r) {
					if (r.message) {
						frappe.set_route('Form', 'Tenders', r.message);
						frappe.show_alert({ message: __("Submission Tender created"), indicator: "green" });
					}
				}
			});
		}
	);
}

function create_accepted_tender(frm) {
	frappe.confirm(
		__("Create Accepted Tender from this Submission?"),
		function () {
			frappe.call({
				method: 'onco.onco.doctype.tenders.tenders.create_accepted_from_submission',
				args: {
					source_name: frm.doc.name
				},
				callback: function (r) {
					if (r.message) {
						frappe.set_route('Form', 'Tenders', r.message);
						frappe.show_alert({ message: __("Accepted Tender created"), indicator: "green" });
					}
				}
			});
		}
	);
}

frappe.ui.form.on("Onco Price Offer", {
	item_group(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "item", "");
	},
	quantity(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "amount", (row.quantity || 0) * (row.price || 0));
	},
	price(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "amount", (row.quantity || 0) * (row.price || 0));
	}
});

frappe.ui.form.on("Distributors Price Offer", {
	item_group(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "item", "");
	},
	quantity(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "amount", (row.quantity || 0) * (row.price || 0));
	},
	price(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "amount", (row.quantity || 0) * (row.price || 0));
	}
});

function open_supplier_allocation_dialog(frm, supplier_row) {
	let allocations = frm.doc.tender_supplier_allocations || [];
	let distributor = supplier_row.supplier;

	let dialog_fields = [
		{
			fieldname: "allocations_info",
			fieldtype: "HTML",
			options: `<div><b>Allocating Items for Distributor:</b> ${distributor}</div>`
		},
		{
			fieldname: "items",
			fieldtype: "Table",
			label: "Items",
			fields: [
				{ fieldname: "item", fieldtype: "Data", label: "Item Code", in_list_view: 1, read_only: 1 },
				{ fieldname: "item_name", fieldtype: "Data", label: "Item Name", in_list_view: 1, read_only: 1 },
				{ fieldname: "tender_qty", fieldtype: "Float", label: "Tender Qty", in_list_view: 1, read_only: 1 },
				{ fieldname: "supply_qty", fieldtype: "Float", label: "Supply Qty", in_list_view: 1 },
				{ fieldname: "price", fieldtype: "Currency", label: "Price", in_list_view: 1 },
				{ fieldname: "amount", fieldtype: "Currency", label: "Amount", in_list_view: 1, read_only: 1 }
			],
			data: [],
			get_data: function() {
				return this.data;
			}
		}
	];

	let dialog = new frappe.ui.Dialog({
		title: __('Allocate Items'),
		fields: dialog_fields,
		size: 'large',
		primary_action_label: __('Save Allocations'),
		primary_action: function(values) {
			let grid_data = dialog.fields_dict.items.grid.get_data();

			// Validate quantities
			let item_totals = {};
			// Sum up existing allocations from OTHER distributors
			(frm.doc.tender_supplier_allocations || []).forEach(r => {
				if (r.distributor !== distributor) {
					item_totals[r.item] = (item_totals[r.item] || 0) + (r.supply_qty || 0);
				}
			});

			// Add the new allocations
			let has_error = false;
			grid_data.forEach(d => {
				if (d.supply_qty > 0) {
					let new_total = (item_totals[d.item] || 0) + d.supply_qty;
					if (new_total > d.tender_qty) {
						frappe.msgprint(__('Total supply quantity for {0} exceeds the Tender Quantity ({1}). You are trying to allocate a total of {2} across all distributors.', [d.item, d.tender_qty, new_total]));
						has_error = true;
					}
				}
			});

			if (has_error) return;

			// Clear old allocations for this distributor
			let new_allocs = (frm.doc.tender_supplier_allocations || []).filter(r => r.distributor !== distributor);
			frm.doc.tender_supplier_allocations = new_allocs;

			let summary_texts = [];
			
			// Save new allocations
			grid_data.forEach(d => {
				if (d.supply_qty > 0) {
					let row = frm.add_child('tender_supplier_allocations');
					row.distributor = distributor;
					row.item = d.item;
					row.item_name = d.item_name;
					row.supply_qty = d.supply_qty;
					row.price = d.price;
					row.amount = d.supply_qty * (d.price || 0);
					summary_texts.push(`${d.item}: ${d.supply_qty}`);
				}
			});

			frappe.model.set_value(supplier_row.doctype, supplier_row.name, 'allocations_summary', summary_texts.join(', '));

			frm.refresh_field("tender_supplier_allocations");
			dialog.hide();
			frappe.show_alert({ message: __('Allocations saved in draft. Click Save or Update when ready.'), indicator: 'green' });
			frm.dirty();
		}
	});

	// Populate data
	let existing_data = {};
	allocations.forEach(r => {
		if (r.distributor === distributor) {
			existing_data[r.item] = r;
		}
	});

	let items_data = [];
	frm.doc.item_tender.forEach(item_row => {
		let ex = existing_data[item_row.item_code] || {};
		items_data.push({
			item: item_row.item_code,
			item_name: item_row.item_name,
			tender_qty: item_row.tender_qty,
			supply_qty: ex.supply_qty || 0,
			price: ex.price || 0,
			amount: (ex.supply_qty || 0) * (ex.price || 0)
		});
	});

	dialog.fields_dict.items.df.data = items_data;
	dialog.fields_dict.items.grid.refresh();

	// Auto-calculate amount inside dialog
	dialog.fields_dict.items.grid.df.onchange = function(e) {
		let grid_data = dialog.fields_dict.items.grid.get_data();
		grid_data.forEach(d => {
			d.amount = (d.supply_qty || 0) * (d.price || 0);
		});
		dialog.fields_dict.items.grid.refresh();
	};

	dialog.show();
}
