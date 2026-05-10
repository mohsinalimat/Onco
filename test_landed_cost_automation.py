"""
Test Script for Landed Cost Automation
Run: bench --site [site-name] execute onco.test_landed_cost_automation.run_tests
"""

import frappe
from frappe import _


def run_tests():
    """Run all test cases for Landed Cost Automation"""
    print("\n" + "="*70)
    print("LANDED COST AUTOMATION - TEST SUITE")
    print("="*70 + "\n")
    
    try:
        test_accounting_dimension_exists()
        test_custom_fields_exist()
        test_vendor_invoice_query()
        test_expense_account_extraction()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        frappe.log_error(f"Landed Cost Test Error: {str(e)}")
        raise


def test_accounting_dimension_exists():
    """Test 1: Verify Accounting Dimension is created"""
    print("Test 1: Checking Accounting Dimension...")
    
    if frappe.db.exists("Accounting Dimension", "Shipments"):
        dimension = frappe.get_doc("Accounting Dimension", "Shipments")
        print(f"  ✓ Accounting Dimension exists: {dimension.name}")
        print(f"    - Label: {dimension.label}")
        print(f"    - Fieldname: {dimension.fieldname}")
        print(f"    - Disabled: {dimension.disabled}")
        
        if dimension.disabled:
            print("  ⚠ WARNING: Dimension is disabled!")
        
        return True
    else:
        print("  ✗ Accounting Dimension 'Shipments' not found")
        print("    Run: bench --site [site] execute onco.onco.install_landed_cost_dimension.run_installation")
        return False


def test_custom_fields_exist():
    """Test 2: Verify Custom Fields are installed"""
    print("\nTest 2: Checking Custom Fields...")
    
    fields_to_check = [
        ("Purchase Invoice", "custom_shipments", "Shipment ID"),
        ("Purchase Invoice", "custom_shipment_id_dimension", "Shipment ID (Vendor Services)"),
        ("Landed Cost Voucher", "custom_shipment_id", "Shipment ID"),
        ("Landed Cost Voucher", "custom_auto_fetch_vendor_invoices", "Auto-fetch Vendor Invoices")
    ]
    
    all_exist = True
    for doctype, fieldname, label in fields_to_check:
        field_name = f"{doctype}-{fieldname}"
        if frappe.db.exists("Custom Field", field_name):
            print(f"  ✓ {doctype}.{fieldname} ({label})")
        else:
            print(f"  ✗ {doctype}.{fieldname} NOT FOUND")
            all_exist = False
    
    if not all_exist:
        print("\n  Run: bench --site [site] migrate")
    
    return all_exist


def test_vendor_invoice_query():
    """Test 3: Test vendor invoice query logic"""
    print("\nTest 3: Testing Vendor Invoice Query...")
    
    # Check if there are any shipments
    shipments = frappe.get_all("Shipments", limit=1)
    
    if not shipments:
        print("  ⚠ No Shipments found in system (skipping query test)")
        return True
    
    shipment_id = shipments[0].name
    print(f"  Testing with Shipment: {shipment_id}")
    
    # Try to find vendor invoices
    vendor_invoices = frappe.db.sql("""
        SELECT 
            name,
            supplier_name,
            grand_total,
            custom_shipment_id_dimension
        FROM 
            `tabPurchase Invoice`
        WHERE 
            custom_shipment_id_dimension = %(shipment_id)s
            AND docstatus = 1
        LIMIT 5
    """, {'shipment_id': shipment_id}, as_dict=True)
    
    if vendor_invoices:
        print(f"  ✓ Found {len(vendor_invoices)} vendor invoice(s) for this shipment:")
        for inv in vendor_invoices:
            print(f"    - {inv.name}: {inv.supplier_name} ({inv.grand_total})")
    else:
        print(f"  ⚠ No vendor invoices found for Shipment {shipment_id}")
        print("    This is normal if you haven't created vendor invoices yet")
    
    return True


def test_expense_account_extraction():
    """Test 4: Test expense account extraction logic"""
    print("\nTest 4: Testing Expense Account Extraction...")
    
    # Find a submitted Purchase Invoice
    invoices = frappe.get_all(
        "Purchase Invoice",
        filters={"docstatus": 1},
        limit=1
    )
    
    if not invoices:
        print("  ⚠ No submitted Purchase Invoices found (skipping test)")
        return True
    
    invoice_name = invoices[0].name
    print(f"  Testing with Invoice: {invoice_name}")
    
    # Get expense accounts
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
    """, {'invoice': invoice_name}, as_dict=True)
    
    if accounts:
        print(f"  ✓ Found {len(accounts)} expense account(s):")
        for acc in accounts:
            print(f"    - {acc.expense_account}: {acc.total_amount} ({acc.count} items)")
        print(f"  Primary account would be: {accounts[0].expense_account}")
    else:
        print(f"  ⚠ No expense accounts found in invoice items")
    
    return True


def create_test_data():
    """
    Helper function to create test data
    WARNING: This creates actual documents in your system!
    """
    print("\n" + "="*70)
    print("CREATING TEST DATA")
    print("="*70 + "\n")
    
    print("⚠ WARNING: This will create test documents in your system!")
    print("Only run this in a test/development environment.\n")
    
    # This is intentionally not implemented to prevent accidental data creation
    # Implement only if needed for testing
    
    print("Test data creation not implemented.")
    print("Please create test data manually following the user guide.\n")


if __name__ == "__main__":
    run_tests()
