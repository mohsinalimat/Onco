# Copyright (c) 2026, Onco and contributors
# For license information, please see license.txt

"""
Landed Cost Voucher Customizations
Auto-fetch vendor invoices based on Shipment ID
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_vendor_invoices_for_shipment(shipment_id, company):
    """
    Fetch all vendor service Purchase Invoices linked to a specific Shipment ID
    via the accounting dimension field custom_shipment_id_dimension
    
    Args:
        shipment_id: The Shipment document name
        company: Company name for filtering
        
    Returns:
        List of vendor invoices with expense account details
    """
    if not shipment_id:
        frappe.throw(_("Shipment ID is required"))
    
    # Query Purchase Invoices that have:
    # 1. custom_shipment_id_dimension = shipment_id (vendor service invoices)
    # 2. docstatus = 1 (submitted)
    # 3. Matching company
    
    vendor_invoices = frappe.db.sql("""
        SELECT 
            pi.name,
            pi.supplier,
            pi.supplier_name,
            pi.posting_date,
            pi.grand_total,
            pi.currency,
            pi.custom_shipment_id_dimension,
            pi.remarks
        FROM 
            `tabPurchase Invoice` pi
        WHERE 
            pi.custom_shipment_id_dimension = %(shipment_id)s
            AND pi.docstatus = 1
            AND pi.company = %(company)s
        ORDER BY 
            pi.posting_date ASC
    """, {
        'shipment_id': shipment_id,
        'company': company
    }, as_dict=True)
    
    if not vendor_invoices:
        return []
    
    # For each invoice, get the primary expense account used
    result = []
    for invoice in vendor_invoices:
        expense_account = get_primary_expense_account(invoice.name)
        
        result.append({
            'name': invoice.name,
            'supplier': invoice.supplier,
            'supplier_name': invoice.supplier_name,
            'posting_date': invoice.posting_date,
            'grand_total': invoice.grand_total,
            'currency': invoice.currency,
            'expense_account': expense_account,
            'description': f"{invoice.supplier_name} - {invoice.name}" + (f" ({invoice.remarks})" if invoice.remarks else "")
        })
    
    return result


def get_primary_expense_account(purchase_invoice_name):
    """
    Get the primary expense account from a Purchase Invoice
    Uses the most common expense account from invoice items
    
    Args:
        purchase_invoice_name: Name of the Purchase Invoice
        
    Returns:
        Expense account name
    """
    # Get expense accounts from Purchase Invoice Items
    accounts = frappe.db.sql("""
        SELECT 
            expense_account,
            COUNT(*) as count,
            SUM(amount) as total_amount
        FROM 
            `tabPurchase Invoice Item`
        WHERE 
            parent = %(invoice)s
            AND expense_account IS NOT NULL
        GROUP BY 
            expense_account
        ORDER BY 
            total_amount DESC
        LIMIT 1
    """, {
        'invoice': purchase_invoice_name
    }, as_dict=True)
    
    if accounts and len(accounts) > 0:
        return accounts[0].expense_account
    
    # Fallback: get from Purchase Invoice header if available
    default_account = frappe.db.get_value(
        'Purchase Invoice',
        purchase_invoice_name,
        'against_expense_account'
    )
    
    if default_account:
        # against_expense_account might be comma-separated
        return default_account.split(',')[0].strip()
    
    # Last resort: return a default expense account for the company
    company = frappe.db.get_value('Purchase Invoice', purchase_invoice_name, 'company')
    default_expense = frappe.db.get_value(
        'Company',
        company,
        'default_expense_account'
    )
    
    return default_expense or ''


def validate_landed_cost_voucher(doc, method):
    """
    Validation hook for Landed Cost Voucher
    Ensures Shipment ID consistency
    
    Args:
        doc: Landed Cost Voucher document
        method: Hook method name
    """
    # If Shipment ID is set, validate that all Purchase Receipts belong to that shipment
    if doc.custom_shipment_id and doc.purchase_receipts:
        for pr_row in doc.purchase_receipts:
            if pr_row.purchase_receipt:
                pr_shipment = frappe.db.get_value(
                    'Purchase Receipt',
                    pr_row.purchase_receipt,
                    ['custom_shipment_ref', 'shipment'],
                    as_dict=True
                )
                
                if pr_shipment:
                    pr_shipment_id = pr_shipment.get('custom_shipment_ref') or pr_shipment.get('shipment')
                    
                    if pr_shipment_id and pr_shipment_id != doc.custom_shipment_id:
                        frappe.throw(_(
                            "Purchase Receipt {0} belongs to Shipment {1}, but this Landed Cost Voucher is for Shipment {2}"
                        ).format(pr_row.purchase_receipt, pr_shipment_id, doc.custom_shipment_id))


def before_submit_landed_cost_voucher(doc, method):
    """
    Before submit hook for Landed Cost Voucher
    Log the landed cost application for audit trail
    
    Args:
        doc: Landed Cost Voucher document
        method: Hook method name
    """
    if doc.custom_shipment_id:
        # Create a comment/log on the Shipment document
        try:
            shipment_doc = frappe.get_doc('Shipments', doc.custom_shipment_id)
            shipment_doc.add_comment(
                'Info',
                f'Landed Cost Voucher {doc.name} applied with total charges: {doc.total_taxes_and_charges}'
            )
        except Exception as e:
            frappe.log_error(f"Could not add comment to Shipment: {str(e)}")


@frappe.whitelist()
def get_shipment_from_purchase_receipt(purchase_receipt):
    """
    Get Shipment ID from a Purchase Receipt
    
    Args:
        purchase_receipt: Purchase Receipt name
        
    Returns:
        Shipment ID or None
    """
    if not purchase_receipt:
        return None
    
    shipment_data = frappe.db.get_value(
        'Purchase Receipt',
        purchase_receipt,
        ['custom_shipment_ref', 'shipment'],
        as_dict=True
    )
    
    if shipment_data:
        return shipment_data.get('custom_shipment_ref') or shipment_data.get('shipment')
    
    return None
