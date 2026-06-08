// Tenders Technical Offer Client Script
// Script Type: Client Script
// Reference Document Type: Tenders
// DocType Event: refresh

frappe.ui.form.on('Tenders', {
    refresh: function(frm) {
        // Add Technical Offer button only for Awarded Tenders
        if (!frm.is_new() && frm.doc.tender_type === 'Awarded Tenders') {
            frm.add_custom_button(__('Add Technical Offer'), function() {
                open_technical_offer_dialog(frm);
            }, __('Offers')).addClass('btn-success');
        }
    }
});

// Function to open technical offer selection dialog
function open_technical_offer_dialog(frm) {
    // Check if we have suppliers configured
    if (!frm.doc.tender_supplier || frm.doc.tender_supplier.length === 0) {
        frappe.msgprint(__('Please add suppliers in the Tender Supplier table first'));
        return;
    }

    let dialog = new frappe.ui.Dialog({
        title: __('Add Technical Offer'),
        fields: [
            {
                fieldname: 'offer_type',
                label: __('Add Technical Offer For'),
                fieldtype: 'Select',
                options: get_available_technical_offer_types(frm),
                reqd: 1,
                onchange: function() {
                    let offer_type = dialog.get_value('offer_type');
                    toggle_technical_distributor_field(dialog, offer_type, frm);
                }
            },
            {
                fieldname: 'distributor',
                label: __('Distributor'),
                fieldtype: 'Select',
                options: get_available_technical_distributors(frm),
                depends_on: 'eval:doc.offer_type=="Distributor"',
                reqd: 0
            },
            {
                fieldname: 'section_break',
                fieldtype: 'Section Break'
            },
            {
                fieldname: 'date_of_submission',
                label: __('Date of Submission'),
                fieldtype: 'Date',
                default: frappe.datetime.get_today(),
                reqd: 1
            },
            {
                fieldname: 'subject',
                label: __('Subject'),
                fieldtype: 'Data',
                reqd: 1
            },
            {
                fieldname: 'attachment',
                label: __('Attachment'),
                fieldtype: 'Attach',
                reqd: 1
            }
        ],
        primary_action_label: __('Add Technical Offer'),
        primary_action: function() {
            process_technical_offer(dialog, frm);
        }
    });

    dialog.show();
}

// Get available technical offer types based on supplying_by configuration
function get_available_technical_offer_types(frm) {
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

// Get available distributors from tender_supplier table for technical offers
function get_available_technical_distributors(frm) {
    let distributors = [];
    
    frm.doc.tender_supplier.forEach(function(row) {
        if (row.supplier && row.supplying_by === 'By Distributor') {
            distributors.push(row.supplier);
        }
    });

    return distributors.join('\n');
}

// Toggle distributor field visibility and requirement for technical offers
function toggle_technical_distributor_field(dialog, offer_type, frm) {
    let distributor_field = dialog.get_field('distributor');
    
    if (offer_type === 'Distributor') {
        distributor_field.df.reqd = 1;
        distributor_field.refresh();
    } else {
        distributor_field.df.reqd = 0;
        distributor_field.refresh();
    }
}

// Process and save technical offer
function process_technical_offer(dialog, frm) {
    let offer_type = dialog.get_value('offer_type');
    let distributor = dialog.get_value('distributor');
    let date_of_submission = dialog.get_value('date_of_submission');
    let subject = dialog.get_value('subject');
    let attachment = dialog.get_value('attachment');

    // Validate required fields
    if (!date_of_submission || !subject || !attachment) {
        frappe.msgprint(__('Please fill all required fields including attachment'));
        return;
    }

    // Validate distributor selection for distributor offers
    if (offer_type === 'Distributor' && !distributor) {
        frappe.msgprint(__('Please select a distributor'));
        return;
    }

    let technical_offer_data = {
        date_of_submission: date_of_submission,
        subject: subject,
        attachment: attachment
    };

    if (offer_type === 'Distributor') {
        technical_offer_data.distributor = distributor;
    }

    // Add technical offer to the appropriate table
    if (offer_type === 'Onco') {
        add_onco_technical_offer(frm, technical_offer_data);
    } else {
        add_distributor_technical_offer(frm, technical_offer_data);
    }

    // Save the document
    frm.save().then(() => {
        frappe.msgprint(__('Technical offer added successfully'));
        dialog.hide();
    });
}

// Add Onco technical offer
function add_onco_technical_offer(frm, offer_data) {
    let new_row = frm.add_child('onco_technical_offer');
    Object.assign(new_row, offer_data);
    frm.refresh_field('onco_technical_offer');
}

