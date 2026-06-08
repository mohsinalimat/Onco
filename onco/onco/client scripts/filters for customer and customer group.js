frappe.ui.form.on('Customer Purchase Order', {
    // Filter customer_main_group to show only groups (is_group = 1)
    onload: function(frm) {
        frm.set_query('customer_main_group', function() {
            return {
                filters: {
                    'is_group': 1
                }
            };
        });
    },
    
    // When customer_main_group is selected, filter customer_group
    customer_main_group: function(frm) {
        // Clear dependent fields when parent changes
        frm.set_value('customer_group', '');
        frm.set_value('customer', '');
        
        // Set filter for customer_group based on selected customer_main_group
        frm.set_query('customer_group', function() {
            if (frm.doc.customer_main_group) {
                return {
                    filters: {
                        'parent_customer_group': frm.doc.customer_main_group,
                    }
                };
            } else {
                return {
                    filters: {
                        'is_group': 1
                    }
                };
            }
        });
    },
    
    // When customer_group is selected, filter customer
    customer_group: function(frm) {
        // Clear customer when customer_group changes
        frm.set_value('customer', '');
        
        // Set filter for customer based on selected customer_group
        frm.set_query('customer', function() {
            if (frm.doc.customer_group) {
                return {
                    filters: {
                        'customer_group': frm.doc.customer_group
                    }
                };
            }
        });
    }
});