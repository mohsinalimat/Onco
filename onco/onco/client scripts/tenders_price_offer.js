// Tenders Price Offer Client Script
// Script Type: Client Script
// Reference Document Type: Tenders
// DocType Event: refresh

frappe.ui.form.on('Tenders', {
    refresh: function(frm) {
        // Add Price Offer button only for Awarded Tenders
        if (!frm.is_new() && frm.doc.tender_type === 'Awarded Tenders') {
            frm.add_custom_button(__('Add Price Offer'), function() {
                open_price_offer_dialog(frm);
            }, __('Offers')).addClass('btn-primary');
        }
    }
});

// Function to open price offer selection dialog
function open_price_offer_dialog(frm) {
    // Check if we have suppliers configured
    if (!frm.doc.tender_supplier || frm.doc.tender_supplier.length === 0) {
        frappe.msgprint(__('Please add suppliers in the Tender Supplier table first'));
        return;
    }

    // Check if we have items in tender
    if (!frm.doc.item_tender || frm.doc.item_tender.length === 0) {
        frappe.msgprint(__('Please add items in the Item Tender table first'));
        return;
    }

    let dialog = new frappe.ui.Dialog({
        title: __('Add Price Offer'),
        size: 'extra-large', // Increased width for better display
        fields: [
            {
                fieldname: 'offer_type',
                label: __('Add Offer For'),
                fieldtype: 'Select',
                options: get_available_offer_types(frm),
                reqd: 1,
                onchange: function() {
                    let offer_type = dialog.get_value('offer_type');
                    toggle_distributor_field(dialog, offer_type, frm);
                }
            },
            {
                fieldname: 'distributor',
                label: __('Distributor'),
                fieldtype: 'Select',
                options: get_available_distributors(frm),
                depends_on: 'eval:doc.offer_type=="Distributor"',
                reqd: 0,
                onchange: function() {
                    let offer_type = dialog.get_value('offer_type');
                    let distributor = dialog.get_value('distributor');
                    if (offer_type === 'Distributor' && distributor) {
                        display_items_for_selection(dialog, frm, offer_type);
                    }
                }
            },
            {
                fieldname: 'section_break',
                fieldtype: 'Section Break'
            },
            {
                fieldname: 'items_html',
                fieldtype: 'HTML',
                options: '<div id="items_selection_area"><p class="text-muted">Please select offer type and distributor (if applicable) to see available items.</p></div>'
            }
        ],
        primary_action_label: __('Add Offers'),
        primary_action: function() {
            process_price_offers(dialog, frm);
        }
    });

    dialog.show();
}

// Get available offer types based on supplying_by configuration
function get_available_offer_types(frm) {
    let options = [];
    let supplying_options = [];
    
    // Get unique supplying_by values from tender_supplier table
    frm.doc.tender_supplier.forEach(function(row) {
        if (row.supplying_by && supplying_options.indexOf(row.supplying_by) === -1) {
            supplying_options.push(row.supplying_by);
        }
    });

    // Check main supplying_by field as well
    if (frm.doc.supplying_by && supplying_options.indexOf(frm.doc.supplying_by) === -1) {
        supplying_options.push(frm.doc.supplying_by);
    }

    // Add Onco option if applicable
    if (supplying_options.includes('Oncopharm') || supplying_options.includes('Oncopharm & Distributor')) {
        options.push('Onco');
    }

    // Add Distributor option if applicable
    if (supplying_options.includes('Distributor') || supplying_options.includes('Oncopharm & Distributor')) {
        options.push('Distributor');
    }

    return options.join('\n');
}

// Get available distributors from tender_supplier table
function get_available_distributors(frm) {
    let distributors = [];
    
    frm.doc.tender_supplier.forEach(function(row) {
        if (row.supplier && row.supplying_by === 'By Distributor') {
            distributors.push(row.supplier);
        }
    });

    return distributors.join('\n');
}

// Toggle distributor field visibility and requirement
function toggle_distributor_field(dialog, offer_type, frm) {
    let distributor_field = dialog.get_field('distributor');
    
    if (offer_type === 'Distributor') {
        distributor_field.df.reqd = 1;
        distributor_field.refresh();
        
        // Clear items display and show message to select distributor first
        dialog.fields_dict.items_html.$wrapper.html(
            '<div class="alert alert-info"><i class="fa fa-info-circle"></i> Please select a distributor first to see available items.</div>'
        );
    } else {
        distributor_field.df.reqd = 0;
        distributor_field.refresh();
        
        // Update items display for Onco immediately
        display_items_for_selection(dialog, frm, offer_type);
    }
}

// Display items for selection with existing offers check
function display_items_for_selection(dialog, frm, offer_type) {
    let distributor = dialog.get_value('distributor');
    
    // For distributor offers, ensure distributor is selected
    if (offer_type === 'Distributor' && !distributor) {
        return;
    }
    
    let items_html = '<h5 style="color: #2c3e50; margin-bottom: 15px;">Select Items for Price Offer:</h5>';
    items_html += '<div class="items-grid" style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 6px; padding: 10px;">';

    frm.doc.item_tender.forEach(function(item, index) {
        let existing_offer = check_existing_offer(frm, item.item_code, offer_type, distributor);
        let border_color = existing_offer ? '#f39c12' : '#ddd';
        let bg_color = existing_offer ? '#fff3cd' : '#ffffff';
        let offer_badge = existing_offer ? 
            `<span class="badge badge-warning" style="margin-left: 10px;">Existing Offer</span>` : 
            `<span class="badge badge-success" style="margin-left: 10px;">New Offer</span>`;
        
        items_html += `
            <div class="item-row" style="border: 2px solid ${border_color}; margin: 8px 0; padding: 15px; border-radius: 6px; background-color: ${bg_color};">
                <div class="row">
                    <div class="col-md-12" style="margin-bottom: 10px;">
                        <input type="checkbox" id="item_${index}" value="${item.item_code}" style="transform: scale(1.2); margin-right: 8px;">
                        <label for="item_${index}" style="font-weight: bold; font-size: 14px;">
                            ${item.item_code} - ${item.item_name || ''}
                        </label>
                        ${offer_badge}
                        ${existing_offer ? `<br><small class="text-warning" style="font-weight: bold;">Current: Qty ${existing_offer.quantity} @ Price ${existing_offer.price}</small>` : ''}
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-2">
                        <label style="font-weight: bold; color: #666;">Tender Qty:</label><br>
                        <span class="badge badge-info" style="font-size: 12px;">${item.tender_qty || 0}</span>
                    </div>
                    <div class="col-md-2">
                        <label style="font-weight: bold; color: #666;">Quantity:</label>
                        <input type="number" class="form-control" id="qty_${index}" 
                               value="${existing_offer ? existing_offer.quantity : (item.tender_qty || 0)}" 
                               min="0" step="0.01" style="font-weight: bold;" onchange="calculate_amount(${index})">
                    </div>
                    <div class="col-md-2">
                        <label style="font-weight: bold; color: #666;">Price:</label>
                        <input type="number" class="form-control" id="price_${index}" 
                               value="${existing_offer ? existing_offer.price : 0}" 
                               min="0" step="0.01" style="font-weight: bold;" onchange="calculate_amount(${index})">
                    </div>
                    ${offer_type === 'Distributor' ? `
                    <div class="col-md-2">
                        <label style="font-weight: bold; color: #666;">Discount %:</label>
                        <input type="number" class="form-control" id="discount_${index}" 
                               value="${existing_offer ? existing_offer.discount_percent : 0}" 
                               min="0" max="100" step="0.01" style="font-weight: bold;">
                        <small class="text-muted">For display only</small>
                    </div>
                    <div class="col-md-2">
                        <label style="font-weight: bold; color: #666;">Credit Limit:</label>
                        <input type="text" class="form-control" id="credit_${index}" 
                               value="${existing_offer ? existing_offer.credit_limit : ''}" 
                               placeholder="Enter credit terms" style="font-weight: bold;">
                    </div>
                    ` : '<div class="col-md-4"></div>'}
                    <div class="col-md-2">
                        <label style="font-weight: bold; color: #666;">Amount:</label><br>
                        <span class="badge badge-primary" style="font-size: 14px; padding: 8px 12px;" id="amount_${index}">
                            ${existing_offer ? existing_offer.amount : 0}
                        </span>
                    </div>
                </div>
            </div>
        `;
    });

    items_html += '</div>';
    
    // Add JavaScript for amount calculation (without discount effect)
    items_html += `
        <script>
            function calculate_amount(index) {
                let qty = parseFloat(document.getElementById('qty_' + index).value) || 0;
                let price = parseFloat(document.getElementById('price_' + index).value) || 0;
                
                // Amount calculation without discount effect (discount is just for display)
                let amount = qty * price;
                document.getElementById('amount_' + index).textContent = amount.toFixed(2);
            }
            
            // Calculate amounts for all items on load
            setTimeout(function() {
                ${frm.doc.item_tender.map((item, index) => `calculate_amount(${index});`).join('\n                ')}
            }, 100);
        </script>
    `;

    dialog.fields_dict.items_html.$wrapper.html(items_html);
}

// Check if offer already exists for item
function check_existing_offer(frm, item_code, offer_type, distributor) {
    let existing_offer = null;
    
    if (offer_type === 'Onco') {
        // Check onco_price_offer table
        if (frm.doc.onco_price_offer) {
            existing_offer = frm.doc.onco_price_offer.find(offer => offer.item === item_code);
        }
    } else if (offer_type === 'Distributor' && distributor) {
        // Check distributors_price_offer table
        if (frm.doc.distributors_price_offer) {
            existing_offer = frm.doc.distributors_price_offer.find(offer => 
                offer.item === item_code && offer.distributor === distributor
            );
        }
    }
    
    return existing_offer;
}

// Process and save price offers
function process_price_offers(dialog, frm) {
    let offer_type = dialog.get_value('offer_type');
    let distributor = dialog.get_value('distributor');
    let selected_items = [];

    // Validate distributor selection for distributor offers
    if (offer_type === 'Distributor' && !distributor) {
        frappe.msgprint(__('Please select a distributor'));
        return;
    }

    // Collect selected items and their data
    let validation_errors = [];
    
    frm.doc.item_tender.forEach(function(item, index) {
        let checkbox = document.getElementById(`item_${index}`);
        if (checkbox && checkbox.checked) {
            let qty = parseFloat(document.getElementById(`qty_${index}`).value) || 0;
            let price = parseFloat(document.getElementById(`price_${index}`).value) || 0;
            let amount = qty * price;
            
            if (qty <= 0 || price <= 0) {
                validation_errors.push(`Please enter valid quantity and price for item: ${item.item_code}`);
                return;
            }

            let offer_data = {
                item: item.item_code,
                item_group: item.item_group,
                quantity: qty,
                price: price,
                amount: amount,
                start_date: frm.doc.tender_start_date,
                end_date: frm.doc.tender_end_date
            };

            if (offer_type === 'Distributor') {
                let discount = parseFloat(document.getElementById(`discount_${index}`).value) || 0;
                let credit_limit = document.getElementById(`credit_${index}`).value || '';
                
                offer_data.distributor = distributor;
                offer_data.discount_percent = discount;
                offer_data.credit_limit = credit_limit;
                // Amount calculation without discount effect (discount is just for display)
                offer_data.amount = qty * price;
            }

            selected_items.push(offer_data);
        }
    });

    // Check for validation errors
    if (validation_errors.length > 0) {
        frappe.msgprint(validation_errors.join('<br>'));
        return;
    }

    if (selected_items.length === 0) {
        frappe.msgprint(__('Please select at least one item'));
        return;
    }

    // Add or update offers in the appropriate table
    selected_items.forEach(function(offer_data) {
        if (offer_type === 'Onco') {
            add_or_update_onco_offer(frm, offer_data);
        } else {
            add_or_update_distributor_offer(frm, offer_data);
        }
    });

    // Mark form as dirty to enable save
    frm.dirty();
    
    // Save the document
    frm.save().then(() => {
        frappe.msgprint(__(`${selected_items.length} price offer(s) processed successfully`));
        dialog.hide();
    }).catch((error) => {
        frappe.msgprint(__('Error saving offers: ') + error.message);
    });
}

// Add or update Onco price offer
function add_or_update_onco_offer(frm, offer_data) {
    // Check if offer already exists
    let existing_row = null;
    if (frm.doc.onco_price_offer) {
        existing_row = frm.doc.onco_price_offer.find(row => row.item === offer_data.item);
    }

    if (existing_row) {
        // Update existing offer - always treat as valid change since user interacted
        Object.assign(existing_row, offer_data);
    } else {
        // Add new offer
        let new_row = frm.add_child('onco_price_offer');
        Object.assign(new_row, offer_data);
    }
    
    frm.refresh_field('onco_price_offer');
}

// Add or update Distributor price offer
function add_or_update_distributor_offer(frm, offer_data) {
    // Check if offer already exists
    let existing_row = null;
    if (frm.doc.distributors_price_offer) {
        existing_row = frm.doc.distributors_price_offer.find(row => 
            row.item === offer_data.item && row.distributor === offer_data.distributor
        );
    }

    if (existing_row) {
        // Update existing offer - always treat as valid change since user interacted
        Object.assign(existing_row, offer_data);
    } else {
        // Add new offer
        let new_row = frm.add_child('distributors_price_offer');
        Object.assign(new_row, offer_data);
    }
    
    frm.refresh_field('distributors_price_offer');
}
