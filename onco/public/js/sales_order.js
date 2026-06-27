frappe.ui.form.on("Sales Order", {
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
            frm.fields_dict.items.grid.toggle_reqd("delivery_date", false);
        }

        if (!frm.doc.delivery_date && frm.doc.docstatus == 1) {
            setTimeout(function () {
                frm.page.set_indicator(__("Set Delivery Date"), "orange");
                frm.dashboard.set_headline_alert(
                    __("Please set Delivery Date to proceed with delivery."),
                    "alert-warning"
                );
            }, 500);
        }
    },

    order_type: function(frm) {
        if (frm.fields_dict.items && frm.fields_dict.items.grid) {
            frm.fields_dict.items.grid.toggle_reqd("delivery_date", false);
        }
    },

    skip_delivery_note: function(frm) {
        if (frm.fields_dict.items && frm.fields_dict.items.grid) {
            frm.fields_dict.items.grid.toggle_reqd("delivery_date", false);
        }
    }
});
