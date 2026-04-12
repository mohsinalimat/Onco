#!/usr/bin/env python3
"""
Fix corrupted warehouse nested set values
Run with: bench execute onco.fix_warehouse_nestedset.fix_warehouse_tree
"""

import frappe
from frappe.utils.nestedset import rebuild_tree

def fix_warehouse_tree():
	"""Rebuild the warehouse tree to fix lft/rgt values"""
	frappe.connect()
	
	print("Rebuilding Warehouse tree...")
	rebuild_tree("Warehouse", "parent_warehouse")
	frappe.db.commit()
	
	print("Warehouse tree rebuilt successfully")
	
	# Verify the fix
	warehouses = frappe.get_all("Warehouse", filters={"name": "Receivable store - Onco"}, fields=["name", "lft", "rgt"])
	if warehouses:
		wh = warehouses[0]
		print(f"\nVerification - {wh.name}: lft={wh.lft}, rgt={wh.rgt}")
		if wh.lft and wh.rgt:
			print("✓ Fix successful")
		else:
			print("✗ Still has NULL values")
	else:
		print("Warehouse not found")

if __name__ == "__main__":
	fix_warehouse_tree()
