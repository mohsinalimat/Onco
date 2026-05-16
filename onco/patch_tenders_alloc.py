import sys

with open(r'f:\Workfiles\oncopharma project\Onco\onco\onco\doctype\tenders\tenders.js', 'r', encoding='utf-8') as f:
    content = f.read()

target1 = "frappe.ui.form.on(\"Tender Supplier\", {\n\tsupplier(frm, cdt, cdn) {"
repl1 = """frappe.ui.form.on("Tender Supplier", {
	allocate_items(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!row.supplier) {
			frappe.msgprint(__('Please select a Distributor first.'));
			return;
		}
		if (!frm.doc.item_tender || frm.doc.item_tender.length === 0) {
			frappe.msgprint(__('Please add items to the Tender first.'));
			return;
		}
		open_supplier_allocation_dialog(frm, row);
	},

	supplier(frm, cdt, cdn) {"""

if target1 in content:
    content = content.replace(target1, repl1)
else:
    print("target1 not found")

new_func = """
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
				}
			});

			frm.refresh_field("tender_supplier_allocations");
			dialog.hide();
			frappe.show_alert({ message: __('Allocations saved'), indicator: 'green' });
			frm.save('Update');
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
"""

if "open_supplier_allocation_dialog" not in content:
    content = content + new_func

with open(r'f:\Workfiles\oncopharma project\Onco\onco\onco\doctype\tenders\tenders.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")
