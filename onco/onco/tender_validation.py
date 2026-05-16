import frappe
from frappe import _

def validate_sales_order_tender_price(doc, method):
    """
    Validate Sales Order against Tender prices.
    Creates approval requests on save, validates approvals on submit.
    """
    if not doc.get("custom_tender"):
        return
    
    tender = frappe.get_doc("Tenders", doc.custom_tender)
    
    # Build map of tender prices and item costs
    tender_prices = {}
    item_costs = {}
    
    for row in tender.item_tender or []:
        if row.item_code:
            tender_prices[row.item_code] = row.tender_price
            # Get item cost from Item master
            item_doc = frappe.get_doc("Item", row.item_code)
            item_costs[row.item_code] = item_doc.valuation_rate or 0
    
    # Detect items with tender_price < item_cost
    loss_making_items = []
    for item in doc.items:
        if item.item_code in tender_prices:
            t_price = tender_prices[item.item_code]
            i_cost = item_costs.get(item.item_code, 0)
            
            if t_price < i_cost:
                loss_making_items.append({
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": item.qty,
                    "tender_price": t_price,
                    "item_cost": i_cost,
                    "deviation_amount": i_cost - t_price
                })
    
    if not loss_making_items:
        return  # No price deviations, allow normal flow
    
    # ON SAVE: Create approval requests in Tender
    if method == "validate" and doc.docstatus == 0:
        create_approval_requests(doc, tender, loss_making_items)
    
    # ON SUBMIT: Validate approvals
    if method == "on_submit":
        validate_approvals(doc, tender, loss_making_items)


def create_approval_requests(sales_order_doc, tender_doc, loss_making_items):
    """
    Create or update approval request rows in Tender Price Deviation table.
    Called when Sales Order is saved.
    """
    tender_name = tender_doc.name
    
    # Check if approval requests already exist for this Sales Order
    existing_approvals = frappe.db.sql("""
        SELECT name, item
        FROM `tabTender Price Deviation`
        WHERE parent = %s AND sales_order_no = %s
    """, (tender_name, sales_order_doc.name), as_dict=True)
    
    existing_map = {row.item: row.name for row in existing_approvals}
    
    for item_data in loss_making_items:
        item_code = item_data["item_code"]
        
        if item_code in existing_map:
            # Update existing approval request
            frappe.db.set_value("Tender Price Deviation", existing_map[item_code], {
                "order_qty": item_data["qty"],
                "tender_price": item_data["tender_price"],
                "item_cost": item_data["item_cost"],
                "deviation_amount": item_data["deviation_amount"]
            }, update_modified=False)
        else:
            # Create new approval request
            row = frappe.get_doc({
                "doctype": "Tender Price Deviation",
                "parent": tender_name,
                "parenttype": "Tenders",
                "parentfield": "tender_price_deviation",
                "item": item_code,
                "item_name": item_data["item_name"],
                "sales_order_no": sales_order_doc.name,
                "order_qty": item_data["qty"],
                "approved_qty": 0,
                "tender_price": item_data["tender_price"],
                "item_cost": item_data["item_cost"],
                "deviation_amount": item_data["deviation_amount"],
                "deviation_status": "Pending Approval"
            })
            row.insert(ignore_permissions=True)
    
    frappe.db.commit()
    
    # Show message to user
    frappe.msgprint(_(
        "This Sales Order contains items with prices below cost. "
        "An approval request has been created in Tender {0}. "
        "You cannot submit this Sales Order until a manager approves it."
    ).format(tender_name), alert=True, indicator="orange")


def validate_approvals(sales_order_doc, tender_doc, loss_making_items):
    """
    Validate that all loss-making items have been approved.
    Called when Sales Order is submitted.
    """
    # Build map of approvals
    approvals = {}
    for row in tender_doc.tender_price_deviation:
        if row.sales_order_no == sales_order_doc.name:
            approvals[row.item] = row
    
    # Validate each loss-making item
    errors = []
    for item_data in loss_making_items:
        item_code = item_data["item_code"]
        
        if item_code not in approvals:
            errors.append(_(
                "Item {0}: No approval request found in Tender"
            ).format(item_code))
            continue
        
        approval = approvals[item_code]
        
        # Check approval status
        if approval.deviation_status != "Approved":
            errors.append(_(
                "Item {0}: Approval status is '{1}', must be 'Approved'"
            ).format(item_code, approval.deviation_status))
            continue
        
        # Check approved quantity
        if not approval.approved_qty or approval.approved_qty <= 0:
            errors.append(_(
                "Item {0}: Approved quantity is not set"
            ).format(item_code))
            continue
        
        # Check order quantity doesn't exceed approved quantity
        if item_data["qty"] > approval.approved_qty:
            errors.append(_(
                "Item {0}: Order quantity {1} exceeds approved quantity {2}"
            ).format(item_code, item_data["qty"], approval.approved_qty))
            continue
        
        # Validate approval details
        if not approval.approved_by:
            errors.append(_(
                "Item {0}: 'Approved By' is not set"
            ).format(item_code))
        
        if not approval.approved_date:
            errors.append(_(
                "Item {0}: 'Approved Date' is not set"
            ).format(item_code))
        
        if not approval.cause_of_deviation:
            errors.append(_(
                "Item {0}: 'Cause of Deviation' is not set"
            ).format(item_code))
    
    if errors:
        frappe.throw(
            _("Cannot submit Sales Order due to approval issues:<br><br>") + 
            "<br>".join(errors),
            title=_("Price Deviation Approval Required")
        )


def log_deviation_history(doc, method):
    """
    Log approved price deviations to Tender Price Deviation Details.
    Called when Sales Order is submitted.
    Creates permanent historical record.
    """
    if not doc.get("custom_tender"):
        return
    
    tender_name = doc.custom_tender
    tender = frappe.get_doc("Tenders", tender_name)
    
    # Build map of tender prices and item costs
    tender_prices = {}
    item_costs = {}
    
    for row in tender.item_tender or []:
        if row.item_code:
            tender_prices[row.item_code] = row.tender_price
            item_doc = frappe.get_doc("Item", row.item_code)
            item_costs[row.item_code] = item_doc.valuation_rate or 0
    
    # Find loss-making items in this Sales Order
    for item in doc.items:
        if item.item_code in tender_prices:
            t_price = tender_prices[item.item_code]
            i_cost = item_costs.get(item.item_code, 0)
            
            if t_price < i_cost:
                # Calculate loss
                loss_per_unit = i_cost - t_price
                total_loss = loss_per_unit * item.qty
                
                # Find who approved this
                approved_by_user = frappe.db.get_value(
                    "Tender Price Deviation",
                    {"parent": tender_name, "sales_order_no": doc.name, "item": item.item_code},
                    "approved_by"
                ) or frappe.session.user
                
                # Create permanent history record
                history_row = frappe.get_doc({
                    "doctype": "Tender Price Deviation Details",
                    "parent": tender_name,
                    "parenttype": "Tenders",
                    "parentfield": "tender_price_deviation_details",
                    "item_name": item.item_code,
                    "sales_order_no": doc.name,
                    "tender_price": t_price,
                    "item_cost": i_cost,
                    "quantity_with_loss": item.qty,
                    "losses_value": total_loss,
                    "approved_status": "Approved",
                    "approved_by": approved_by_user
                })
                history_row.insert(ignore_permissions=True)
    
    frappe.db.commit()


def update_tender_status(doc, method):
    """
    Update Tender Status table when Sales Order is submitted.
    Tracks supplied quantities against tender quantities.
    """
    if not doc.get("custom_tender"):
        return
    
    tender_name = doc.custom_tender
    
    # Update supplied quantities for each item in the Sales Order
    for item in doc.items:
        # Find matching row in tender_status using SQL
        status_rows = frappe.db.sql("""
            SELECT name, supplied_quantity, tender_quantity
            FROM `tabTender Status`
            WHERE parent = %s AND item_name = %s
        """, (tender_name, item.item_code), as_dict=True)
        
        if status_rows:
            status_row = status_rows[0]
            
            # Calculate new values
            new_supplied_qty = (status_row.supplied_quantity or 0) + item.qty
            tender_qty = status_row.tender_quantity or 0
            new_remaining_qty = tender_qty - new_supplied_qty
            new_fulfillment_percent = (new_supplied_qty / tender_qty * 100) if tender_qty > 0 else 0
            
            # Update directly in database
            frappe.db.set_value("Tender Status", status_row.name, {
                "supplied_quantity": new_supplied_qty,
                "remaining_quantity": new_remaining_qty,
                "fulfillment_percent": new_fulfillment_percent
            }, update_modified=False)
    
    frappe.db.commit()


def revert_tender_status(doc, method):
    """
    Revert Tender Status table when Sales Order is cancelled.
    Reduces supplied quantities.
    """
    if not doc.get("custom_tender"):
        return
    
    tender_name = doc.custom_tender
    
    # Revert supplied quantities for each item in the Sales Order
    for item in doc.items:
        # Find matching row in tender_status using SQL
        status_rows = frappe.db.sql("""
            SELECT name, supplied_quantity, tender_quantity
            FROM `tabTender Status`
            WHERE parent = %s AND item_name = %s
        """, (tender_name, item.item_code), as_dict=True)
        
        if status_rows:
            status_row = status_rows[0]
            
            # Calculate new values
            new_supplied_qty = max(0, (status_row.supplied_quantity or 0) - item.qty)
            tender_qty = status_row.tender_quantity or 0
            new_remaining_qty = tender_qty - new_supplied_qty
            new_fulfillment_percent = (new_supplied_qty / tender_qty * 100) if tender_qty > 0 else 0
            
            # Update directly in database
            frappe.db.set_value("Tender Status", status_row.name, {
                "supplied_quantity": new_supplied_qty,
                "remaining_quantity": new_remaining_qty,
                "fulfillment_percent": new_fulfillment_percent
            }, update_modified=False)
    
    frappe.db.commit()
