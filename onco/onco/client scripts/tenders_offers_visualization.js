// Tenders Offers Visualization Client Script
// Script Type: Client Script
// Reference Document Type: Tenders
// DocType Event: refresh, onload_post_render

frappe.ui.form.on('Tenders', {
    refresh: function(frm) {
        // Update visualization when form refreshes
        if (frm.doc.tender_type === 'Awarded Tenders' || frm.doc.tender_type === 'Accepted Tenders') {
            update_offers_visualization(frm);
        }
    },

    onload_post_render: function(frm) {
        // Update visualization after form loads
        if (frm.doc.tender_type === 'Awarded Tenders' || frm.doc.tender_type === 'Accepted Tenders') {
            setTimeout(() => {
                update_offers_visualization(frm);
            }, 500);
        }
    }
});

// Update offers visualization in HTML fields
function update_offers_visualization(frm) {
    update_onco_offers_view(frm);
    update_distributors_offers_view(frm);
}

// Update Onco offers visualization
function update_onco_offers_view(frm) {
    let html_content = generate_onco_offers_html(frm);
    
    // Set the HTML content to the onco_offers_view field
    if (frm.fields_dict.onco_offers_view) {
        frm.fields_dict.onco_offers_view.$wrapper.html(html_content);
    }
}

// Update Distributors offers visualization
function update_distributors_offers_view(frm) {
    let html_content = generate_distributors_offers_html(frm);
    
    // Set the HTML content to the distributors_offers_view field
    if (frm.fields_dict.distributors_offers_view) {
        frm.fields_dict.distributors_offers_view.$wrapper.html(html_content);
    }
}

// Generate HTML for Onco offers
function generate_onco_offers_html(frm) {
    let html = `
        <div class="onco-offers-container" style="padding: 15px; background: #f8f9fa; border-radius: 8px; margin: 10px 0;">
            <h4 style="color: #2c3e50; margin-bottom: 20px; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                <i class="fa fa-building" style="margin-right: 8px;"></i>Oncopharm Offers
            </h4>
    `;

    // Price Offers Section
    html += generate_onco_price_offers_section(frm);
    
    // Technical Offers Section
    html += generate_onco_technical_offers_section(frm);

    html += '</div>';
    return html;
}

// Generate Onco price offers section
function generate_onco_price_offers_section(frm) {
    let html = `
        <div class="price-offers-section" style="margin-bottom: 25px;">
            <h5 style="color: #27ae60; margin-bottom: 15px;">
                <i class="fa fa-money" style="margin-right: 5px;"></i>Price Offers
            </h5>
    `;

    if (frm.doc.onco_price_offer && frm.doc.onco_price_offer.length > 0) {
        html += `
            <div class="table-responsive">
                <table class="table table-bordered table-striped" style="margin-bottom: 0;">
                    <thead style="background: #3498db; color: white;">
                        <tr>
                            <th>Item Code</th>
                            <th>Item Group</th>
                            <th>Quantity</th>
                            <th>Price</th>
                            <th>Amount</th>
                            <th>Start Date</th>
                            <th>End Date</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        let total_amount = 0;
        frm.doc.onco_price_offer.forEach(function(offer) {
            total_amount += (offer.amount || 0);
            html += `
                <tr>
                    <td><strong>${offer.item || ''}</strong></td>
                    <td>${offer.item_group || ''}</td>
                    <td>${format_number(offer.quantity || 0)}</td>
                    <td>${format_currency(offer.price || 0)}</td>
                    <td><strong>${format_currency(offer.amount || 0)}</strong></td>
                    <td>${format_date(offer.start_date)}</td>
                    <td>${format_date(offer.end_date)}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                    <tfoot style="background: #ecf0f1;">
                        <tr>
                            <th colspan="4" style="text-align: right;">Total Amount:</th>
                            <th>${format_currency(total_amount)}</th>
                            <th colspan="2"></th>
                        </tr>
                    </tfoot>
                </table>
            </div>
        `;
    } else {
        html += '<p class="text-muted" style="font-style: italic;">No price offers available</p>';
    }

    html += '</div>';
    return html;
}

// Generate Onco technical offers section
function generate_onco_technical_offers_section(frm) {
    let html = `
        <div class="technical-offers-section">
            <h5 style="color: #8e44ad; margin-bottom: 15px;">
                <i class="fa fa-file-text" style="margin-right: 5px;"></i>Technical Offers
            </h5>
    `;

    if (frm.doc.onco_technical_offer && frm.doc.onco_technical_offer.length > 0) {
        html += '<div class="technical-offers-grid">';

        frm.doc.onco_technical_offer.forEach(function(offer, index) {
            html += `
                <div class="technical-offer-card" style="border: 1px solid #ddd; border-radius: 6px; padding: 15px; margin-bottom: 10px; background: white;">
                    <div class="row">
                        <div class="col-md-3">
                            <strong>Date of Submission:</strong><br>
                            <span class="text-primary">${format_date(offer.date_of_submission)}</span>
                        </div>
                        <div class="col-md-6">
                            <strong>Subject:</strong><br>
                            <span>${offer.subject || ''}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Attachment:</strong><br>
                            ${offer.attachment ? 
                                `<a href="${offer.attachment}" target="_blank" class="btn btn-xs btn-default">
                                    <i class="fa fa-download"></i> Download
                                </a>` : 
                                '<span class="text-muted">No attachment</span>'
                            }
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
    } else {
        html += '<p class="text-muted" style="font-style: italic;">No technical offers available</p>';
    }

    html += '</div>';
    return html;
}

// Generate HTML for Distributors offers
function generate_distributors_offers_html(frm) {
    let html = `
        <div class="distributors-offers-container" style="padding: 15px; background: #f8f9fa; border-radius: 8px; margin: 10px 0;">
            <h4 style="color: #2c3e50; margin-bottom: 20px; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">
                <i class="fa fa-users" style="margin-right: 8px;"></i>Distributors Offers
            </h4>
    `;

    // Price Offers Section
    html += generate_distributors_price_offers_section(frm);
    
    html += '</div>';
    return html;
}

// Generate Distributors price offers section
function generate_distributors_price_offers_section(frm) {
    let html = `
        <div class="price-offers-section" style="margin-bottom: 25px;">
            <h5 style="color: #27ae60; margin-bottom: 15px;">
                <i class="fa fa-money" style="margin-right: 5px;"></i>Price Offers
            </h5>
    `;

    if (frm.doc.distributors_price_offer && frm.doc.distributors_price_offer.length > 0) {
        // Group offers by distributor
        let offers_by_distributor = {};
        frm.doc.distributors_price_offer.forEach(function(offer) {
            let distributor = offer.distributor || 'Unknown';
            if (!offers_by_distributor[distributor]) {
                offers_by_distributor[distributor] = [];
            }
            offers_by_distributor[distributor].push(offer);
        });

        // Create separate table for each distributor in the same section
        Object.keys(offers_by_distributor).forEach(function(distributor, index) {
            let distributor_offers = offers_by_distributor[distributor];
            let distributor_total = 0;

            html += `
                <div class="distributor-table" style="margin-bottom: 25px;">
                    <h6 style="color: #e74c3c; margin-bottom: 10px; padding: 8px 12px; background: #f8f9fa; border-left: 4px solid #e74c3c; border-radius: 4px;">
                        <i class="fa fa-user"></i> ${distributor}
                    </h6>
                    <div class="table-responsive">
                        <table class="table table-bordered table-striped" style="margin-bottom: 0;">
                            <thead style="background: #e74c3c; color: white;">
                                <tr>
                                    <th>Item Code</th>
                                    <th>Item Group</th>
                                    <th>Quantity</th>
                                    <th>Price</th>
                                    <th>Discount %</th>
                                    <th>Amount</th>
                                    <th>Credit Limit</th>
                                    <th>Period</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            distributor_offers.forEach(function(offer) {
                distributor_total += (offer.amount || 0);
                html += `
                    <tr>
                        <td><strong>${offer.item || ''}</strong></td>
                        <td>${offer.item_group || ''}</td>
                        <td>${format_number(offer.quantity || 0)}</td>
                        <td>${format_currency(offer.price || 0)}</td>
                        <td>${format_number(offer.discount_percent || 0)}%</td>
                        <td><strong>${format_currency(offer.amount || 0)}</strong></td>
                        <td>${offer.credit_limit || ''}</td>
                        <td>${format_date(offer.start_date)} - ${format_date(offer.end_date)}</td>
                    </tr>
                `;
            });

            html += `
                            </tbody>
                            <tfoot style="background: #ecf0f1;">
                                <tr>
                                    <th colspan="5" style="text-align: right;">${distributor} Total:</th>
                                    <th style="color: #e74c3c; font-weight: bold;">${format_currency(distributor_total)}</th>
                                    <th colspan="2"></th>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            `;
        });
    } else {
        html += '<p class="text-muted" style="font-style: italic;">No distributor price offers available</p>';
    }

    html += '</div>';
    return html;
}

// Utility function to format currency
function format_currency(amount) {
    if (!amount) return '0.00';
    return parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Utility function to format numbers
function format_number(number) {
    if (!number) return '0';
    return parseFloat(number).toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

// Utility function to format dates
function format_date(date) {
    if (!date) return '';
    return frappe.datetime.str_to_user(date);
}

// Refresh visualization when child tables are updated
frappe.ui.form.on('Onco Price Offer', {
    onco_price_offer_add: function(frm) {
        setTimeout(() => update_onco_offers_view(frm), 100);
    },
    onco_price_offer_remove: function(frm) {
        setTimeout(() => update_onco_offers_view(frm), 100);
    }
});

frappe.ui.form.on('Onco Technical Offer', {
    onco_technical_offer_add: function(frm) {
        setTimeout(() => update_onco_offers_view(frm), 100);
    },
    onco_technical_offer_remove: function(frm) {
        setTimeout(() => update_onco_offers_view(frm), 100);
    }
});

frappe.ui.form.on('Distributors Price Offer', {
    distributors_price_offer_add: function(frm) {
        setTimeout(() => update_distributors_offers_view(frm), 100);
    },
    distributors_price_offer_remove: function(frm) {
        setTimeout(() => update_distributors_offers_view(frm), 100);
    }
});


