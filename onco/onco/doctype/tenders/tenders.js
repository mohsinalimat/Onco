// Copyright (c) 2026, ds and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tenders", {
	refresh(frm) {
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
			}

			// === ACCEPTED TENDERS ===
			// Show actions specific to accepted tenders
			if (frm.doc.tender_type === "Accepted Tenders") {
				// Create Sales Order from accepted tender
				frm.add_custom_button(__('Create Sales Order'), function () {
					create_sales_order_from_tender(frm);
				}, __('Actions'));

				// Update fulfillment status from invoices
				frm.add_custom_button(__('Update Status from Invoices'), function () {
					update_status_from_invoices(frm);
				}, __('Actions'));

				// Approve price deviations if any
				if (frm.doc.tender_price_deviation && frm.doc.tender_price_deviation.length > 0) {
					frm.add_custom_button(__('Approve All Price Deviations'), function () {
						approve_all_deviations(frm);
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

		// Filter price lists in tender_price_list by supplier
		frm.set_query("price_list", "tender_price_list", function (doc, cdt, cdn) {
			let row = locals[cdt][cdn];
			let filters = {
				"buying": 1,
				"enabled": 1
			};

			// Filter by supplier if selected
			if (row.distributor) {
				filters["applicable_for"] = row.distributor;
			}

			return {
				filters: filters
			};
		});

		// Add filter for distributor in tender_price_list - should be from Pharmaceuticals Local Distributors Companies
		frm.set_query("distributor", "tender_price_list", function () {
			return {
				filters: {
					"customer_group": "Pharmaceuticals Local Distributors Companies"
				}
			};
		});
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

	apply_extra_quantities(frm) {
		toggle_tender_rules_fields(frm);
		frm.refresh_field("extra_quantities_column");
	},

	apply_extended_time(frm) {
		toggle_tender_rules_fields(frm);
		frm.refresh_field("extended_time_column");
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
		populate_tender_status_realtime(frm);
	},

	tender_qty(frm, cdt, cdn) {
		populate_tender_status_realtime(frm);
	}
});

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
	let show_tender_supplier = ["Tender Submission", "Accepted Tenders"].includes(frm.doc.tender_type);

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
		if (category === "UPA Tender") options = ["TNDR-AWR-UPA-.YYYY.-.{tender_number}."];
		else if (category === "Private Tender") options = ["TNDR-AWR-PRV-.YYYY.-.{tender_number}."];
	} else if (type === "Tender Submission") {
		if (category === "UPA Tender") options = ["TNDR-SUB-UPA-.YYYY.-.{tender_number}."];
		else if (category === "Private Tender") options = ["TNDR-SUB-PRV-.YYYY.-.{tender_number}."];
	} else if (type === "Accepted Tenders") {
		if (category === "UPA Tender") options = ["TNDR-ACP-UPA-.YYYY.-.{tender_number}."];
		else if (category === "Private Tender") options = ["TNDR-ACP-PRV-.YYYY.-.{tender_number}."];
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
	// Toggle extra quantities fields
	frm.set_df_property("extra_quantities_column", "hidden", !frm.doc.apply_extra_quantities);
	frm.set_df_property("extra_qty_type", "hidden", !frm.doc.apply_extra_quantities);
	frm.set_df_property("extra_qty_value", "hidden", !frm.doc.apply_extra_quantities);

	// Toggle extended time fields
	frm.set_df_property("extended_time_column", "hidden", !frm.doc.apply_extended_time);
	frm.set_df_property("extended_start_date", "hidden", !frm.doc.apply_extended_time);
	frm.set_df_property("extended_end_date", "hidden", !frm.doc.apply_extended_time);

	frm.refresh_field("extra_quantities_column");
	frm.refresh_field("extended_time_column");
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

function update_status_from_invoices(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Sales Invoice',
			filters: { 'custom_tender_ref': frm.doc.name, 'docstatus': 1 },
			fields: ['name', 'posting_date', 'items']
		},
		callback: function (r) {
			if (r.message && r.message.length > 0) {
				// Update supplied quantities from invoices
				let updated = false;
				r.message.forEach(invoice => {
					// Get invoice items
					frappe.call({
						method: 'frappe.client.get',
						args: {
							doctype: 'Sales Invoice',
							name: invoice.name
						},
						callback: function (inv_response) {
							inv_response.message.items.forEach(item => {
								frm.doc.tender_status.forEach(status_row => {
									if (status_row.item_name === item.item_code) {
										status_row.supplied_quantity = (status_row.supplied_quantity || 0) + item.qty;
										status_row.remaining_quantity = status_row.tender_quantity - status_row.supplied_quantity;
										status_row.fulfillment_percent = (status_row.supplied_quantity / status_row.tender_quantity) * 100;
										updated = true;
									}
								});
							});
							if (updated) {
								frm.refresh_field("tender_status");
								frappe.show_alert({ message: __("Tender status updated"), indicator: "green" });
							}
						}
					});
				});
			} else {
				frappe.msgprint(__("No sales invoices found for this tender"));
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
			rate: row.tender_price,
			delivery_date: values.delivery_date
		})).filter(i => i.item_code);

		frappe.call({
			method: 'frappe.client.insert',
			args: {
				doc: {
					doctype: 'Sales Order',
					customer: values.customer,
					delivery_date: values.delivery_date,
					custom_tender_ref: frm.doc.name,
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
