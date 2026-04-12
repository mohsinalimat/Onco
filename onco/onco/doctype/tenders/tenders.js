// Copyright (c) 2026, ds and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tenders", {
	refresh(frm) {
		// Add custom buttons
		if (frm.doc.docstatus === 1) {
			// Workflow transition buttons for Awarded Tenders
			if (frm.doc.tender_type === "Awarded Tenders") {
				if (!frm.doc.workflow_status || frm.doc.workflow_status === "Awarded") {
					frm.add_custom_button(__('Mark as Submission'), function () {
						mark_as_submission(frm);
					}, __('Workflow'));
				}
				
				if (frm.doc.workflow_status === "Submission") {
					frm.add_custom_button(__('Create Accepted Tender'), function () {
						create_accepted_tender(frm);
					}, __('Workflow'));
				}
			}
			
			if (frm.doc.tender_price_deviation && frm.doc.tender_price_deviation.length > 0) {
				frm.add_custom_button(__('Approve All Price Deviations'), function () {
					approve_all_deviations(frm);
				}, __('Actions'));
			}

			// Button to update status from sales invoices
			frm.add_custom_button(__('Update Status from Invoices'), function () {
				update_status_from_invoices(frm);
			}, __('Actions'));

			// Button to approve rule changes (Role restriction removed for testing)
			frm.add_custom_button(__('Approve Rule Change'), function () {
				approve_rule_change(frm);
			}, __('Approvals'));
		}

		// Add Upload Data button for FMD
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
	},

	tender_type(frm) {
		// Reset rules if switching to market data tenders
		if (frm.doc.tender_type === "Tenders for market data") {
			frm.set_value("apply_extended_time", 0);
			frm.set_value("apply_extra_quantities", 0);
		}
		toggle_item_tables(frm);
		set_naming_series_options(frm);
	},

	category(frm) {
		set_naming_series_options(frm);
	},

	supplying_by(frm) {
		toggle_offer_sections(frm);
		
		// Auto-populate Oncopharm when "By Oncopharm" selected
		if (frm.doc.supplying_by === "Oncopharm" || frm.doc.supplying_by === "Oncopharm & Distributor") {
			let has_oncopharm = false;
			(frm.doc.tender_supplier || []).forEach(row => {
				if (row.supplying_by === "By Oncopharm") {
					has_oncopharm = true;
				}
			});
			
			if (!has_oncopharm) {
				// Search for Oncopharm customer
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Customer',
						filters: {
							'customer_name': ['like', '%ONCOPHARM%']
						},
						fields: ['name'],
						limit: 1
					},
					callback: function(r) {
						if (r.message && r.message.length > 0) {
							let row = frm.add_child("tender_supplier");
							row.supplying_by = "By Oncopharm";
							row.supplier = r.message[0].name;
							frm.refresh_field("tender_supplier");
						} else {
							// Just add the row without supplier if not found
							let row = frm.add_child("tender_supplier");
							row.supplying_by = "By Oncopharm";
							frm.refresh_field("tender_supplier");
						}
					}
				});
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

function toggle_item_tables(frm) {
	// Show/hide item tables based on tender type
	let show_items_fmd = frm.doc.tender_type === "Tenders for market data";
	let show_item_tender = ["Awarded Tenders", "Tender Submission", "Accepted Tenders"].includes(frm.doc.tender_type);
	let show_tender_supplier = ["Tender Submission", "Accepted Tenders"].includes(frm.doc.tender_type) || (frm.doc.tender_type === "Awarded Tenders" && frm.doc.supplying_by && frm.doc.supplying_by !== "Oncopharm");

	frm.set_df_property("items_fmd", "hidden", !show_items_fmd);
	frm.set_df_property("item_tender", "hidden", !show_item_tender);
	frm.set_df_property("tender_supplier", "hidden", !show_tender_supplier);

	frm.refresh_field("items_fmd");
	frm.refresh_field("item_tender");
	frm.refresh_field("tender_supplier");
}

function toggle_offer_sections(frm) {
	const supplying_by = frm.doc.supplying_by;
	const is_onco = supplying_by === "Oncopharm" || supplying_by === "Oncopharm & Distributor";
	const is_distributor = supplying_by === "Distributor" || supplying_by === "Oncopharm & Distributor";

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
	const is_accepted = frm.doc.is_accepted_tender;

	if (type === "Tenders for market data") {
		options = ["TNDR-FMD-.YYYY.-.####"];
	} else if (type === "Awarded Tenders") {
		if (is_accepted) {
			// Accepted tender naming
			if (category === "UPA Tender") options = ["TNDR-ACP-UPA-.YYYY.-.{tender_number}."];
			else if (category === "Private Tender") options = ["TNDR-ACP-PRV-.YYYY.-.{tender_number}."];
		} else {
			// Awarded tender naming
			if (category === "UPA Tender") options = ["TNDR-AWR-UPA-.YYYY.-.{tender_number}."];
			else if (category === "Private Tender") options = ["TNDR-AWR-PRV-.YYYY.-.{tender_number}."];
		}
	}

	if (options.length > 0) {
		frm.set_df_property("naming_series", "options", options);
		if (!options.includes(frm.doc.naming_series)) {
			frm.set_value("naming_series", options[0]);
		}
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
		__("Mark this Awarded Tender as Submission? This will allow adding supplier offers."),
		function () {
			frappe.call({
				method: 'frappe.client.set_value',
				args: {
					doctype: 'Tenders',
					name: frm.doc.name,
					fieldname: 'workflow_status',
					value: 'Submission'
				},
				callback: function () {
					frappe.show_alert({ message: __("Tender marked as Submission"), indicator: "green" });
					frm.reload_doc();
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
