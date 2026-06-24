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
        }
    }
});
