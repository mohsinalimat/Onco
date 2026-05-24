#!/usr/bin/env python3
"""
Fix Warehouse Nestedset Structure
This script rebuilds the lft/rgt values for the Warehouse tree structure
"""

import frappe
from frappe.utils.nestedset import rebuild_tree

def fix_warehouse_nestedset():
    """Rebuild the warehouse tree structure"""
    frappe.init(site='your-site-name')  # Replace with your actual site name
    frappe.connect()
    
    print("Starting warehouse nestedset rebuild...")
    
    try:
        # Check for warehouses with NULL lft/rgt
        null_warehouses = frappe.db.sql("""
            SELECT name, warehouse_name, parent_warehouse, is_group
            FROM `tabWarehouse`
            WHERE lft IS NULL OR rgt IS NULL OR lft = 0 OR rgt = 0
        """, as_dict=True)
        
        if null_warehouses:
            print(f"\nFound {len(null_warehouses)} warehouses with NULL or zero lft/rgt values:")
            for wh in null_warehouses:
                print(f"  - {wh.name} (Parent: {wh.parent_warehouse or 'None'}, Is Group: {wh.is_group})")
        
        # Rebuild the entire Warehouse tree
        print("\nRebuilding Warehouse tree structure...")
        rebuild_tree("Warehouse", "parent_warehouse")
        
        print("\n✓ Warehouse tree structure rebuilt successfully!")
        
        # Verify the fix
        print("\nVerifying fix...")
        still_null = frappe.db.sql("""
            SELECT name
            FROM `tabWarehouse`
            WHERE lft IS NULL OR rgt IS NULL OR lft = 0 OR rgt = 0
        """)
        
        if still_null:
            print(f"⚠ Warning: {len(still_null)} warehouses still have NULL/zero values")
            print("These may need manual intervention:")
            for wh in still_null:
                print(f"  - {wh[0]}")
        else:
            print("✓ All warehouses now have valid lft/rgt values")
        
        frappe.db.commit()
        print("\n✓ Changes committed to database")
        
    except Exception as e:
        frappe.db.rollback()
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()

if __name__ == "__main__":
    fix_warehouse_nestedset()
