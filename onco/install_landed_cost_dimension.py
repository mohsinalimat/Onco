"""
Installation script for Landed Cost Automation
Sets up Shipment ID as an accounting dimension
"""

import frappe
from frappe import _


def setup_shipment_accounting_dimension():
    """
    Create Shipment ID as an accounting dimension
    This allows the Shipment ID to be tracked in GL entries
    """
    print("\n" + "="*70)
    print("Setting up Shipment ID as Accounting Dimension")
    print("="*70 + "\n")
    
    # Check if Accounting Dimension already exists
    if frappe.db.exists("Accounting Dimension", "Shipments"):
        print("✓ Accounting Dimension 'Shipments' already exists")
        return
    
    try:
        # Create Accounting Dimension
        dimension = frappe.get_doc({
            "doctype": "Accounting Dimension",
            "document_type": "Shipments",
            "label": "Shipment ID",
            "fieldname": "custom_shipment_id_dimension",
            "disabled": 0,
            "mandatory_for_pl": 0,
            "mandatory_for_bs": 0
        })
        
        dimension.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"✓ Created Accounting Dimension: {dimension.name}")
        print(f"  - Document Type: {dimension.document_type}")
        print(f"  - Field Name: {dimension.fieldname}")
        print(f"  - Label: {dimension.label}")
        
        # The system will automatically add the dimension field to relevant doctypes
        print("\n✓ Accounting Dimension setup complete!")
        print("  The dimension will be available on:")
        print("  - Purchase Invoice")
        print("  - Journal Entry")
        print("  - Payment Entry")
        print("  - GL Entry")
        
    except Exception as e:
        print(f"✗ Error creating Accounting Dimension: {str(e)}")
        frappe.log_error(f"Accounting Dimension Setup Error: {str(e)}")
        raise


def install_custom_fields():
    """
    Install custom fields for Landed Cost automation
    """
    print("\n" + "="*70)
    print("Installing Custom Fields")
    print("="*70 + "\n")
    
    # Custom fields are defined in custom/*.json files
    # They will be automatically installed when the app is installed
    
    fields_to_check = [
        ("Purchase Invoice", "custom_shipment_id_dimension"),
        ("Landed Cost Voucher", "custom_shipment_id"),
        ("Landed Cost Voucher", "custom_auto_fetch_vendor_invoices")
    ]
    
    for doctype, fieldname in fields_to_check:
        if frappe.db.exists("Custom Field", f"{doctype}-{fieldname}"):
            print(f"✓ Custom Field exists: {doctype}.{fieldname}")
        else:
            print(f"⚠ Custom Field missing: {doctype}.{fieldname}")
            print(f"  Run: bench --site [site-name] migrate")
    
    print("\n✓ Custom fields check complete!")


def run_installation():
    """
    Main installation function
    Run this after installing the app:
    bench --site [site-name] execute onco.onco.install_landed_cost_dimension.run_installation
    """
    print("\n" + "="*70)
    print("LANDED COST AUTOMATION - INSTALLATION")
    print("="*70 + "\n")
    
    try:
        # Step 1: Install custom fields
        install_custom_fields()
        
        # Step 2: Setup accounting dimension
        setup_shipment_accounting_dimension()
        
        print("\n" + "="*70)
        print("INSTALLATION COMPLETE!")
        print("="*70)
        print("\nNext steps:")
        print("1. Reload your browser to see the new fields")
        print("2. Create a test vendor invoice with Shipment ID dimension")
        print("3. Create a Landed Cost Voucher and test auto-fetch")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Installation failed: {str(e)}")
        frappe.log_error(f"Landed Cost Installation Error: {str(e)}")
        raise


if __name__ == "__main__":
    run_installation()
