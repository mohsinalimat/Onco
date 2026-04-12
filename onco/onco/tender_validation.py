import frappe
from frappe import _

def validate_sales_invoice_tender_price(doc, method):
    """
    Validate Sales Invoice against Tender prices with approval workflow.
    Shows approval dialog for price deviations and validates approved quantities.
    """
    if doc.get("custom_tender_ref"):
        tender = frappe.get_doc("Tenders", doc.custom_tender_ref)
        
        # Build map of tender prices
        tender_prices = {}
        for row in tender.item_tender or []:
            if row.item_code:
                tender_prices[row.item_code] = row.tender_price
        
        # Detect deviations
        deviations = []
        for item in doc.items:
            if item.item_code in tender_prices:
                t_price = tender_prices[item.item_code]
                if item.rate < t_price:
                    deviations.append({
                        "item_code": item.item_code,
                        "invoice_rate": item.rate,
                        "tender_price": t_price,
                        "qty": item.qty
                    })
        
        if deviations:
            # Check if approval is provided
            if not doc.get("custom_price_deviation_approved"):
                # Show approval dialog message
                deviation_msg = "<br>".join([
                    _("Item {0}: Invoice Rate {1} < Tender Price {2}").format(
                        d["item_code"], d["invoice_rate"], d["tender_price"]
                    ) for d in deviations
                ])
                frappe.throw(_(
                    "Price deviations detected. Please approve before submitting:<br><br>{0}<br><br>"
                    "Check 'Price Deviation Approved' and fill approval details."
                ).format(deviation_msg))
            
            # Validate approval details
            if not doc.get("custom_cause_of_deviation"):
                frappe.throw(_("Please provide the 'Cause of Deviation' for the price deviation approval."))
            
            if not doc.get("custom_approved_by"):
                frappe.throw(_("Please specify which manager approved this price deviation in 'Approved By'."))
            
            if not doc.get("custom_approval_date"):
                frappe.throw(_("Please specify the 'Approved Date' for the price deviation approval."))
            
            # Validate approved quantities
            if doc.get("custom_approved_quantities"):
                approved_map = {}
                for appr in doc.custom_approved_quantities:
                    approved_map[appr.item_code] = appr.approved_qty
                
                for item in doc.items:
                    if item.item_code in [d["item_code"] for d in deviations]:
                        approved_qty = approved_map.get(item.item_code, 0)
                        if item.qty > approved_qty:
                            frappe.throw(_(
                                "Item {0}: Quantity {1} exceeds approved quantity {2}"
                            ).format(item.item_code, item.qty, approved_qty))
            
            # Log deviation to Tender
            tender.update_deviation_details(doc.name, doc.items)
            tender.save(ignore_permissions=True)
