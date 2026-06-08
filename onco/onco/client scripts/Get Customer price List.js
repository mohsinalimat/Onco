frappe.ui.form.on('Customer Purchase Order', {
    customer: function(frm) {
        filter_price_list(frm);
    },
    
    onload: function(frm) {
        if (frm.doc.customer) {
            filter_price_list(frm);
        }
    },
    
    refresh: function(frm) {
        if (frm.doc.customer) {
            filter_price_list(frm);
        }
    }
});

function filter_price_list(frm) {
    if (!frm.doc.customer) {
        return;
    }
    
    // Get customer's group
    frappe.db.get_value('Customer', frm.doc.customer, 'customer_group', (r) => {
        if (r && r.customer_group) {
            let customer_group = r.customer_group;
            
            // Get all enabled selling price lists
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Price List',
                    filters: {
                        selling: 1,
                        enabled: 1
                    },
                    fields: ['name'],
                    limit_page_length: 0
                },
                callback: function(response) {
                    if (response.message && response.message.length > 0) {
                        check_applicable_price_lists(frm, response.message, customer_group);
                    } else {
                        show_no_price_list_message(frm, customer_group);
                    }
                }
            });
        }
    });
}

function check_applicable_price_lists(frm, price_lists, customer_group) {
    let applicable_price_lists = [];
    let completed = 0;
    let total = price_lists.length;
    
    price_lists.forEach(price_list => {
        // Get the full Price List document with child tables
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Price List',
                name: price_list.name
            },
            callback: function(r) {
                if (r.message) {
                    let is_applicable = false;
                    
                    // Check custom_apply_for_customers child table
                    if (r.message.custom_apply_for_customers && r.message.custom_apply_for_customers.length > 0) {
                        let customer_found = r.message.custom_apply_for_customers.some(row => row.customer === frm.doc.customer);
                        if (customer_found) {
                            is_applicable = true;
                        }
                    }
                    
                    // Check custom_apply_for_customer_groups child table
                    if (!is_applicable && r.message.custom_apply_for_customer_groups && r.message.custom_apply_for_customer_groups.length > 0) {
                        let group_found = r.message.custom_apply_for_customer_groups.some(row => row.customer_group === customer_group);
                        if (group_found) {
                            is_applicable = true;
                        }
                    }
                    
                    // Add to applicable list if conditions met
                    if (is_applicable) {
                        applicable_price_lists.push(price_list.name);
                    }
                }
                
                completed++;
                
                // When all price lists are checked, apply filter
                if (completed === total) {
                    apply_price_list_filter(frm, applicable_price_lists, customer_group);
                }
            }
        });
    });
}

function apply_price_list_filter(frm, applicable_price_lists, customer_group) {
    if (applicable_price_lists.length > 0) {
        // Set query to show only applicable price lists
        frm.set_query('price_list', function() {
            return {
                filters: {
                    name: ['in', applicable_price_lists],
                    selling: 1,
                    enabled: 1
                }
            };
        });
        
        // Refresh the field to apply the filter
        frm.refresh_field('price_list');
        
    } else {
        show_no_price_list_message(frm, customer_group);
    }
}

function show_no_price_list_message(frm, customer_group) {
    // Set query to return no results
    frm.set_query('price_list', function() {
        return {
            filters: {
                name: ['in', []],
                selling: 1
            }
        };
    });
    
    // Refresh the field
    frm.refresh_field('price_list');
    
    // Show message to user
    frappe.msgprint({
        title: __('No Price List Available'),
        indicator: 'orange',
        message: __('No price list is configured for customer <b>{0}</b> or customer group <b>{1}</b>.<br><br>Please configure price lists in the Price List master by adding this customer or customer group to the applicable price lists.', 
            [frm.doc.customer, customer_group])
    });
}