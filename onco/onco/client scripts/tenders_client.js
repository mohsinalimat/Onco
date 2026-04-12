frappe.ui.form.on("Tenders", "onload", function(frm) {
    cur_frm.set_query("active_ingredient", function() {
        return {
            "filters": {
                "group": "ANTI-BLEEDING DRUGS"
            }
        };
    });
});

frappe.ui.form.on("Tenders Items", "onload", function(frm) {
    cur_frm.set_query("active_ingredient", function() {
        return {
            "filters": {
                "group": "ANTI-BLEEDING DRUGS"
            }
        };
    });
});