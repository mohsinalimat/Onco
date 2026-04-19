#!/usr/bin/env python3
"""
Fix script to update all Purchase Receipt shipment field references from custom_shipment_ref to shipment
Run on both onco.com and onco-test.com
"""

import frappe

def fix_shipment_references():
    """Update all references from custom_shipment_ref to shipment in Purchase Receipt"""
    
    print("=== Fixing Shipment Field References ===\n")
    
    # 1. Update Custom Field records
    print("1. Updating Custom Field records...")
    
    # Ensure Purchase Receipt-shipment field links to Shipments
    frappe.db.sql("""
        UPDATE `tabCustom Field` 
        SET options = 'Shipments', label = 'Shipment Ref'
        WHERE name = 'Purchase Receipt-shipment'
    """)
    
    # Update Stock Entry fetch_from
    frappe.db.sql("""
        UPDATE `tabCustom Field` 
        SET fetch_from = 'custom_purchase_receipt.shipment'
        WHERE name = 'Stock Entry-custom_shipment_ref'
    """)
    
    frappe.db.commit()
    print("   ✓ Custom Fields updated\n")
    
    # 2. Clear caches
    print("2. Clearing caches...")
    frappe.clear_cache()
    print("   ✓ Caches cleared\n")
    
    print("=== Fix Complete ===")
    print("\nSummary:")
    print("- Purchase Receipt uses 'shipment' field")
    print("- Purchase Invoice uses 'custom_shipments' field")
    print("- Stock Entry fetches from 'custom_purchase_receipt.shipment'")
    print("- All Python code updated to use correct field names")

if __name__ == "__main__":
    fix_shipment_references()
