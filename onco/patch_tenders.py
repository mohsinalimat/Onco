import sys

with open(r'f:\Workfiles\oncopharma project\Onco\onco\onco\doctype\tenders\tenders.js', 'r', encoding='utf-8') as f:
    content = f.read()

target1 = "{ fieldname: 'credit_limit', fieldtype: 'Currency', label: __('Credit Limit'), depends_on: 'eval:doc.offer_for == \"Distributor\"' },\n\t];"
repl1 = "{ fieldname: 'credit_limit', fieldtype: 'Currency', label: __('Credit Limit'), depends_on: 'eval:doc.offer_for == \"Distributor\"' },\n\t\t{ fieldname: 'attachment', fieldtype: 'Attach', label: __('Attachment') },\n\t];"
if target1 in content:
    content = content.replace(target1, repl1)
else:
    print("target1 not found")

target2 = "			} else {\n\t\t\t\tlet row = frm.add_child('distributors_price_offer');\n\t\t\t\tObject.assign(row, values);\n\t\t\t}"
repl2 = "			} else {\n\t\t\t\t(frm.doc.distributors_price_offer || []).forEach(r => {\n\t\t\t\t\tif (r.item === values.item && r.distributor === values.distributor && r.status !== 'Archived') {\n\t\t\t\t\t\tr.status = 'Archived';\n\t\t\t\t\t}\n\t\t\t\t});\n\t\t\t\tlet row = frm.add_child('distributors_price_offer');\n\t\t\t\tObject.assign(row, values);\n\t\t\t\trow.status = 'Active';\n\t\t\t}"
if target2 in content:
    content = content.replace(target2, repl2)
else:
    print("target2 not found")

target3 = "\ttender_qty(frm, cdt, cdn) {\n\t\tpopulate_tender_status_realtime(frm);\n\t}\n});"
repl3 = "\ttender_qty(frm, cdt, cdn) {\n\t\tpopulate_tender_status_realtime(frm);\n\t}\n});\n\nfrappe.ui.form.on('Distributors Price Offer', {\n\titem: function(frm, cdt, cdn) {\n\t\tarchive_previous_offers(frm, locals[cdt][cdn]);\n\t},\n\tdistributor: function(frm, cdt, cdn) {\n\t\tarchive_previous_offers(frm, locals[cdt][cdn]);\n\t}\n});\n\nfunction archive_previous_offers(frm, new_row) {\n\tif (!new_row.item || !new_row.distributor) return;\n\t\n\tlet changed = false;\n\t(frm.doc.distributors_price_offer || []).forEach(r => {\n\t\tif (r.name !== new_row.name && r.item === new_row.item && r.distributor === new_row.distributor && r.status !== 'Archived') {\n\t\t\tfrappe.model.set_value(r.doctype, r.name, 'status', 'Archived');\n\t\t\tchanged = true;\n\t\t}\n\t});\n}"
if target3 in content:
    content = content.replace(target3, repl3)
else:
    print("target3 not found")

with open(r'f:\Workfiles\oncopharma project\Onco\onco\onco\doctype\tenders\tenders.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")
