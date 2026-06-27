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

function set_price_list_query(frm) {
    frm.set_query('selling_price_list', function () {
        return {
            query: 'onco.onco.item_query.filter_apply_price_lists',
            filters: { customer: frm.doc.customer || '' }
        };
    });
}

frappe.ui.form.on("Sales Order", {
    refresh: function (frm) {
        set_so_item_query(frm);
        set_price_list_query(frm);
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

    customer: function (frm) {
        set_price_list_query(frm);
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
