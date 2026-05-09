# Copyright (c) 2026, ds and contributors
# For license information, please see license.txt

from datetime import datetime, timedelta
import frappe
from frappe import _
from frappe.model.document import Document


class Tenders(Document):
	def validate(self):
		"""Validate tender rules and calculate price deviations"""
		self.validate_naming_series()
		self.apply_tender_rules()
		self.calculate_price_deviations()
		self.populate_tender_status()
		self.validate_tender_dates()
		self.check_tender_rule_change_permission()
		
		if self.tender_type == "Accepted Tenders":
			self.populate_tender_price_deviation_details()

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

	def apply_tender_rules(self):
		"""Apply extra quantities and extended time rules to tender"""
		# Only apply from day one if master switch is activated
		if not getattr(self, "applying_rules", 0):
			return
			
		# Apply Extra Quantities (only to items flagged with extend_qty)
		if self.apply_extra_quantities and self.extra_qty_type and self.extra_qty_value:
			self.apply_extra_quantity_logic()

		# Apply Extended Time only to items flagged with extend_time=1
		# The tender-level header dates are NOT overwritten — only per-item dates are amended.
		if self.apply_extended_time and self.extended_start_date and self.extended_end_date:
			for row in (self.item_tender or []):
				if getattr(row, 'extend_time', 0):
					row.tender_start_date = self.extended_start_date
					row.tender_end_date = self.extended_end_date

	def apply_extra_quantity_logic(self):
		"""Apply extra quantity rules to all child tables based on tender type"""
		if not self.extra_qty_type or self.extra_qty_value is None:
			return

		if self.tender_type == "Tenders for market data":
			self._apply_extra_qty_to_items_fmd()
		elif self.tender_type in ["Awarded Tenders", "Tender Submission", "Accepted Tenders"]:
			self._apply_extra_qty_to_item_tender()
			self._apply_extra_qty_to_tender_supplier()

	def _apply_extra_qty_to_items_fmd(self):
		"""Apply extra quantities to Items FMD table"""
		for row in self.items_fmd or []:
			if not hasattr(row, 'original_quantity'):
				row.original_quantity = row.quantity or 0

			if self.extra_qty_type == "Percent":
				extra = row.original_quantity * (self.extra_qty_value / 100)
				row.quantity = row.original_quantity + extra
			elif self.extra_qty_type == "Quantity":
				row.quantity = row.original_quantity + self.extra_qty_value

	def _apply_extra_qty_to_item_tender(self):
		"""Apply extra quantities only to Item Tender rows flagged with extend_qty=1"""
		for row in self.item_tender or []:
			# Skip rows not marked for quantity extension
			if not getattr(row, 'extend_qty', 0):
				continue

			if not hasattr(row, 'original_qty') or not row.original_qty:
				row.original_qty = row.tender_qty or 0

			if self.extra_qty_type == "Percent":
				extra = (row.original_qty or 0) * (self.extra_qty_value / 100)
				row.tender_qty = (row.original_qty or 0) + extra
			elif self.extra_qty_type == "Quantity":
				row.tender_qty = (row.original_qty or 0) + self.extra_qty_value

	def _apply_extra_qty_to_tender_supplier(self):
		"""Apply extra quantities to Tender Supplier table"""
		for row in self.tender_supplier or []:
			if not hasattr(row, 'original_supply_qty'):
				row.original_supply_qty = row.supply_qty or 0

			if self.extra_qty_type == "Percent":
				extra = row.original_supply_qty * (self.extra_qty_value / 100)
				row.supply_qty = row.original_supply_qty + extra
			elif self.extra_qty_type == "Quantity":
				row.supply_qty = row.original_supply_qty + self.extra_qty_value

	def calculate_price_deviations(self):
		"""Calculate price deviations for items in the tender"""
		# Clear existing price deviations
		self.tender_price_deviation = []

		# Determine which item table to check based on tender type
		items_to_check = []
		if self.tender_type in ["Awarded Tenders", "Tender Submission", "Accepted Tenders"] and self.item_tender:
			items_to_check = self.item_tender


		# Calculate deviations for each item
		for row in items_to_check:
			item_code = row.item_code if hasattr(row, 'item_code') else None
			if not item_code:
				continue

			# Get item cost from Item doctype
			try:
				item_doc = frappe.get_doc("Item", item_code)
				item_cost = item_doc.valuation_rate or item_doc.standard_rate or 0
			except frappe.DoesNotExistError:
				item_cost = 0

			# Get tender price from the row
			tender_price = row.tender_price if hasattr(row, 'tender_price') else 0

			# Calculate deviation only if tender price is less than cost
			if tender_price and item_cost and tender_price < item_cost:
				deviation_amount = item_cost - tender_price
				deviation_percent = (deviation_amount / item_cost * 100) if item_cost > 0 else 0

				# Add to price deviation table
				self.append("tender_price_deviation", {
					"item": item_code,
					"item_name": row.item_name if hasattr(row, 'item_name') else "",
					"tender_price": tender_price,
					"item_cost": item_cost,
					"deviation_amount": deviation_amount,
					"deviation_percent": round(deviation_percent, 2),
					"deviation_status": "Pending Approval"
				})

	def populate_tender_status(self):
		"""Populate or update tender status from item tables without resetting supplied quantities"""
		# Get items from appropriate table
		items_to_track = []
		if self.tender_type == "Tenders for market data" and self.items_fmd:
			items_to_track = [(row.item, row.quantity) for row in self.items_fmd if hasattr(row, 'item') and row.item]
		elif self.tender_type in ["Awarded Tenders", "Tender Submission", "Accepted Tenders"] and self.item_tender:
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

		if self.apply_extended_time:
			if self.extended_start_date and self.extended_end_date:
				if self.extended_start_date >= self.extended_end_date:
					frappe.throw("Extended Start Date must be before Extended End Date")

	def check_tender_rule_change_permission(self):
		"""Check if tender rules can be changed (80% fulfillment rule)"""
		if self.docstatus == 1:
			# Get original document to see if rules changed
			original_doc = self.get_doc_before_save()
			if not original_doc: return

			rules_changed = (
				self.apply_extra_quantities != original_doc.apply_extra_quantities or
				self.extra_qty_type != original_doc.extra_qty_type or
				self.extra_qty_value != original_doc.extra_qty_value or
				self.apply_extended_time != original_doc.apply_extended_time or
				self.extended_end_date != original_doc.extended_end_date
			)

			if rules_changed:
				if self.tender_status:
					total_tender_qty = sum(row.tender_quantity for row in self.tender_status)
					total_supplied_qty = sum(row.supplied_quantity for row in self.tender_status)

					if total_tender_qty > 0:
						fulfillment_percent = (total_supplied_qty / total_tender_qty)
						
						if fulfillment_percent < 0.8:
							frappe.throw(_("Any change in tender rules cannot be made before selling 80% of the total quantities."))
							
						if "Tender Manager" not in frappe.get_roles(frappe.session.user):
							frappe.throw(_("Even after 80% fulfillment, only the Tender Manager has permission to change tender rules."))

	def update_tender_end_date_if_extended(self):
		"""Update tender end date after submission if extended time is applied"""
		if self.apply_extended_time and self.extended_end_date:
			self.db_update({"tender_end_date": self.extended_end_date})

	def get_deviation_summary(self):
		"""Get summary of price deviations"""
		if not self.tender_price_deviation:
			return None

		total_deviation = sum(row.deviation_amount for row in self.tender_price_deviation)
		total_items_with_deviation = len(self.tender_price_deviation)
		pending_approval = sum(1 for row in self.tender_price_deviation if row.deviation_status == "Pending Approval")
		approved_deviations = sum(1 for row in self.tender_price_deviation if row.deviation_status == "Approved")

		return {
			"total_deviation": total_deviation,
			"total_items_with_deviation": total_items_with_deviation,
			"pending_approval": pending_approval,
			"approved_deviations": approved_deviations
		}

	def get_fulfillment_status(self):
		"""Calculate overall tender fulfillment status"""
		if not self.tender_status:
			return 0

		total_tender_qty = sum(row.tender_quantity for row in self.tender_status)
		total_supplied_qty = sum(row.supplied_quantity for row in self.tender_status)

		if total_tender_qty > 0:
			return round((total_supplied_qty / total_tender_qty) * 100, 2)
		return 0

	def can_create_sales_invoice(self):
		"""Check if sales invoice can be created (all deviations must be approved)"""
		if not self.tender_price_deviation:
			return True

		for row in self.tender_price_deviation:
			if row.deviation_status != "Approved":
				return False

		return True

	def update_deviation_details(self, invoice_no, items_list):
		"""Update tender price deviation details from sales invoice"""
		self.tender_price_deviation_details = []

		for item in items_list:
			item_code = item.get("item_code")
			qty = item.get("qty")
			rate = item.get("rate")

			# Find matching tender item
			tender_price = None
			for dev_row in self.tender_price_deviation:
				if dev_row.item == item_code:
					tender_price = dev_row.tender_price
					break

			if tender_price and rate < tender_price:
				# Use valuation rate as cost if available
				item_cost = frappe.db.get_value("Item", item_code, "valuation_rate") or 0
				
				# Losses = (Cost - Rate) * Qty if rate < cost
				losses = 0
				if rate < item_cost:
					losses = (item_cost - rate) * qty

				detail_row = self.append("tender_price_deviation_details", {
					"item_name": item_code,
					"invoice_no": invoice_no,
					"tender_price": tender_price,
					"item_cost": item_cost,
					"quantity_with_loss": qty,
					"losses_value": losses,
					"approved_status": "Pending",
					"approved_by": frappe.session.user
				})

	def populate_tender_price_deviation_details(self):
		"""Fetch historical sales and cost data for Accepted Tenders"""
		if not self.item_tender:
			return

		self.tender_price_deviation_details = []
		for item in self.item_tender:
			item_code = item.item_code
			if not item_code: continue

			# 1. Get average purchase price (cost) from valuation rate
			item_cost = frappe.db.get_value("Item", item_code, "valuation_rate") or 0
			
			# 2. Get latest sales price for this item to show recent market price
			last_sale = frappe.get_all("Sales Invoice Item", 
				filters={"item_code": item_code, "docstatus": 1},
				fields=["parent", "rate"],
				order_by="creation desc",
				limit=1
			)
			
			invoice_no = last_sale[0].parent if last_sale else None
			
			# 3. Tender Price is the awarded price
			tender_price = item.tender_price or 0
			
			# 4. Calculate Losses: if tender price < cost, we are losing money
			losses = 0
			if tender_price < item_cost:
				# Using tender quantity for potential loss calculation
				losses = (item_cost - tender_price) * (item.tender_qty or 0)
			
			self.append("tender_price_deviation_details", {
				"item_name": item_code,
				"invoice_no": invoice_no,
				"tender_price": tender_price,
				"item_cost": item_cost,
				"quantity_with_loss": item.tender_qty if tender_price < item_cost else 0,
				"losses_value": losses
			})

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
	
	# Copy tender rules
	target_doc.applying_rules = source_doc.applying_rules
	target_doc.apply_extra_quantities = source_doc.apply_extra_quantities
	target_doc.extra_qty_type = source_doc.extra_qty_type
	target_doc.extra_qty_value = source_doc.extra_qty_value
	target_doc.apply_extended_time = source_doc.apply_extended_time
	target_doc.extended_start_date = source_doc.extended_start_date
	target_doc.extended_end_date = source_doc.extended_end_date
	
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
	
	# Copy offers from submission
	for row in source_doc.onco_price_offer or []:
		target_doc.append("onco_price_offer", row.as_dict())
	for row in source_doc.onco_technical_offer or []:
		target_doc.append("onco_technical_offer", row.as_dict())
	for row in source_doc.distributors_price_offer or []:
		target_doc.append("distributors_price_offer", row.as_dict())
	for row in source_doc.distributors_technical_offer or []:
		target_doc.append("distributors_technical_offer", row.as_dict())
	
	# Copy tender rules
	target_doc.applying_rules = source_doc.applying_rules
	target_doc.apply_extra_quantities = source_doc.apply_extra_quantities
	target_doc.extra_qty_type = source_doc.extra_qty_type
	target_doc.extra_qty_value = source_doc.extra_qty_value
	target_doc.apply_extended_time = source_doc.apply_extended_time
	target_doc.extended_start_date = source_doc.extended_start_date
	target_doc.extended_end_date = source_doc.extended_end_date
	
	# Copy price lists
	for row in source_doc.tender_price_list or []:
		target_doc.append("tender_price_list", {
			"distributor": row.distributor if hasattr(row, 'distributor') else "",
			"price_list": row.price_list if hasattr(row, 'price_list') else ""
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
            "Item Name": "item",
            "item name": "item",
            "Item": "item",
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
            
            if item_data.get("item"):
                doc.append("items_fmd", item_data)
                
        doc.save()
        return True
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "FMD Upload Error")
        frappe.throw(f"Error parsing file: {str(e)}")

@frappe.whitelist()
def save_item_extension_flags(tender_name, selections):
	"""
	Save per-item extend_qty / extend_time flags on an Item Tender child table.
	This method uses db_set on the child DocType directly, which is the correct
	way to update child table fields on a submitted (docstatus=1) parent document
	without requiring a cancel/amend cycle.

	Called from the client-side extension dialog on submitted Accepted Tenders
	and Tender Submissions.
	"""
	if isinstance(selections, str):
		import json
		selections = json.loads(selections)

	# Validate the parent doc exists and user has write permission
	parent = frappe.get_doc("Tenders", tender_name)
	frappe.has_permission("Tenders", "write", parent, throw=True)

	for sel in selections:
		row_name = sel.get("name")
		extend_qty = int(sel.get("extend_qty", 0))
		extend_time = int(sel.get("extend_time", 0))

		if not row_name:
			continue

		# Write directly to the child table row — safe for submitted docs
		# because Item Tender fields have allow_on_submit=1
		frappe.db.set_value(
			"Item Tender",
			row_name,
			{"extend_qty": extend_qty, "extend_time": extend_time},
			update_modified=False
		)

	# Trigger re-validation of extension rules on the parent so
	# quantities/dates are recalculated with the new per-item selections.
	# We re-load the doc fresh so it picks up the new child values.
	parent = frappe.get_doc("Tenders", tender_name)
	if parent.applying_rules:
		parent.apply_tender_rules()
		parent.save(ignore_permissions=True)

	frappe.db.commit()
	return {"status": "ok"}


@frappe.whitelist()
def check_sales_invoice_deviations(sales_invoice_name):
	"""
	Whitelisted method for client-side to check for deviations without throwing an error.
	Used to prompt the user for approval.
	"""
	doc = frappe.get_doc("Sales Invoice", sales_invoice_name)
	if not doc.get("custom_tender_ref"):
		return {"deviations": []}

	tender = frappe.get_doc("Tenders", doc.custom_tender_ref)
	
	# Build map of tender prices
	tender_prices = {}
	for row in tender.item_tender or []:
		if row.item_code:
			tender_prices[row.item_code] = row.tender_price
	
	# Detect deviations
	deviations = []
	for item in doc.items:
		if item.item_code in tender_prices:
			t_price = tender_prices[item.item_code]
			if item.rate < t_price:
				deviations.append({
					"item_code": item.item_code,
					"invoice_rate": item.rate,
					"tender_price": t_price,
					"qty": item.qty
				})
	
	return {
		"deviations": deviations,
		"already_approved": doc.get("custom_price_deviation_approved") or 0
	}


