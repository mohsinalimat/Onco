// frappe.ui.form.on("Purchase Receipt", {
//   on_submit(frm) {

//     let purchase_invoice = frm.doc.items[0].purchase_invoice

//     frappe.msgprint("hello")
//     frappe.call({
//       method: "onco.onco.doctype.shipments.shipments.get_shipment",
//       args:{
//         purchase_invoice: purchase_invoice,
//         rec:frm.doc,
//       },
//       callback:function(res){
//         console.log("response",res.message)
//         frm.set_value("group_same_items",1)  
//       } 
      
//     })
// }
// });
  frappe.ui.form.on("Purchase Receipt", {
    before_save(frm) {
        if (frm.doc.items && frm.doc.items.length > 0) {
            let purchase_invoice = frm.doc.items[0].purchase_invoice;

            if (purchase_invoice) {
                frappe.msgprint("Fetching shipment details...");

                frappe.call({
                    method: "onco.onco.doctype.shipments.shipments.get_shipment",
                    args: {
                        purchase_invoice: purchase_invoice,
                        rec: frm.doc,
                    },
                    callback: function (res) {
                        if (res.message) {
                            console.log("response(get_shipment)", res.message);
                            doc_shipments = res.message;
                            // frm.set_value("group_same_items", 1);
                            frappe.call({
                              method: "onco.onco.doctype.shipments.shipments.set_shipment",
                              args: {
                                doc_shipments: doc_shipments,
                                  rec: frm.doc,
                              },
                              callback: function (res) {
                                  if (res.message) {
                                      console.log("response (set_shipment)", res.message);
                                      let receipt = res.message;
                                      setTimeout(
                                        function () {
                                      console.log(receipt)
                                      console.log("awb :",receipt.awb)
                                      frm.set_value("awb",receipt.awb);
                                      frm.set_value("invoice",receipt.invoice);
                                      frm.set_value("certificate_of_analysis_",receipt.certificate_of_analysis_);
                                      frm.set_value("certificate_of_origin",receipt.certificate_of_origin);
                                      frm.set_value("certificate_of_euro_1_",receipt.certificate_of_euro_1_);
                                      frm.set_value("certificate_of_insurance_",receipt.certificate_of_insurance_);
                                      frm.set_value("invoice_no",receipt.invoice_no);
                                      frm.set_value("invoice_date",receipt.invoice_date);                                
                                      frm.set_value("batch_no",receipt.batch_no);
                                      frm.set_value("expiry_date",receipt.expiry_date);
                                      frm.set_value("manufacturing_date_",receipt.manufacturing_date_);
                                      frm.set_value("awb_no",receipt.awb_no);
                                      frm.set_value("awb_date",receipt.awb_date);

                                      frm.set_value("arrived_",receipt.arrived);
                                      frm.set_value("arrivail_date",receipt.arrivail_date);
                                      frm.set_value("bank_authenticated_",receipt.bank_authenticated);
                                      frm.set_value("bank_authenticating_date",receipt.bank_authenticating_date);
                                      frm.set_value("restricted_release_status",receipt.restricted_release_status);
                                      frm.set_value("restricted_release_date",receipt.restricted_release_date);
                                      frm.set_value("customs_release_status",receipt.customs_release_status);
                                      frm.set_value("customs_release_no",receipt.customs_release_no);
                                      frm.set_value("customs_release_date",receipt.customs_release_date);

                                      frm.set_value("instructions",receipt.instructions);
                                      frm.set_value("remarks",receipt.remarks);
                                      frm.set_value("is_internal_supplier",receipt.is_internal_supplier);










                                  },1000)
                                      

                                  } else {
                                      frappe.msgprint("No shipment found.");
                                  }
                              }
                          });
                        } else {
                            frappe.throw("No shipment found.");
                        }
                    }
                });
            } else {
                frappe.msgprint("No Purchase Invoice linked to this receipt.");
            }
        } else {
            frappe.msgprint("No items found in Purchase Receipt.");
        }
    }
  });

frappe.ui.form.on('Purchase Invoice', {
    refresh: function(frm) {
        if (frm.is_new() && frm.doc.update_stock !== 1) {
            frm.set_value('update_stock', 1);
        }
        if (frm.doc.supplier && frm.fields_dict.items && frm.fields_dict.items.grid) {
            frm.fields_dict.items.grid.get_field('item_code').get_query = function () {
                return {
                    filters: [
                        ['Item', 'default_supplier', '=', frm.doc.supplier],
                        ['Item Supplier', 'supplier', '=', frm.doc.supplier]
                    ]
                };
            };
        }
    },

    supplier: function (frm) {
        if (frm.doc.supplier && frm.fields_dict.items && frm.fields_dict.items.grid) {
            frm.fields_dict.items.grid.get_field('item_code').get_query = function () {
                return {
                    filters: [
                        ['Item', 'default_supplier', '=', frm.doc.supplier],
                        ['Item Supplier', 'supplier', '=', frm.doc.supplier]
                    ]
                };
            };
        }
    },

    update_stock: function(frm) {
        if (frm.doc.items) {
            frm.doc.items.forEach(function(item) {
                if (frm.doc.update_stock === 1) {
                    frappe.model.set_value(item.doctype, item.name, 'use_serial_batch_fields', 1);
                }
            });
            frm.refresh_field('items');
        }
    }
});

frappe.ui.form.on('Purchase Invoice Item', {
    items_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (frm.doc.update_stock === 1) {
            frappe.model.set_value(cdt, cdn, 'use_serial_batch_fields', 1);
        }
    },

    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (frm.doc.update_stock === 1) {
            frappe.model.set_value(cdt, cdn, 'use_serial_batch_fields', 1);
        }
        if (row.item_code) {
            frappe.db.get_value('Item', row.item_code, 'has_batch_no', function(r) {
                if (r && r.has_batch_no) {
                    frappe.show_alert({
                        message: __('This item requires a batch number'),
                        indicator: 'blue'
                    }, 5);
                }
            });
        }
    }
});
