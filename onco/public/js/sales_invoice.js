frappe.ui.form.on("Sales Invoice", {
    before_submit: function (frm) {
        if (frm.doc.custom_tender_ref && !frm.doc.custom_price_deviation_approved) {
            // Stop submission and check for deviations via server call
            frappe.validated = false;

            frappe.call({
                method: "onco.onco.doctype.tenders.tenders.check_sales_invoice_deviations",
                args: {
                    sales_invoice_name: frm.doc.name
                },
                callback: function (r) {
                    if (r.message && r.message.deviations && r.message.deviations.length > 0) {
                        let deviation_msg = r.message.deviations.map(d =>
                            `<li><b>${d.item_code}</b>: ${frappe.format(d.invoice_rate, { fieldtype: 'Currency' })} < ${frappe.format(d.tender_price, { fieldtype: 'Currency' })}</li>`
                        ).join("");

                        let msg = `
							<p>${__("Price deviations detected relative to Tender:")} <b>${frm.doc.custom_tender_ref}</b></p>
							<ul>${deviation_msg}</ul>
							<p>${__("Would you like to open the approval fields to resolve this?")}</p>
						`;

                        frappe.confirm(msg,
                            function () {
                                // User clicked Yes - scroll to approval and focus
                                frm.set_df_property("custom_price_deviation_approved", "hidden", 0);
                                frm.scroll_to_field("custom_price_deviation_approved");
                                frappe.show_alert({ message: __("Please check 'Price Deviation Approved' and fill details."), indicator: 'orange' });
                            },
                            function () {
                                // User clicked No - stay as is
                                frappe.msgprint({
                                    title: __("Submission Cancelled"),
                                    indicator: 'red',
                                    message: __("You cannot submit a Sales Invoice with price deviations without approval.")
                                });
                            }
                        );
                    } else {
                        // No deviations or already approved in background, proceed with submission
                        frm.doc.docstatus = 1;
                        frm.save('Submit');
                    }
                }
            });
        }
    }
});
