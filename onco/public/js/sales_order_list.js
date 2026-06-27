frappe.listview_settings["Sales Order"] = frappe.listview_settings["Sales Order"] || {};

var original_get_indicator = frappe.listview_settings["Sales Order"].get_indicator;

frappe.listview_settings["Sales Order"].get_indicator = function (doc) {
    if (!doc.skip_delivery_note && !doc.delivery_date && doc.docstatus == 1 && flt(doc.per_delivered) < 100) {
        return [__("Set Delivery Date"), "orange", "per_delivered,<,100"];
    }
    if (original_get_indicator) {
        return original_get_indicator(doc);
    }
};
