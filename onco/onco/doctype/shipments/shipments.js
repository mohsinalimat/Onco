
// Custom Logic for Shipments
frappe.ui.form.on("Shipments", {
  refresh: function (frm) {
    frm.trigger("render_dashboard");
    if (frm.doc.docstatus === 1 && frm.doc.status === "Completed") {
      frm.add_custom_button(__("Purchase Receipt"), function () {
        frappe.model.open_mapped_doc({
          method: "onco.onco.doctype.shipments.shipments.make_purchase_receipt",
          frm: frm
        })
      }, __("Create"));
    }
  },

  mode_of_shipping: function (frm) {
    frm.trigger("set_naming_series");
    frm.trigger("render_dashboard");
  },

  awb_no: function (frm) {
    frm.trigger("set_naming_series");
    frm.trigger("render_dashboard");
  },

  swb_no: function (frm) {
    frm.trigger("set_naming_series");
    frm.trigger("render_dashboard");
  },

  awb_date: function (frm) {
    frm.trigger("render_dashboard");
  },

  swb_date: function (frm) {
    frm.trigger("render_dashboard");
  },

  awb_attach: function (frm) {
    frm.trigger("render_dashboard");
  },

  swb_attach: function (frm) {
    frm.trigger("render_dashboard");
  },

  invoice: function (frm) {
    frm.trigger("render_dashboard");
  },

  packing_list: function (frm) {
    frm.trigger("render_dashboard");
  },

  certificate_of_analysis_: function (frm) {
    frm.trigger("render_dashboard");
  },

  certificate_of_origin: function (frm) {
    frm.trigger("render_dashboard");
  },

  set_naming_series: function (frm) {
    if (frm.doc.mode_of_shipping && (frm.doc.awb_no || frm.doc.swb_no)) {
      let suffix = frm.doc.mode_of_shipping === "Air freight" ? "AWB-" + (frm.doc.awb_no || "") : "SWB-" + (frm.doc.swb_no || "");
      // Note: In Frappe, we can't easily change the name if it's already saved, 
      // but we can set the naming series if we have multiple.
      // The requirement says "SHIP-IMP-AWB-00000000".
      // We will assume the user has a custom naming series or we use a field to display it.
      // For now, let's just make sure the fields are clear.
    }
  },

  // Commented out: Purchase Invoice doesn't have custom_importation_approval field
  // If you need to fetch importation approval, get it from the linked Purchase Order instead
  // purchase_invoice: function (frm) {
  //   if (frm.doc.purchase_invoice) {
  //     frappe.db.get_value("Purchase Invoice", frm.doc.purchase_invoice, "custom_importation_approval")
  //       .then(r => {
  //         if (r.message && r.message.custom_importation_approval) {
  //           frm.set_value("custom_importation_approval", r.message.custom_importation_approval);
  //         }
  //       });
  //   }
  // },

  validate: function (frm) {
    if (frm.doc.cold_chain && !frm.doc.cold_chain_equipment_ready) {
      frappe.throw(__("Cold Chain Equipment must be ready for Cold Chain shipments."));
    }
  },

  arrived: function (frm) { frm.trigger("render_dashboard"); },
  bank_authenticated: function (frm) {
    if (frm.doc.bank_authenticated && !frm.doc.date_of_submission_bank) {
      frm.set_value("date_of_submission_bank", frappe.datetime.get_today());
    }
    frm.trigger("render_dashboard");
  },
  restricted_release_status: function (frm) {
    if (frm.doc.restricted_release_status && !frm.doc.date_of_submission_restricted) {
      frm.set_value("date_of_submission_restricted", frappe.datetime.get_today());
    }
    frm.trigger("render_dashboard");
  },
  customs_release_status: function (frm) {
    if (frm.doc.customs_release_status && !frm.doc.date_of_submission_customs) {
      frm.set_value("date_of_submission_customs", frappe.datetime.get_today());
    }
    frm.trigger("render_dashboard");
  },
  received_at_warehouse: function (frm) {
    if (frm.doc.received_at_warehouse) {
      frm.set_value("received_date", frappe.datetime.get_today());
      frm.set_value("time_of_received", frappe.datetime.now_time());
      frm.set_value("received_warehouse", "Imported  Finished Phr Incoming Warehouse - Onco");
      frm.set_value("source_warehouse", "Imported  Finished Phr Incoming Warehouse - Onco");
      frm.set_value("target_warehouse", "Imported Finished Phr Receipt and Inspection Warehouse  - Onco");
    }
    frm.trigger("render_dashboard");
  },

  render_dashboard: function (frm) {
    // Steps Mapping
    const steps = [
      { label: "Acceptance", done: has_attachments(frm) },
      { label: "Arrival", done: frm.doc.arrived },
      { label: "Bank Auth", done: frm.doc.bank_authenticated },
      { label: "Restricted Release", done: frm.doc.restricted_release_status },
      { label: "Customs Release", done: frm.doc.customs_release_status },
      { label: "Warehouse Receipt", done: frm.doc.received_at_warehouse }
    ];

    let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 20px; background-color: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
        `;

    steps.forEach((step, index) => {
      let color = step.done ? "#48bb78" : "#a0aec0"; // Green vs Gray
      let icon = step.done ? "✓" : (index + 1);
      let weight = step.done ? "bold" : "normal";

      html += `
                <div style="text-align: center; flex: 1;">
                    <div style="
                        width: 30px; 
                        height: 30px; 
                        background-color: ${color}; 
                        color: white; 
                        border-radius: 50%; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center;
                        margin: 0 auto 8px;
                        font-weight: bold;
                    ">
                        ${icon}
                    </div>
                    <div style="font-size: 12px; color: ${step.done ? '#2d3748' : '#718096'}; font-weight: ${weight};">
                        ${step.label}
                    </div>
                </div >
  `;

      // Add connector line except for last item
      if (index < steps.length - 1) {
        html += `<div style="flex: 1; height: 2px; background-color: #e2e8f0; margin-top: -20px;"></div>`;
      }
    });

    html += `</div>`;

    frm.fields_dict['shipment_status_dashboard'].wrapper.innerHTML = html;
  }
});

function has_attachments(frm) {
  // Check mode of shipping is selected
  if (!frm.doc.mode_of_shipping) {
    return false;
  }

  // Check freight-specific fields
  var freight_complete = false;
  if (frm.doc.mode_of_shipping === "Air freight") {
    freight_complete = !!frm.doc.awb_attach && !!frm.doc.awb_no && !!frm.doc.awb_date;
  } else if (frm.doc.mode_of_shipping === "Sea freight") {
    freight_complete = !!frm.doc.swb_attach && !!frm.doc.swb_no && !!frm.doc.swb_date;
  }

  // Check all required attachments
  return freight_complete &&
    !!frm.doc.invoice &&
    !!frm.doc.packing_list &&
    !!frm.doc.certificate_of_analysis_ &&
    !!frm.doc.certificate_of_origin;
}

frappe.ui.form.on('Shipment Invoice', {
  purchase_invoice: function (frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    if (row.purchase_invoice) {
      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "Purchase Invoice",
          name: row.purchase_invoice
        },
        callback: function (r) {
          if (r.message) {
            var invoice = r.message;
            console.log("Fetched Invoice for Row:", invoice);

            frappe.model.set_value(cdt, cdn, "invoice_no", invoice.bill_no || invoice.name);
            frappe.model.set_value(cdt, cdn, "invoice_date", invoice.posting_date);

            // Fetch all items
            if (invoice.items && invoice.items.length > 0) {
              // The first item uses the current row
              var first_item = invoice.items[0];
              frappe.model.set_value(cdt, cdn, "item_code", first_item.item_code);
              frappe.model.set_value(cdt, cdn, "item_name", first_item.item_name);
              frappe.model.set_value(cdt, cdn, "qty", first_item.qty);
              frappe.model.set_value(cdt, cdn, "uom", first_item.uom);
              frappe.model.set_value(cdt, cdn, "rate", first_item.rate);
              frappe.model.set_value(cdt, cdn, "amount", first_item.amount);
              frappe.model.set_value(cdt, cdn, "batch_no", first_item.batch_no || "");
              frappe.model.set_value(cdt, cdn, "serial_no", first_item.serial_no || "");
              frappe.model.set_value(cdt, cdn, "serial_and_batch_bundle", first_item.serial_and_batch_bundle || "");
              frappe.model.set_value(cdt, cdn, "expiry_date", first_item.expiry_date || "");

              // For any subsequent items, we need to add new rows to the child table
              if (invoice.items.length > 1) {
                // Wait for the first row to be set, then add others
                setTimeout(() => {
                  for (let i = 1; i < invoice.items.length; i++) {
                    let item = invoice.items[i];
                    let new_row = frappe.model.add_child(frm.doc, "Shipment Invoice", "custom_invoices");

                    new_row.purchase_invoice = invoice.name;
                    new_row.invoice_no = invoice.bill_no || invoice.name;
                    new_row.invoice_date = invoice.posting_date;
                    new_row.item_code = item.item_code;
                    new_row.item_name = item.item_name;
                    new_row.qty = item.qty;
                    new_row.uom = item.uom;
                    new_row.rate = item.rate;
                    new_row.amount = item.amount;
                    new_row.batch_no = item.batch_no || "";
                    new_row.serial_no = item.serial_no || "";
                    new_row.serial_and_batch_bundle = item.serial_and_batch_bundle || "";
                    new_row.expiry_date = item.expiry_date || "";
                  }
                  frm.refresh_field("custom_invoices");
                }, 100);
              }
            }
          }
        }
      });
    }
  }
});
