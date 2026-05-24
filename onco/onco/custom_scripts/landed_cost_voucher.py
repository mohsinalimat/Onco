# Copyright (c) 2026, Onco and contributors

"""
Landed Cost Voucher Customizations
- Auto-fetch vendor invoices based on Shipment ID (multi-shipment table)
- Cumulative tracking (allocated, already used, remaining)
- Vendor invoice details in taxes table
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_vendor_invoices_for_shipment(shipment_id, company):
    """
    Fetch all vendor service Purchase Invoices linked to a shipment
    via the Shipment Allocation Reference child table, with cumulative tracking.

    Args:
        shipment_id: The Shipment document name
        company: Company name for filtering

    Returns:
        List of vendor invoices with allocation & cumulative details
    """
    if not shipment_id:
        frappe.throw(_("Shipment ID is required"))

    vendor_invoices = frappe.db.sql("""
        SELECT DISTINCT
            pi.name,
            pi.supplier,
            pi.supplier_name,
            pi.posting_date,
            pi.grand_total,
            pi.currency,
            pi.bill_no,
            pi.remarks,
            sar.amount as allocated_to_shipment
        FROM
            `tabPurchase Invoice` pi
        INNER JOIN
            `tabShipment Allocation Reference` sar
            ON sar.parent = pi.name
            AND sar.parenttype = 'Purchase Invoice'
            AND sar.parentfield = 'custom_shipment_allocation'
        WHERE
            sar.shipment_id = %(shipment_id)s
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

    result = []
    for invoice in vendor_invoices:
        expense_account = get_primary_expense_account(invoice.name)

        already_used = get_already_used_in_lcv(invoice.name, shipment_id)
        remaining = invoice.allocated_to_shipment - already_used
        if remaining < 0:
            remaining = 0

        result.append({
            'name': invoice.name,
            'supplier': invoice.supplier,
            'supplier_name': invoice.supplier_name,
            'posting_date': invoice.posting_date,
            'grand_total': invoice.grand_total,
            'currency': invoice.currency,
            'bill_no': invoice.bill_no or '',
            'expense_account': expense_account,
            'allocated_to_shipment': invoice.allocated_to_shipment,
            'already_used': already_used,
            'remaining': remaining,
            'description': f"{invoice.supplier_name} - {invoice.name}"
                + (f" ({invoice.remarks})" if invoice.remarks else "")
        })

    return result


def get_already_used_in_lcv(purchase_invoice_name, shipment_id):
    """
    Calculate how much of a vendor invoice's allocation to a specific shipment
    has already been consumed by submitted Landed Cost Vouchers.

    Args:
        purchase_invoice_name: The vendor Purchase Invoice name
        shipment_id: The Shipment ID

    Returns:
        Total amount already used in submitted LCVs
    """
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(tax.amount), 0) as used
        FROM `tabLanded Cost Taxes and Charges` tax
        INNER JOIN `tabLanded Cost Voucher` lcv
            ON tax.parent = lcv.name
        WHERE
            tax.custom_vendor_invoice = %(pi)s
            AND lcv.custom_shipment_id = %(shipment)s
            AND lcv.docstatus = 1
    """, {
        'pi': purchase_invoice_name,
        'shipment': shipment_id
    }, as_dict=True)

    return result[0].used if result else 0


def get_primary_expense_account(purchase_invoice_name):
    """
    Get the primary expense account from a Purchase Invoice
    Uses the most common expense account from invoice items
    """
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

    default_account = frappe.db.get_value(
        'Purchase Invoice',
        purchase_invoice_name,
        'against_expense_account'
    )

    if default_account:
        return default_account.split(',')[0].strip()

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
    Ensures all linked PIs reference the same shipment via the allocation table
    """
    if doc.custom_shipment_id and doc.purchase_receipts:
        for voucher_row in doc.purchase_receipts:
            if voucher_row.receipt_document and voucher_row.receipt_document_type == 'Purchase Invoice':
                pi_shipments = frappe.db.sql("""
                    SELECT shipment_id
                    FROM `tabShipment Allocation Reference`
                    WHERE parent = %(pi)s
                        AND parenttype = 'Purchase Invoice'
                        AND parentfield = 'custom_shipment_allocation'
                """, {'pi': voucher_row.receipt_document}, as_dict=True)

                if pi_shipments:
                    pi_shipment_ids = [s.shipment_id for s in pi_shipments]
                    if doc.custom_shipment_id not in pi_shipment_ids:
                        frappe.throw(_(
                            "Purchase Invoice {0} is allocated to shipments {1}, "
                            "but this Landed Cost Voucher is for Shipment {2}"
                        ).format(
                            voucher_row.receipt_document,
                            ', '.join(pi_shipment_ids),
                            doc.custom_shipment_id
                        ))

                legacy_shipment = frappe.db.get_value(
                    'Purchase Invoice',
                    voucher_row.receipt_document,
                    'custom_shipments'
                )

                if legacy_shipment and legacy_shipment != doc.custom_shipment_id:
                    frappe.throw(_(
                        "Purchase Invoice {0} belongs to Shipment {1} (goods shipment), "
                        "but this Landed Cost Voucher is for Shipment {2}"
                    ).format(voucher_row.receipt_document, legacy_shipment, doc.custom_shipment_id))


def before_submit_landed_cost_voucher(doc, method):
    """
    Before submit hook for Landed Cost Voucher
    Log the landed cost application on the Shipment document
    """
    if doc.custom_shipment_id:
        try:
            shipment_doc = frappe.get_doc('Shipments', doc.custom_shipment_id)
            shipment_doc.add_comment(
                'Info',
                f'Landed Cost Voucher {doc.name} applied with total charges: {doc.total_taxes_and_charges}'
            )
        except Exception as e:
            frappe.log_error(f"Could not add comment to Shipment: {str(e)}")


@frappe.whitelist()
def get_shipment_from_purchase_invoice(purchase_invoice):
    """
    Get the first Shipment ID from a Purchase Invoice's allocation table.
    Returns the first shipment found in Shipment Allocation Reference,
    or the legacy custom_shipments field as fallback.
    """
    if not purchase_invoice:
        return None

    shipments = frappe.db.sql("""
        SELECT shipment_id
        FROM `tabShipment Allocation Reference`
        WHERE parent = %(pi)s
            AND parenttype = 'Purchase Invoice'
            AND parentfield = 'custom_shipment_allocation'
        ORDER BY idx ASC
        LIMIT 1
    """, {'pi': purchase_invoice}, as_dict=True)

    if shipments:
        return shipments[0].shipment_id

    legacy = frappe.db.get_value('Purchase Invoice', purchase_invoice, 'custom_shipments')
    return legacy or None
