function set_so_item_query(frm) {
    if (!frm.fields_dict.items || !frm.fields_dict.items.grid) return;
    var filters = { custom_pharmaceutical_item: 1, disabled: 0 };
    if (frm.doc.item_group) {
        filters.item_group = frm.doc.item_group;
    }
    frm.fields_dict.items.grid.get_field('item_code').get_query = function () {
        return { filters: filters };
    };
}

frappe.ui.form.on("Sales Order", {
    refresh: function (frm) {
        set_so_item_query(frm);
        if (frm.fields_dict.items && frm.fields_dict.items.grid) {
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

    item_group: function (frm) {
        set_so_item_query(frm);
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
