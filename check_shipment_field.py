#!/usr/bin/env python3
import frappe

frappe.init(site='onco.com')
frappe.connect()

# Check if custom_shipment_ref exists in Purchase Receipt
columns = frappe.db.sql("""
    SHOW COLUMNS FROM `tabPurchase Receipt` 
    WHERE Field LIKE '%shipment%'
""", as_dict=1)

print("Shipment-related columns in Purchase Receipt:")
for col in columns:
    print(f"  - {col.Field} ({col.Type})")

# Check Custom Field records
custom_fields = frappe.db.sql("""
    SELECT name, fieldname, dt 
    FROM `tabCustom Field` 
    WHERE dt = 'Purchase Receipt' AND fieldname LIKE '%shipment%'
""", as_dict=1)

print("\nCustom Field records for Purchase Receipt:")
for cf in custom_fields:
    print(f"  - {cf.name}: {cf.fieldname}")

frappe.db.close()
