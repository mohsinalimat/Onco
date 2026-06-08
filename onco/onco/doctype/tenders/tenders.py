# Copyright (c) 2026, ds and contributors
# For license information, please see license.txt

from datetime import datetime, timedelta
import frappe
from frappe import _
from frappe.model.document import Document


class Tenders(Document):
	def validate(self):
		"""Validate tender"""
		self.validate_naming_series()
		self.populate_tender_status()
		self.validate_tender_dates()
		self.set_financial_offer_submitted_date()

	def set_financial_offer_submitted_date(self):
		"""Set submitted_date for Financial Offer rows when tender is submitted"""
		if self.docstatus == 1:  # Only for submitted tenders
			for row in self.onco_price_offer or []:
				if not row.submitted_date:
					row.submitted_date = frappe.utils.today()
	
	def before_save(self):
		"""Set submitted_date for new Financial Offer rows on submitted tenders"""
		if self.docstatus == 1:  # Only for submitted tenders
			for row in self.onco_price_offer or []:
				if not row.submitted_date:
					row.submitted_date = frappe.utils.today()

	def validate_naming_series(self):
		"""Validate that the naming series matches the tender type and category"""
		if not self.naming_series:
			frappe.throw(_("Naming Series is required"))
		
		# Check for Tenders for Market Data
		if self.tender_type == "Tenders for market data":
			if "FMD" not in self.naming_series:
				frappe.throw(_("Naming series must be TNDR-FMD-.YYYY.-.#### for Tenders for Market Data"))
		
		# Check for Awarded Tenders
		elif self.tender_type == "Awarded Tenders":
			if not self.category:
				frappe.throw(_("Category is required for Awarded Tenders"))
			if self.category == "UPA Tender" and "AWR-UPA" not in self.naming_series:
				frappe.throw(_("Naming series must be TNDR-AWR-UPA-.YYYY.-.{{tender_number}}. for Awarded UPA Tender"))
			elif self.category == "Private Tender" and "AWR-PRV" not in self.naming_series:
				frappe.throw(_("Naming series must be TNDR-AWR-PRV-.YYYY.-.{{tender_number}}. for Awarded Private Tender"))
			if "FMD" in self.naming_series:
				frappe.throw(_("Cannot use FMD naming series for Awarded Tenders."))
		
		# Check for Tender Submission
		elif self.tender_type == "Tender Submission":
			if not self.category:
				frappe.throw(_("Category is required for Tender Submission"))
			if self.category == "UPA Tender" and "SUB-UPA" not in self.naming_series:
				frappe.throw(_("Naming series must be TNDR-SUB-UPA-.YYYY.-.{{tender_number}}. for UPA Submission"))
			elif self.category == "Private Tender" and "SUB-PRV" not in self.naming_series:
				frappe.throw(_("Naming series must be TNDR-SUB-PRV-.YYYY.-.{{tender_number}}. for Private Submission"))
		
		# Check for Accepted Tenders
		elif self.tender_type == "Accepted Tenders":
			if not self.category:
				frappe.throw(_("Category is required for Accepted Tenders"))
			if self.category == "UPA Tender" and "ACP-UPA" not in self.naming_series:
				frappe.throw(_("Naming series must be TNDR-ACP-UPA-.YYYY.-.{{tender_number}}. for Accepted UPA Tender"))
			elif self.category == "Private Tender" and "ACP-PRV" not in self.naming_series:
				frappe.throw(_("Naming series must be TNDR-ACP-PRV-.YYYY.-.{{tender_number}}. for Accepted Private Tender"))

	def on_submit(self):
		"""Actions to perform on tender submission"""
		# Set initial workflow status only for base Awarded Tenders
		if self.tender_type == "Awarded Tenders" and not self.workflow_status:
			self.db_set("workflow_status", "Awarded")





	def populate_tender_status(self):
		"""Populate or update tender status from item tables without resetting supplied quantities"""
		# Only populate tender status for actual tenders, not market data
		if self.tender_type == "Tenders for market data":
			return
			
		# Get items from item_tender table only
		items_to_track = []
		if self.item_tender:
			items_to_track = [(row.item_code, row.tender_qty) for row in self.item_tender if hasattr(row, 'item_code') and row.item_code]

		if not items_to_track:
			return

		# Map existing status entries by item
		existing_status = {row.item_name: row for row in (self.tender_status or [])}
		
		seen_items = set()

		for item_code, tender_qty in items_to_track:
			if not item_code or item_code in seen_items:
				continue
			
			seen_items.add(item_code)

			if item_code in existing_status:
				# Update existing row if quantities changed
				status_row = existing_status[item_code]
				if status_row.tender_quantity != tender_qty:
					status_row.tender_quantity = tender_qty or 0
					status_row.remaining_quantity = (tender_qty or 0) - (status_row.supplied_quantity or 0)
					if tender_qty and tender_qty > 0:
						status_row.fulfillment_percent = ((status_row.supplied_quantity or 0) / tender_qty * 100)
					else:
						status_row.fulfillment_percent = 0
			else:
				# Create new status row
				self.append("tender_status", {
					"item_name": item_code,
					"tender_quantity": tender_qty or 0,
					"supplied_quantity": 0,
					"remaining_quantity": tender_qty or 0,
					"fulfillment_percent": 0
				})

	def validate_tender_dates(self):
		"""Validate that tender start date is before end date"""
		if self.tender_start_date and self.tender_end_date:
			if self.tender_start_date >= self.tender_end_date:
				frappe.throw("Tender Start Date must be before Tender End Date")



	def get_fulfillment_status(self):
		"""Calculate overall tender fulfillment status"""
		if not self.tender_status:
			return 0

		total_tender_qty = sum(row.tender_quantity for row in self.tender_status)
		total_supplied_qty = sum(row.supplied_quantity for row in self.tender_status)

		if total_tender_qty > 0:
			return round((total_supplied_qty / total_tender_qty) * 100, 2)
		return 0





	def get_tender_price_for_item(self, item_code):
		"""Helper to find the best tender price across allocations and offers"""
		for alloc in getattr(self, "tender_supplier_allocations", []):
			if alloc.item == item_code and alloc.price:
				return alloc.price
		
		for offer in getattr(self, "distributors_price_offer", []):
			if offer.item == item_code and getattr(offer, "status", "") == "Active" and offer.price:
				return offer.price
				
		for offer in getattr(self, "onco_price_offer", []):
			if offer.item == item_code and offer.price:
				return offer.price
				
		return 0

@frappe.whitelist()
def create_submission_from_awarded(source_name):
	"""Create Submission Tender from Awarded Tender"""
	source_doc = frappe.get_doc("Tenders", source_name)
	
	if source_doc.tender_type != "Awarded Tenders" or source_doc.workflow_status not in [None, "", "Awarded"]:
		frappe.throw(_("Can only create Submission Tender from Awarded Tender with Awarded status"))
	
	# Create new Submission Tender (same doctype, separate tender_type)
	target_doc = frappe.new_doc("Tenders")
	target_doc.tender_type = "Tender Submission"  # Explicit type
	target_doc.category = source_doc.category
	target_doc.tender_number = source_doc.tender_number
	target_doc.year_of_tender = source_doc.year_of_tender
	target_doc.hospitalagent_name = source_doc.hospitalagent_name
	target_doc.date = frappe.utils.today()
	target_doc.tender_start_date = source_doc.tender_start_date
	target_doc.tender_end_date = source_doc.tender_end_date
	target_doc.supplying_by = source_doc.supplying_by
	target_doc.number_of_distributors = source_doc.get("number_of_distributors")
	target_doc.source_awarded_tender = source_name
	
	# Copy items
	for row in source_doc.item_tender or []:
		target_doc.append("item_tender", {
			"item_code": row.item_code,
			"item_group": row.item_group,
			"item_name": row.item_name,
			"tender_qty": row.tender_qty,
			"tender_price": row.tender_price if hasattr(row, 'tender_price') else 0,
			"tender_start_date": row.tender_start_date,
			"tender_end_date": row.tender_end_date
		})
	
	target_doc.number_of_distributors = source_doc.get("number_of_distributors")
	
	# Set naming series for Submission
	if source_doc.category == "UPA Tender":
		target_doc.naming_series = "TNDR-SUB-UPA-.YYYY.-.{tender_number}.-"
	elif source_doc.category == "Private Tender":
		target_doc.naming_series = "TNDR-SUB-PRV-.YYYY.-.{tender_number}.-"
	
	target_doc.insert()
	
	# Mark source as having a submission created
	source_doc.db_set("workflow_status", "Submission")
	
	return target_doc.name

@frappe.whitelist()
def create_accepted_from_submission(source_name):
	"""Create Accepted Tender from a Tender Submission"""
	source_doc = frappe.get_doc("Tenders", source_name)
	
	if source_doc.tender_type != "Tender Submission":
		frappe.throw(_("Can only create Accepted Tender from a Tender Submission"))
	
	# Create new Accepted Tender (explicit type)
	target_doc = frappe.new_doc("Tenders")
	target_doc.tender_type = "Accepted Tenders"  # Explicit type
	target_doc.source_awarded_tender = source_doc.source_awarded_tender or source_name
	target_doc.category = source_doc.category
	target_doc.tender_number = source_doc.tender_number
	target_doc.year_of_tender = source_doc.year_of_tender
	target_doc.hospitalagent_name = source_doc.hospitalagent_name
	target_doc.date = frappe.utils.today()
	target_doc.tender_start_date = source_doc.tender_start_date
	target_doc.tender_end_date = source_doc.tender_end_date
	target_doc.supplying_by = source_doc.supplying_by
	target_doc.number_of_distributors = source_doc.get("number_of_distributors")
	
	# Copy items
	for row in source_doc.item_tender or []:
		target_doc.append("item_tender", {
			"item_code": row.item_code,
			"item_group": row.item_group,
			"item_name": row.item_name,
			"tender_qty": row.tender_qty,
			"tender_price": row.tender_price if hasattr(row, 'tender_price') else 0,
			"tender_start_date": row.tender_start_date,
			"tender_end_date": row.tender_end_date
		})
	
	# Copy suppliers
	for row in source_doc.tender_supplier or []:
		target_doc.append("tender_supplier", {
			"supplying_by": row.supplying_by if hasattr(row, 'supplying_by') else "",
			"supplier": row.supplier if hasattr(row, 'supplier') else "",
			"supply_qty": row.supply_qty if hasattr(row, 'supply_qty') else 0
		})
	
	# Copy supplier allocations
	for row in source_doc.tender_supplier_allocations or []:
		target_doc.append("tender_supplier_allocations", row.as_dict())
	
	# Copy offers from submission
	for row in source_doc.onco_price_offer or []:
		target_doc.append("onco_price_offer", row.as_dict())
	for row in source_doc.onco_technical_offer or []:
		target_doc.append("onco_technical_offer", row.as_dict())
	for row in source_doc.distributors_price_offer or []:
		target_doc.append("distributors_price_offer", row.as_dict())
	
	# Populate tender_price_list from tender_supplier (accepted tenders need distributor price lists)
	for row in source_doc.tender_supplier or []:
		if row.supplier:
			target_doc.append("tender_price_list", {
				"distributor": row.supplier,
				"price_list": ""
			})
	
	# Set naming series
	if source_doc.category == "UPA Tender":
		target_doc.naming_series = "TNDR-ACP-UPA-.YYYY.-.{tender_number}.-"
	elif source_doc.category == "Private Tender":
		target_doc.naming_series = "TNDR-ACP-PRV-.YYYY.-.{tender_number}.-"
	
	target_doc.insert()
	
	# Mark source submission as Accepted
	source_doc.db_set("workflow_status", "Accepted")
	
	return target_doc.name

@frappe.whitelist()
def upload_fmd_items(parent, file_url):
    """Parse CSV/Excel file and upload items to Items FMD table"""
    from frappe.utils.file_manager import get_file_path
    import pandas as pd
    
    file_path = get_file_path(file_url)
    
    try:
        if file_url.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        doc = frappe.get_doc("Tenders", parent)
        
        # Expected columns: Item Name, Quantity, Existing Supplier
        # Mapping to fieldnames: item, quantity, existing_supplier
        
        # Simple mapping heuristic
        col_map = {
            "Item Name": "item_description",
            "item name": "item_description",
            "Item": "item_description",
            "Quantity": "quantity",
            "qty": "quantity",
            "Qty": "quantity",
            "Existing Supplier": "existing_supplier",
            "Supplier": "existing_supplier"
        }
        
        for _, row in df.iterrows():
            item_data = {}
            for col, field in col_map.items():
                if col in df.columns:
                    item_data[field] = row[col]
            
            if item_data.get("item_description"):
                doc.append("items_fmd", item_data)
                
        doc.save()
        return True
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "FMD Upload Error")
        frappe.throw(f"Error parsing file: {str(e)}")

@frappe.whitelist()
def apply_mid_tender_extensions(tender_name, selections):
	"""
	Apply mid-tender extensions to selected items.
	Directly updates tender_qty and tender_end_date on Item Tender rows,
	then recalculates Tender Status accordingly.
	This is a manual operation triggered from the Mid-Tender Extension dialog.
	"""
	if isinstance(selections, str):
		import json
		selections = json.loads(selections)

	parent = frappe.get_doc("Tenders", tender_name)
	frappe.has_permission("Tenders", "write", parent, throw=True)

	updated_items = {}
	for sel in selections:
		row_name = sel.get("name")
		if not row_name:
			continue

		update_values = {}
		new_qty = sel.get("new_qty")
		new_end_date = sel.get("new_end_date")

		if new_qty is not None:
			update_values["tender_qty"] = new_qty
			update_values["extend_qty"] = 1
		if new_end_date:
			update_values["tender_end_date"] = new_end_date
			update_values["extend_time"] = 1

		if update_values:
			frappe.db.set_value(
				"Item Tender",
				row_name,
				update_values,
				update_modified=False
			)
			if new_qty is not None:
				updated_items[sel.get("item_code")] = new_qty

	# Update Tender Status rows to reflect new quantities
	if updated_items:
		for status_row in frappe.db.get_all(
			"Tender Status",
			filters={"parent": tender_name},
			fields=["name", "item_name", "supplied_quantity"]
		):
			if status_row.item_name in updated_items:
				new_qty = updated_items[status_row.item_name]
				remaining = new_qty - (status_row.supplied_quantity or 0)
				fulfillment = ((status_row.supplied_quantity or 0) / new_qty * 100) if new_qty > 0 else 0
				frappe.db.set_value(
					"Tender Status",
					status_row.name,
					{
						"tender_quantity": new_qty,
						"remaining_quantity": remaining,
						"fulfillment_percent": fulfillment
					},
					update_modified=False
				)

	frappe.db.commit()
	return {"status": "ok"}



