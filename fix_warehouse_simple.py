"""
Simple Warehouse Nestedset Fix
Run this with: bench --site [your-site] console
Then: exec(open('apps/onco/fix_warehouse_simple.py').read())
"""

import frappe
from frappe.utils.nestedset import rebuild_tree

def fix_warehouses():
    """Fix warehouse nestedset structure"""
    
    print("\n" + "="*60)
    print("WAREHOUSE NESTEDSET FIX")
    print("="*60)
    
    # Check for problematic warehouses
    print("\n1. Checking for warehouses with NULL/zero lft/rgt values...")
    null_warehouses = frappe.db.sql("""
        SELECT name, warehouse_name, parent_warehouse, is_group, lft, rgt
        FROM `tabWarehouse`
        WHERE lft IS NULL OR rgt IS NULL OR lft = 0 OR rgt = 0
        ORDER BY name
    """, as_dict=True)
    
    if null_warehouses:
        print(f"\n   Found {len(null_warehouses)} problematic warehouses:")
        for wh in null_warehouses:
            print(f"   - {wh.name}")
            print(f"     Parent: {wh.parent_warehouse or 'None'}")
            print(f"     Is Group: {wh.is_group}")
            print(f"     lft: {wh.lft}, rgt: {wh.rgt}")
    else:
        print("   ✓ No warehouses with NULL/zero values found")
        return
    
    # Rebuild tree
    print("\n2. Rebuilding Warehouse tree structure...")
    try:
        rebuild_tree("Warehouse", "parent_warehouse")
        print("   ✓ Tree structure rebuilt")
    except Exception as e:
        print(f"   ✗ Error rebuilding tree: {str(e)}")
        return
    
    # Verify fix
    print("\n3. Verifying fix...")
    still_null = frappe.db.sql("""
        SELECT name, lft, rgt
        FROM `tabWarehouse`
        WHERE lft IS NULL OR rgt IS NULL OR lft = 0 OR rgt = 0
    """, as_dict=True)
    
    if still_null:
        print(f"   ⚠ Warning: {len(still_null)} warehouses still have issues:")
        for wh in still_null:
            print(f"   - {wh.name} (lft: {wh.lft}, rgt: {wh.rgt})")
    else:
        print("   ✓ All warehouses now have valid lft/rgt values")
    
    # Commit changes
    print("\n4. Committing changes...")
    frappe.db.commit()
    print("   ✓ Changes committed")
    
    print("\n" + "="*60)
    print("FIX COMPLETED")
    print("="*60)
    print("\nYou can now try creating a Purchase Order again.")

# Run the fix
fix_warehouses()
