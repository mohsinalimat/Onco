frappe.ui.form.on("Sales Invoice", {
    refresh: function (frm) {
        if (frm.fields_dict.items && frm.fields_dict.items.grid) {
            frm.fields_dict.items.grid.get_field('item_code').get_query = function () {
                return {
                    filters: {
                        custom_pharmaceutical_item: 1,
                        disabled: 0
                    }
                };
            };
        }
    },

    before_submit: function (frm) {
        if (!frm.doc.custom_tender_ref || frm.doc.custom_price_deviation_approved) {
            return;
        }

        frappe.validated = false;

        frappe.call({
            method: "onco.onco.tender_validation.check_sales_invoice_deviations",
            args: {
                sales_invoice_name: frm.doc.name
            },
            callback: function (r) {
                if (!r.message || !r.message.deviations || r.message.deviations.length === 0) {
                    frm.save('Submit');
                    return;
                }

                let deviation_msg = r.message.deviations.map(d =>
                    `<li><b>${d.item_code}</b> (${d.item_name}): Invoice rate ${format_currency(d.invoice_rate)} < Tender price ${format_currency(d.tender_price)}</li>`
                ).join("");

                let msg = `
                    <p>${__("Price deviations detected relative to Tender:")} <b>${frm.doc.custom_tender_ref}</b></p>
                    <ul>${deviation_msg}</ul>
                    <p>${__("Check 'Price Deviation Approved' and fill the required fields below to proceed.")}</p>
                `;

                frappe.confirm(msg,
                    function () {
                        frm.set_df_property("custom_price_deviation_approved", "hidden", 0);
                        frm.scroll_to_field("custom_price_deviation_approved");
                        frappe.show_alert({ message: __("Please check 'Price Deviation Approved' and fill approval details."), indicator: 'orange' });
                    },
                    function () {
                        frappe.msgprint({
                            title: __("Submission Cancelled"),
                            indicator: 'red',
                            message: __("You cannot submit a Sales Invoice with price deviations without approval.")
                        });
                    }
                );
            }
        });
    }
});

function format_currency(value) {
    if (value === null || value === undefined) return '0.00';
    return parseFloat(value).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}
