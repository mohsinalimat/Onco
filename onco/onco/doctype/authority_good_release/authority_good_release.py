# Copyright (c) 2026, ds and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class AuthorityGoodRelease(Document):
	def autoname(self):
		"""Generate naming series based on release type with batch sequence for shortage control"""
		if not self.release_type:
			frappe.throw(_("Release Type is required for naming"))
		
		# Map release_type to prefix
		prefix_map = {
			"Lot Release Batch": "LRB",
			"Analysis Batch Inspection": "ABI",
			"Analysis Batch Registration": "ABR"
		}
		prefix = prefix_map.get(self.release_type)
		
		if not prefix:
			frappe.throw(_("Invalid Release Type: {0}").format(self.release_type))
		
		# Get current year (YYYY format)
		year = frappe.utils.nowdate()[:4]
		
		# Get AWB/SWB from linked Shipment
		awb_swb = self.get_awb_swb_number()
		
		# Get auto-incremented counter
		counter = self.get_next_counter(prefix, year)
		
		# Get batch sequence number for shortage control releases
		batch_seq = self.get_batch_sequence_number()
		
		# Generate name in format: {PREFIX}-{YYYY}-{XXXX}-{AWB/SWB}-{BATCH}
		# Example: LRB-2026-0001-AWB123-01, LRB-2026-0001-AWB123-02
		self.name = f"{prefix}-{year}-{counter:04d}-{awb_swb}-{batch_seq:02d}"
	
	def update_status(self):
		"""Update status field based on document state"""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			self.status = "Submitted"
		elif self.docstatus == 2:
			self.status = "Cancelled"

	def get_awb_swb_number(self):
		"""Get AWB or SWB number from linked Shipment"""
		# Return "0000" if shipment field is empty
		if not self.shipment_no:
			return "0000"
		
		try:
			# Fetch Shipment document
			shipment = frappe.get_doc("Shipments", self.shipment_no)
			
			# Check mode_of_shipping field
			if shipment.mode_of_shipping == "Air freight":
				# Return awb_no if Air freight
				return shipment.awb_no if shipment.awb_no else "0000"
			else:
				# Return swb_no for other modes
				return shipment.swb_no if shipment.swb_no else "0000"
		except Exception:
			# Return "0000" if Shipment not found or any error
			return "0000"

	def get_next_counter(self, prefix, year):
		"""Get auto-incremented counter for naming series"""
		# Query Authority Good Release documents with name like "{prefix}-{year}-%"
		existing = frappe.get_all(
			"Authority Good Release",
			filters={
				"name": ["like", f"{prefix}-{year}-%"]
			},
			fields=["name"],
			order_by="name desc",
			limit=1
		)
		
		if existing:
			# Extract counter from name (format: PREFIX-YYYY-XXXX-AWB-BB)
			# Counter is the third component after splitting by "-"
			parts = existing[0].name.split("-")
			if len(parts) >= 3:
				try:
					last_counter = int(parts[2])
					return last_counter + 1
				except ValueError:
					# If counter is not a valid integer, start from 1
					pass
		
		# Return 1 if no existing documents or extraction failed
		return 1
	
	def get_batch_sequence_number(self):
		"""
		Get batch sequence number for shortage control releases
		For the same Incoming Check Report, each new AGR gets an incremented batch number
		Example: First release = 01, Second release = 02, etc.
		"""
		# If no incoming_check_report, return 01 (first batch)
		if not self.incoming_check_report:
			return 1
		
		# Get all Authority Good Release documents for this incoming_check_report
		# Exclude cancelled (docstatus = 2) and exclude current document if it exists
		filters = {
			"incoming_check_report": self.incoming_check_report,
			"docstatus": ["!=", 2]  # Exclude cancelled
		}
		
		# Exclude current document if it already has a name
		if self.name:
			filters["name"] = ["!=", self.name]
		
		existing_agrs = frappe.get_all(
			"Authority Good Release",
			filters=filters,
			fields=["name"],
			order_by="creation desc"
		)
		
		# Batch sequence is count of existing AGRs + 1
		return len(existing_agrs) + 1



	def before_save(self):
		"""Called before the document is saved"""
		self.update_status()
		self.set_released_goods_warehouse()
		self.calculate_quantities()
	
	def set_released_goods_warehouse(self):
		"""Set released_goods_warehouse from Incoming Check Report if not already set"""
		if not self.released_goods_warehouse and self.incoming_check_report:
			# Set default warehouse (1 space before dash - matches database)
			self.released_goods_warehouse = "Imported Finished Phr Released Warehouse (Oncopharm) - Onco"
	
	def update_status(self):
		"""Update status field based on document state"""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			self.status = "Submitted"
		elif self.docstatus == 2:
			self.status = "Cancelled"

	
	def calculate_quantities(self):
		"""Calculate all derived quantity fields based on release type and subtype"""
		for item in self.items:
			# Set requested_qty from actual_quantity (read-only, auto-populated)
			if not item.requested_qty or item.requested_qty == 0:
				item.requested_qty = item.actual_quantity or 0
			
			# Toggle relationship between released_qty and shortage_control_qty
			# For LRB with Shortage Control: one fills, the other auto-calculates
			if self.release_type == "Lot Release Batch" and self.lrb_subtype == "With Shortage Control Quantity":
				requested = item.requested_qty or 0
				released = item.released_qty or 0
				shortage = item.shortage_control_qty or 0
				
				# If user entered released_qty, calculate shortage_control_qty
				if released > 0 and shortage == 0:
					item.shortage_control_qty = max(0, requested - released)
				# If user entered shortage_control_qty, calculate released_qty
				elif shortage > 0 and released == 0:
					item.released_qty = max(0, requested - shortage)
				# If both are entered, validate they sum to requested_qty
				elif released > 0 and shortage > 0:
					if (released + shortage) != requested:
						frappe.throw(
							_("For item {0}: Released Qty ({1}) + Shortage Control Qty ({2}) must equal Requested Qty ({3})").format(
								item.item_code, released, shortage, requested
							)
						)
				
				# Net released = released qty (what actually moves to released warehouse)
				# Shortage control qty stays in source warehouse
				# Formula: Requested = Released + Shortage Control
				# Example: 500 = 200 + 300
				# Net Released = 200 (moves to warehouse)
				item.net_released_qty = item.released_qty or 0
			else:
				# Without shortage control, net released equals released qty
				item.net_released_qty = item.released_qty or 0
				item.shortage_control_qty = 0

			# ABI - Analysis Batch Inspection
			if self.release_type == "Analysis Batch Inspection":
				# ABI Authority Release Total
				if self.abi_subtype == "Authority Release Total":
					# Fetch total_unreleased_qty from Incoming Check Report
					# (invoice_qty - sum of all previous releases)
					if self.incoming_check_report:
						item.total_unreleased_qty = self.get_total_unreleased_from_icr(item)

				# ABI Authority Release Partial with Withdrawal Sample
				elif self.abi_subtype == "Authority Release Partial with Withdrawal Sample":
					# Calculate total_unreleased_qty = invoice_qty - withdrew_sample_qty - partial_released_qty
					invoice = item.invoice_quantity or 0
					withdrew = item.withdrew_sample_qty or 0
					partial = item.partial_released_qty or 0
					item.total_unreleased_qty = invoice - withdrew - partial

				# ABI Withdrawal Sample Without Partial Release
				elif self.abi_subtype == "Withdrawal Sample Without Partial Release":
					# Calculate total_released_qty = invoice_qty - withdrew_sample_qty
					invoice = item.invoice_quantity or 0
					withdrew = item.withdrew_sample_qty or 0
					item.total_unreleased_qty = invoice - withdrew

			# Handle final_released for ABI subtypes
			if self.final_released == "Yes" and self.release_type == "Analysis Batch Inspection":
				# Add total_unreleased_qty to released_qty
				total_unreleased = item.total_unreleased_qty or 0
				item.released_qty = (item.released_qty or 0) + total_unreleased
				# Set total_unreleased_qty = 0
				item.total_unreleased_qty = 0

	def get_total_unreleased_from_icr(self, item):
		"""
		Fetch total_unreleased_qty from Incoming Check Report
		Calculates: invoice_qty - sum of all previous releases for this item
		"""
		if not self.incoming_check_report:
			return 0

		try:
			# Get the Incoming Check Report document
			icr_doc = frappe.get_doc("Incoming Check Report", self.incoming_check_report)

			# Find the matching item in ICR
			icr_item = None
			for icr_item_row in icr_doc.items:
				# Match by item_code AND bundle AND serial AND batch
				if (icr_item_row.item_code == item.item_code and
					getattr(icr_item_row, "serial_and_batch_bundle", None) == getattr(item, "serial_and_batch_bundle", None) and
					getattr(icr_item_row, "serial_no", None) == getattr(item, "serial_no", None) and
					icr_item_row.batch_no == item.batch_no):
					icr_item = icr_item_row
					break

			if not icr_item:
				return 0

			# Get invoice quantity from ICR
			invoice_qty = icr_item.invoice_quantity or 0

			# Get all Authority Good Release documents for this incoming_check_report
			# Exclude cancelled (docstatus = 2) and exclude current document
			agr_list = frappe.get_all(
				"Authority Good Release",
				filters={
					"incoming_check_report": self.incoming_check_report,
					"docstatus": ["!=", 2],  # Exclude cancelled
					"name": ["!=", self.name]  # Exclude current document
				},
				fields=["name"]
			)

			# Sum all previous releases for this item
			total_previous_releases = 0
			for agr_name in agr_list:
				agr_doc = frappe.get_doc("Authority Good Release", agr_name["name"])

				# Find matching items in the AGR document
				for agr_item in agr_doc.items:
					if (agr_item.item_code == item.item_code and 
						getattr(agr_item, "serial_and_batch_bundle", None) == getattr(item, "serial_and_batch_bundle", None) and
						getattr(agr_item, "serial_no", None) == getattr(item, "serial_no", None) and
						agr_item.batch_no == item.batch_no):
						total_previous_releases += agr_item.released_qty or 0

			# Calculate total unreleased = invoice_qty - sum of all previous releases
			total_unreleased = invoice_qty - total_previous_releases

			return max(0, total_unreleased)  # Ensure non-negative

		except Exception as e:
			frappe.log_error(f"Error calculating total unreleased from ICR: {str(e)}")
			return 0


	def validate(self):
		"""Main validation method that orchestrates all validation checks"""
		self.validate_release_type_and_subtype()
		self.validate_required_quantity_fields()
		self.validate_quantities()
		self.validate_dates()
		self.validate_attachments()
		self.validate_required_fields()
		self.validate_cumulative_quantities()
		self.calculate_net_quantities()
		self.calculate_totals()
	
	def validate_required_quantity_fields(self):
		"""Validate that either released_qty or shortage_control_qty is filled for each item"""
		for item in self.items:
			released = item.released_qty or 0
			shortage = item.shortage_control_qty or 0
			
			# For LRB with Shortage Control, at least one must be filled
			if self.release_type == "Lot Release Batch" and self.lrb_subtype == "With Shortage Control Quantity":
				if released == 0 and shortage == 0:
					frappe.throw(
						_("Row #{0}: Either Released Qty or Shortage Control Qty must be entered for item {1}").format(
							item.idx, item.item_code
						)
					)
			# For other types, released_qty is mandatory
			elif released == 0:
				frappe.throw(
					_("Row #{0}: Released Qty is required for item {1}").format(
						item.idx, item.item_code
					)
				)
	
	def validate_release_type_and_subtype(self):
			"""Validate release type and subtype requirements"""
			# Check release_type is populated
			if not self.release_type:
				frappe.throw("Release Type is required")

			# If release_type == "Lot Release Batch", verify lrb_subtype is populated
			if self.release_type == "Lot Release Batch":
				if not self.lrb_subtype:
					frappe.throw("LRB Subtype is required when Release Type is 'Lot Release Batch'")

			# If release_type == "Analysis Batch Inspection", verify abi_subtype is populated
			if self.release_type == "Analysis Batch Inspection":
				if not self.abi_subtype:
					frappe.throw("ABI Subtype is required when Release Type is 'Analysis Batch Inspection'")

	
	def validate_quantities(self):
		"""Validate all quantity fields"""
		for item in self.items:
			# Verify all quantity fields are non-negative
			quantity_fields = {
				'released_qty': item.released_qty or 0,
				'shortage_control_qty': item.shortage_control_qty or 0,
				'withdrew_sample_qty': item.withdrew_sample_qty or 0,
				'partial_released_qty': item.partial_released_qty or 0,
				'actual_quantity': item.actual_quantity or 0,
				'invoice_quantity': item.invoice_quantity or 0
			}
			
			for field_name, field_value in quantity_fields.items():
				if field_value < 0:
					frappe.throw(
						_("Quantity field '{0}' cannot be negative for item {1}. Current value: {2}").format(
							field_name, item.item_code, field_value
						)
					)
			
			# Verify released_qty <= actual_quantity
			if item.released_qty and item.actual_quantity:
				if item.released_qty > item.actual_quantity:
					frappe.throw(
						_("Released quantity ({0}) cannot exceed actual quantity ({1}) for item {2}").format(
							item.released_qty, item.actual_quantity, item.item_code
						)
					)
			
			# If lrb_subtype == "With Shortage Control Quantity": verify released_qty + shortage_control_qty <= actual_quantity
			if self.lrb_subtype == "With Shortage Control Quantity":
				released = item.released_qty or 0
				shortage = item.shortage_control_qty or 0
				actual = item.actual_quantity or 0
				
				if (released + shortage) > actual:
					frappe.throw(
						_("Released quantity ({0}) plus shortage control quantity ({1}) cannot exceed actual quantity ({2}) for item {3}").format(
							released, shortage, actual, item.item_code
						)
					)
			
			# If abi_subtype == "Authority Release Partial with Withdrawal Sample": verify withdrew_sample_qty + partial_released_qty <= invoice_qty
			if self.abi_subtype == "Authority Release Partial with Withdrawal Sample":
				withdrew = item.withdrew_sample_qty or 0
				partial = item.partial_released_qty or 0
				invoice = item.invoice_quantity or 0
				
				if (withdrew + partial) > invoice:
					frappe.throw(
						_("Withdrew sample quantity ({0}) plus partial released quantity ({1}) cannot exceed invoice quantity ({2}) for item {3}").format(
							withdrew, partial, invoice, item.item_code
						)
					)
			
			# If abi_subtype == "Withdrawal Sample Without Partial Release": verify withdrew_sample_qty <= invoice_qty
			if self.abi_subtype == "Withdrawal Sample Without Partial Release":
				withdrew = item.withdrew_sample_qty or 0
				invoice = item.invoice_quantity or 0
				
				if withdrew > invoice:
					frappe.throw(
						_("Withdrew sample quantity ({0}) cannot exceed invoice quantity ({1}) for item {2}").format(
							withdrew, invoice, item.item_code
						)
					)
	
	def validate_dates(self):
		"""Validate manufacturing and expiry dates"""
		from frappe.utils import getdate, today
		
		for item in self.items:
			# Skip validation if dates are not set
			if not item.manufacturing_date or not item.expiry_date:
				continue
			
			manufacturing_date = getdate(item.manufacturing_date)
			expiry_date = getdate(item.expiry_date)
			today_date = getdate(today())
			
			# Verify manufacturing_date < expiry_date
			if manufacturing_date >= expiry_date:
				frappe.throw(
					_("Manufacturing date ({0}) must be before expiry date ({1}) for item {2}").format(
						manufacturing_date, expiry_date, item.item_code
					)
				)
			
			# Verify expiry_date > today's date
			if expiry_date <= today_date:
				frappe.throw(
					_("Expiry date ({0}) must be in the future for item {1}. Current date: {2}").format(
						expiry_date, item.item_code, today_date
					)
				)
	
	def validate_attachments(self):
		"""Validate required attachments based on release type and subtype"""
		# If abi_subtype == "Authority Release Total": verify release_report attachment is present
		if self.abi_subtype == "Authority Release Total":
			if not self.release_report:
				frappe.throw(
					_("Release Report attachment is required when ABI Subtype is 'Authority Release Total'")
				)
		
		# If release_type == "Analysis Batch Registration": verify registration_documentation attachment is present
		if self.release_type == "Analysis Batch Registration":
			if not self.registration_documentation:
				frappe.throw(
					_("Registration Documentation attachment is required when Release Type is 'Analysis Batch Registration'")
				)
		
		# If final_released == "Yes": verify compliance_report_attachment is present
		if self.final_released == "Yes":
			if not self.compliance_report_attachment:
				frappe.throw(
					_("Compliance Report Attachment is required when Final Released is 'Yes'")
				)
	
	def validate_required_fields(self):
		"""Validate required fields based on release type and final release status"""
		# Verify release_type is populated
		if not self.release_type:
			frappe.throw("Release Type is required")
		
		# If release_type == "Analysis Batch Registration": verify registration_number and registration_date
		if self.release_type == "Analysis Batch Registration":
			if not self.registration_number:
				frappe.throw("Registration Number is required for Analysis Batch Registration")
			if not self.registration_date:
				frappe.throw("Registration Date is required for Analysis Batch Registration")
		
		# If final_released == "Yes": verify final_release_date and compliance_report_number
		if self.final_released == "Yes":
			if not self.final_release_date:
				frappe.throw("Final Release Date is required when Final Released is set to Yes")
			if not self.compliance_report_number:
				frappe.throw("Compliance Report Number is required when Final Released is set to Yes")
	
	def validate_cumulative_quantities(self):
		"""
		Validate cumulative quantities across all AGR documents
		For shortage control: ensure each release doesn't exceed the shortage control limit
		"""
		# Skip if incoming_check_report is empty
		if not self.incoming_check_report:
			return
		
		# Get all Authority Good Release documents for this incoming_check_report
		# Exclude cancelled (docstatus = 2) and exclude current document
		agr_list = frappe.get_all(
			"Authority Good Release",
			filters={
				"incoming_check_report": self.incoming_check_report,
				"docstatus": ["!=", 2],  # Exclude cancelled
				"name": ["!=", self.name]  # Exclude current document
			},
			fields=["name"]
		)
		
		# Get the Incoming Check Report document to access its items
		icr_doc = frappe.get_doc("Incoming Check Report", self.incoming_check_report)
		
		# For each item in current document
		for item in self.items:
			# Initialize cumulative quantities with current document's quantities
			cumulative_released = item.released_qty or 0
			cumulative_sample = item.withdrew_sample_qty or 0
			
			# Sum quantities from other AGR documents for this item_code and batch_no
			for agr_name in agr_list:
				agr_doc = frappe.get_doc("Authority Good Release", agr_name["name"])
				
				# Find matching items in the AGR document
				for agr_item in agr_doc.items:
					if (agr_item.item_code == item.item_code and 
						agr_item.batch_no == item.batch_no):
						cumulative_released += agr_item.released_qty or 0
						cumulative_sample += agr_item.withdrew_sample_qty or 0
			
			# Get actual_quantity from Incoming Check Report for this item
			icr_item = None
			for icr_item_row in icr_doc.items:
				if (icr_item_row.item_code == item.item_code and 
					icr_item_row.batch_no == item.batch_no):
					icr_item = icr_item_row
					break
			
			if not icr_item:
				frappe.throw(
					_("Item {0} with batch {1} not found in Incoming Check Report {2}").format(
						item.item_code, item.batch_no, self.incoming_check_report
					)
				)
			
			# Verify cumulative released_qty + sample_qty <= actual_quantity
			total_cumulative = cumulative_released + cumulative_sample
			if total_cumulative > icr_item.accepted_quantity:
				frappe.throw(
					_("Cumulative released quantity ({0}) + sample quantity ({1}) = {2} exceeds actual quantity ({3}) for item {4} (batch: {5})").format(
						cumulative_released, cumulative_sample, total_cumulative, 
						icr_item.accepted_quantity, item.item_code, item.batch_no
					)
				)
			
			# SHORTAGE CONTROL VALIDATION
			# For "With Shortage Control Quantity", validate against shortage control limit
			if self.lrb_subtype == "With Shortage Control Quantity":
				# Calculate the shortage control limit for this batch
				# Shortage control limit = actual_quantity - released_qty (from previous AGRs)
				previous_released = cumulative_released - (item.released_qty or 0)
				previous_sample = cumulative_sample - (item.withdrew_sample_qty or 0)
				
				# Remaining available = actual_quantity - (previous_released + previous_sample)
				remaining_available = icr_item.accepted_quantity - (previous_released + previous_sample)
				
				# Current release (released + sample) should not exceed remaining available
				current_release_total = (item.released_qty or 0) + (item.withdrew_sample_qty or 0)
				
				if current_release_total > remaining_available:
					frappe.throw(
						_("Current release quantity ({0}) exceeds remaining available quantity ({1}) for item {2} (batch: {3}). "
						  "Previous releases: {4}, Actual quantity: {5}").format(
							current_release_total, remaining_available, item.item_code, item.batch_no,
							previous_released + previous_sample, icr_item.accepted_quantity
						)
					)

	def calculate_totals(self):
		"""Calculate total quantities from items"""
		total_requested = 0
		total_released = 0
		total_actual = 0
		total_net_released = 0
		total_shortage_control = 0
		total_sample = 0
		
		for item in self.items:
			total_requested += getattr(item, 'requested_qty', 0) or 0
			total_released += getattr(item, 'released_qty', 0) or 0
			total_actual += getattr(item, 'actual_quantity', 0) or 0  # Changed from actual_qty to actual_quantity
			total_shortage_control += getattr(item, 'shortage_control_qty', 0) or 0
			total_sample += getattr(item, 'withdrew_sample_qty', 0) or 0
			total_net_released += getattr(item, 'net_released_qty', 0) or 0
		
		self.total_requested_qty = total_requested
		self.total_released_qty = total_released
		self.total_actual_qty = total_actual
		self.total_net_released_qty = total_net_released
		self.total_shortage_control_qty = total_shortage_control
		self.total_sample_qty = total_sample

	def on_submit(self):
		# Update status to Submitted
		self.update_status()
		# Only auto-create stock entries if the flag is enabled
		if self.create_stock_entry:
			self.create_stock_entries()
		self.update_shipment_release_status()
		self.update_incoming_check_report()
		# Send notification to selected user
		self.send_notification_to_user()
	
	def send_notification_to_user(self):
		"""
		Send notification to the selected user when Authority Good Release is submitted
		"""
		if not self.notify_user:
			return
		
		try:
			# Create notification message
			message = _("New Authority Good Release {0} has been submitted for {1}").format(
				self.name,
				self.release_type
			)
			
			# Add details to message
			details = []
			if self.incoming_check_report:
				details.append(_("Incoming Check Report: {0}").format(self.incoming_check_report))
			if self.shipment_no:
				details.append(_("Shipment: {0}").format(self.shipment_no))
			if self.batch_no:
				details.append(_("Batch: {0}").format(self.batch_no))
			if self.total_released_qty:
				details.append(_("Total Released Qty: {0}").format(self.total_released_qty))
			
			if details:
				message += "<br><br>" + "<br>".join(details)
			
			# Send notification
			frappe.share.add(
				"Authority Good Release",
				self.name,
				user=self.notify_user,
				read=1,
				write=0,
				submit=0,
				share=0,
				notify=1
			)
			
			# Create notification document
			notification = frappe.get_doc({
				"doctype": "Notification Log",
				"subject": _("New Authority Good Release: {0}").format(self.name),
				"for_user": self.notify_user,
				"type": "Alert",
				"document_type": "Authority Good Release",
				"document_name": self.name,
				"email_content": message
			})
			notification.insert(ignore_permissions=True)
			
			frappe.msgprint(
				_("Notification sent to {0}").format(self.notify_user),
				alert=True,
				indicator='green'
			)
			
		except Exception as e:
			frappe.log_error(
				message=f"Failed to send notification for AGR {self.name}: {str(e)}",
				title="Authority Good Release - Notification Failed"
			)
			# Don't throw error, just log it - notification failure shouldn't block submission
	
	@frappe.whitelist()
	def create_stock_entries_manually(self):
		"""
		Manually create stock entries after document submission
		This allows users to create stock entries on-demand instead of automatically on submit
		"""
		# Check if document is submitted
		if self.docstatus != 1:
			frappe.throw(_("Document must be submitted before creating stock entries"))
		
		# Create stock entries
		stock_entries = self.create_stock_entries()
		
		# Return success message with created stock entry names
		if stock_entries:
			entry_names = [se.name for se in stock_entries]
			frappe.msgprint(
				_("Successfully created {0} stock entries: {1}").format(
					len(stock_entries),
					", ".join(entry_names)
				),
				alert=True,
				indicator='green'
			)
			return entry_names
		else:
			frappe.msgprint(
				_("No stock entries were created. Please check the quantities and warehouse settings."),
				alert=True,
				indicator='orange'
			)
			return []
	
	def on_cancel(self):
		"""
		Called when an Authority Good Release document is cancelled
		- Update status to Cancelled
		- Remove current AGR from Incoming Check Report's authority_good_releases list
		- Recalculate Incoming Check Report's total_released_qty and remaining_unreleased_qty
		- Update Shipment release status
		"""
		# Update status to Cancelled
		self.update_status()
		# Update Incoming Check Report to recalculate quantities
		self.update_incoming_check_report_on_cancel()

		# Update Shipment release status
		self.update_shipment_status_on_cancel()

	def update_incoming_check_report_on_cancel(self):
		"""
		Update Incoming Check Report when AGR is cancelled
		- Recalculate total_released_qty (excluding cancelled AGR)
		- Recalculate remaining_unreleased_qty
		"""
		# Skip if incoming_check_report is empty
		if not self.incoming_check_report:
			return

		try:
			# Fetch Incoming Check Report document
			icr_doc = frappe.get_doc("Incoming Check Report", self.incoming_check_report)

			# Get all Authority Good Release documents for this incoming_check_report
			# Include only submitted documents (docstatus = 1), excluding cancelled (docstatus = 2)
			agr_list = frappe.get_all(
				"Authority Good Release",
				filters={
					"incoming_check_report": self.incoming_check_report,
					"docstatus": 1  # Only submitted documents
				},
				fields=["name"]
			)

			# Calculate total_released_qty across all remaining linked AGRs
			# Formula: released_qty - sample_qty (because samples are withdrawn separately)
			total_released_qty = 0

			for agr_name in agr_list:
				agr_doc = frappe.get_doc("Authority Good Release", agr_name["name"])

				# Sum (released_qty - sample_qty) from all items in this AGR
				for agr_item in agr_doc.items:
					released = agr_item.released_qty or 0
					sample = agr_item.withdrew_sample_qty or 0
					# Only count the quantity that actually goes to released warehouse
					# (released qty minus samples that are withdrawn)
					total_released_qty += (released - sample)

			# Calculate remaining_unreleased_qty
			# This is the total actual_quantity from ICR minus total_released_qty
			total_actual_quantity = 0
			for icr_item in icr_doc.items:
				total_actual_quantity += icr_item.accepted_quantity or 0

			remaining_unreleased_qty = total_actual_quantity - total_released_qty

			# Ensure remaining_unreleased_qty is not negative
			remaining_unreleased_qty = max(0, remaining_unreleased_qty)

			# Update Incoming Check Report fields
			icr_doc.total_released_qty = total_released_qty
			icr_doc.remaining_unreleased_qty = remaining_unreleased_qty

			# Save Incoming Check Report
			# Use flags to bypass validation and avoid recursion
			icr_doc.flags.ignore_validate = True
			icr_doc.flags.ignore_mandatory = True
			icr_doc.save()

			frappe.msgprint(
				_("Incoming Check Report {0} updated after cancellation: Total Released Qty = {1}, Remaining Unreleased Qty = {2}").format(
					self.incoming_check_report,
					total_released_qty,
					remaining_unreleased_qty
				),
				alert=True,
				indicator='orange'
			)

		except Exception as e:
			frappe.log_error(
				message=f"Failed to update Incoming Check Report {self.incoming_check_report} on cancellation: {str(e)}",
				title="Authority Good Release - Update ICR on Cancel Failed"
			)
			frappe.throw(
				_("Failed to update Incoming Check Report on cancellation: {0}").format(str(e))
			)

	def update_shipment_status_on_cancel(self):
		"""
		Update Shipment release status when AGR is cancelled
		- Recalculate cumulative released and unreleased quantities
		- Update release_complete status
		"""
		# Skip if shipment field is empty
		if not self.shipment_no:
			return

		try:
			# Get all Authority Good Release documents for this shipment
			# Include only submitted documents (docstatus = 1), excluding cancelled (docstatus = 2)
			agr_list = frappe.get_all(
				"Authority Good Release",
				filters={
					"shipment_no": self.shipment_no,
					"docstatus": 1  # Only submitted documents
				},
				fields=["name", "release_type", "lrb_subtype", "abi_subtype"]
			)

			# Calculate cumulative quantities
			total_released = 0
			total_unreleased = 0

			for agr_data in agr_list:
				agr_doc = frappe.get_doc("Authority Good Release", agr_data["name"])

				# Sum released quantities
				for item in agr_doc.items:
					total_released += item.released_qty or 0
					total_unreleased += item.total_unreleased_qty or 0

			# Fetch Shipment document
			shipment_doc = frappe.get_doc("Shipments", self.shipment_no)

			# Update Shipment fields
			# If there are still AGRs, use the most recent one's release type
			if agr_list:
				latest_agr = agr_list[0]
				shipment_doc.release_type = latest_agr.get("release_type", "")

				# Determine subtype display
				if latest_agr.get("release_type") == "Lot Release Batch":
					shipment_doc.release_subtype = latest_agr.get("lrb_subtype", "")
				elif latest_agr.get("release_type") == "Analysis Batch Inspection":
					shipment_doc.release_subtype = latest_agr.get("abi_subtype", "")
				else:
					shipment_doc.release_subtype = ""
			else:
				# No AGRs left, clear release tracking fields
				shipment_doc.release_type = ""
				shipment_doc.release_subtype = ""

			shipment_doc.total_released_qty = total_released
			shipment_doc.total_unreleased_qty = total_unreleased
			shipment_doc.release_complete = (total_unreleased == 0) if agr_list else 0

			# Save Shipment document
			shipment_doc.flags.ignore_validate = True
			shipment_doc.flags.ignore_mandatory = True
			shipment_doc.save()

			frappe.msgprint(
				_("Shipment {0} release status updated after cancellation").format(self.shipment_no),
				alert=True,
				indicator='orange'
			)

		except Exception as e:
			frappe.log_error(
				message=f"Failed to update Shipment {self.shipment_no} on cancellation: {str(e)}",
				title="Authority Good Release - Update Shipment on Cancel Failed"
			)
			# Don't throw error here, just log it - shipment update is not critical for cancellation
			frappe.msgprint(
				_("Warning: Failed to update Shipment release status: {0}").format(str(e)),
				alert=True,
				indicator='orange'
			)


	def calculate_net_quantities(self):
		"""Calculate net released quantities based on shortage control
		
		IMPORTANT: Net Released Qty = Released Qty (the amount going to warehouse)
		The shortage control quantity stays in the source warehouse.
		
		Formula: Requested Qty = Released Qty + Shortage Control Qty
		Example: 500 = 200 + 300
		
		Net Released Qty = Released Qty = 200 (what moves to released warehouse)
		Shortage Control Qty = 300 (what stays in source warehouse)
		"""
		for item in self.items:
			# If shortage control is enabled for this type
			if self.lrb_subtype == "With Shortage Control Quantity":
				# Net Released = Released Qty (NOT released - shortage!)
				# The shortage control qty stays in source warehouse
				# The released qty is what actually moves to released warehouse
				item.net_released_qty = item.released_qty or 0
			else:
				item.shortage_control_qty = 0
				# Without shortage control, net released equals released qty
				item.net_released_qty = item.released_qty or 0

	def get_subtype_display(self):
		"""
		Get the display value for the release subtype
		Returns the appropriate subtype based on release_type
		"""
		if self.release_type == "Lot Release Batch":
			return self.lrb_subtype or ""
		elif self.release_type == "Analysis Batch Inspection":
			return self.abi_subtype or ""
		else:
			return ""

	def update_shipment_release_status(self):
		"""
		Update Shipment document with cumulative release information from all linked AGRs
		- Skip if shipment field is empty
		- Get all Authority Good Release documents for this shipment (docstatus = 1, submitted)
		- Calculate cumulative total_released_qty (sum of released_qty across all AGRs)
		- Calculate cumulative total_unreleased_qty (sum of total_unreleased_qty across all AGRs)
		- Update shipment fields: release_type, release_subtype, total_released_qty, total_unreleased_qty
		- Set release_complete = True if total_unreleased_qty == 0, else False
		"""
		# Skip if shipment field is empty
		if not self.shipment_no:
			return
		
		try:
			# Get all Authority Good Release documents for this shipment (docstatus = 1, submitted)
			agr_list = frappe.get_all(
				"Authority Good Release",
				filters={
					"shipment_no": self.shipment_no,
					"docstatus": 1  # Only submitted documents
				},
				fields=["name"]
			)
			
			# Calculate cumulative total_released_qty (sum of released_qty across all AGRs)
			cumulative_released_qty = 0
			cumulative_unreleased_qty = 0
			
			for agr_name in agr_list:
				agr_doc = frappe.get_doc("Authority Good Release", agr_name["name"])
				
				# Sum released_qty from all items in this AGR
				for agr_item in agr_doc.items:
					cumulative_released_qty += agr_item.released_qty or 0
					
					# Sum total_unreleased_qty from all items in this AGR
					cumulative_unreleased_qty += agr_item.total_unreleased_qty or 0
			
			# Update Shipment fields using db_set to avoid validation issues
			# Use db_set instead of doc.save() to bypass read-only field restrictions
			frappe.db.set_value("Shipments", self.shipment_no, {
				"release_type": self.release_type,
				"release_subtype": self.get_subtype_display(),
				"total_released_qty": cumulative_released_qty,
				"total_unreleased_qty": cumulative_unreleased_qty,
				"release_complete": 1 if cumulative_unreleased_qty == 0 else 0
			}, update_modified=False)
			
			frappe.msgprint(
				_("Shipment {0} updated: Release Type = {1}, Total Released Qty = {2}, Total Unreleased Qty = {3}, Release Complete = {4}").format(
					self.shipment_no,
					self.release_type,
					cumulative_released_qty,
					cumulative_unreleased_qty,
					"Yes" if cumulative_unreleased_qty == 0 else "No"
				),
				alert=True,
				indicator='green'
			)
			
		except Exception as e:
			frappe.log_error(
				message=f"Failed to update Shipment {self.shipment_no}: {str(e)}",
				title="Authority Good Release - Update Shipment Failed"
			)
			frappe.throw(
				_("Failed to update Shipment: {0}").format(str(e))
			)

	def update_incoming_check_report(self):
		"""
		Update Incoming Check Report with AGR reference and calculated quantities
		- Add current AGR to authority_good_releases child table if not already present
		- Calculate and update total_released_qty (sum of released_qty across all linked AGRs)
		- Calculate and update remaining_unreleased_qty (actual_quantity - total_released_qty)
		"""
		# Skip if incoming_check_report is empty
		if not self.incoming_check_report:
			return
		
		try:
			# Fetch Incoming Check Report document
			icr_doc = frappe.get_doc("Incoming Check Report", self.incoming_check_report)
			
			# Get all Authority Good Release documents for this incoming_check_report
			# Include only submitted documents (docstatus = 1)
			agr_list = frappe.get_all(
				"Authority Good Release",
				filters={
					"incoming_check_report": self.incoming_check_report,
					"docstatus": 1  # Only submitted documents
				},
				fields=["name"]
			)
			
			# Calculate total_released_qty across all linked AGRs
			# Formula: released_qty - sample_qty (because samples are withdrawn separately)
			total_released_qty = 0
			
			for agr_name in agr_list:
				agr_doc = frappe.get_doc("Authority Good Release", agr_name["name"])
				
				# Sum (released_qty - sample_qty) from all items in this AGR
				for agr_item in agr_doc.items:
					released = agr_item.released_qty or 0
					sample = agr_item.withdrew_sample_qty or 0
					# Only count the quantity that actually goes to released warehouse
					# (released qty minus samples that are withdrawn)
					total_released_qty += (released - sample)
			
			# Calculate remaining_unreleased_qty
			# This is the total actual_quantity from ICR minus total_released_qty
			total_actual_quantity = 0
			for icr_item in icr_doc.items:
				total_actual_quantity += icr_item.accepted_quantity or 0
			
			remaining_unreleased_qty = total_actual_quantity - total_released_qty
			
			# Ensure remaining_unreleased_qty is not negative
			remaining_unreleased_qty = max(0, remaining_unreleased_qty)
			
			# Update Incoming Check Report fields
			icr_doc.total_released_qty = total_released_qty
			icr_doc.remaining_unreleased_qty = remaining_unreleased_qty
			
			# Save Incoming Check Report
			# Use flags to bypass validation and avoid recursion
			icr_doc.flags.ignore_validate = True
			icr_doc.flags.ignore_mandatory = True
			icr_doc.save()
			
			frappe.msgprint(
				_("Incoming Check Report {0} updated: Total Released Qty = {1}, Remaining Unreleased Qty = {2}").format(
					self.incoming_check_report,
					total_released_qty,
					remaining_unreleased_qty
				),
				alert=True,
				indicator='green'
			)
			
		except Exception as e:
			frappe.log_error(
				message=f"Failed to update Incoming Check Report {self.incoming_check_report}: {str(e)}",
				title="Authority Good Release - Update ICR Failed"
			)
			frappe.throw(
				_("Failed to update Incoming Check Report: {0}").format(str(e))
			)

	def create_stock_entries(self):
		"""Create all required stock entries based on release type"""
		stock_entries = []
		
		# Create sample stock entry if needed
		if self.has_sample_quantity():
			se_sample = self.create_sample_stock_entry()
			stock_entries.append(se_sample)
		
		# Create released goods stock entry if needed
		if self.has_released_quantity():
			se_released = self.create_released_stock_entry()
			stock_entries.append(se_released)
		
		# Create final release stock entry if needed
		if self.is_final_release():
			se_final = self.create_final_release_stock_entry()
			stock_entries.append(se_final)
		
		return stock_entries

	def has_sample_quantity(self):
		"""
		Check if any item has withdrew_sample_qty > 0
		Returns True if sample quantities need to be transferred
		"""
		for item in self.items:
			if (item.withdrew_sample_qty or 0) > 0:
				return True
		return False

	def has_released_quantity(self):
		"""
		Check if any item has released_qty > 0 or partial_released_qty > 0
		Returns True if released quantities need to be transferred
		"""
		for item in self.items:
			if (item.released_qty or 0) > 0 or (item.partial_released_qty or 0) > 0:
				return True
		return False

	def is_final_release(self):
		"""
		Check if final_released == "Yes"
		Returns True if this is a final release requiring transfer to sales/onco warehouse
		"""
		return self.final_released == "Yes"

	def create_sample_stock_entry(self):
		"""
		Create Stock Entry for sample quantities
		Transfers withdrew_sample_qty from source warehouse to sample warehouse
		
		Returns:
			Stock Entry document
		"""
		# Use source_warehouse field from the document
		source_warehouse = self.source_warehouse
		
		# Validate source_warehouse is set
		if not source_warehouse:
			frappe.throw(_("Source Warehouse is required to create sample stock entry"))
		
		# Create new Stock Entry document
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.from_warehouse = source_warehouse
		se.to_warehouse = self.sample_warehouse
		
		# Set reference fields
		se.custom_authority_good_release = self.name
		
		# Add items with withdrew_sample_qty > 0
		has_items = False
		for item in self.items:
			if (item.withdrew_sample_qty or 0) > 0:
				se.append("items", {
					"item_code": item.item_code,
					"qty": item.withdrew_sample_qty,
					"s_warehouse": source_warehouse,
					"t_warehouse": self.sample_warehouse,
					"batch_no": item.batch_no,
					# DO NOT copy serial_and_batch_bundle - let ERPNext create new one
					# "serial_and_batch_bundle": getattr(item, "serial_and_batch_bundle", None),
					"use_serial_batch_fields": 1,  # Enable serial/batch fields
					"manufacturing_date": item.manufacturing_date,
					"expiry_date": item.expiry_date,
					"uom": frappe.db.get_value("Item", item.item_code, "stock_uom")
				})
				has_items = True
		
		# Only insert and submit if there are items
		if not has_items:
			frappe.throw(_("No items with sample quantities found"))
		
		try:
			# Insert and submit Stock Entry
			se.insert()
			se.submit()
			
			frappe.msgprint(
				_("Stock Entry {0} created for sample quantities").format(se.name),
				alert=True,
				indicator='green'
			)
			
			return se
			
		except Exception as e:
			frappe.log_error(
				message=f"Failed to create sample Stock Entry for AGR {self.name}: {str(e)}",
				title="Authority Good Release - Sample Stock Entry Failed"
			)
			frappe.throw(
				_("Failed to create Stock Entry for sample quantities: {0}").format(str(e))
			)
	
	def get_source_warehouse(self):
		"""
		Get source warehouse from Incoming Check Report
		
		Returns:
			str: Warehouse name
		"""
		if not self.incoming_check_report:
			frappe.throw(_("Incoming Check Report is required to determine source warehouse"))
		
		try:
			# Fetch Incoming Check Report document
			icr_doc = frappe.get_doc("Incoming Check Report", self.incoming_check_report)
			
			# Get inspection_warehouse field
			if not icr_doc.inspection_warehouse:
				frappe.throw(
					_("Inspection Warehouse not set in Incoming Check Report {0}").format(
						self.incoming_check_report
					)
				)
			
			return icr_doc.inspection_warehouse
			
		except Exception as e:
			frappe.log_error(
				message=f"Failed to get source warehouse from ICR {self.incoming_check_report}: {str(e)}",
				title="Authority Good Release - Get Source Warehouse Failed"
			)
			frappe.throw(
				_("Failed to get source warehouse: {0}").format(str(e))
			)

	def create_released_stock_entry(self):
		"""
		Create Stock Entry for released quantities
		Transfers released_qty or partial_released_qty from source warehouse to released_goods_warehouse
		
		Returns:
			Stock Entry document
		"""
		# Use source_warehouse field from the document
		source_warehouse = self.source_warehouse
		
		# Validate source_warehouse is set
		if not source_warehouse:
			frappe.throw(_("Source Warehouse is required to create released stock entry"))
		
		# Validate released_goods_warehouse is set
		if not self.released_goods_warehouse:
			frappe.throw(_("Released Goods Warehouse is required to create released stock entry"))
		
		# Create new Stock Entry document
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.from_warehouse = source_warehouse
		se.to_warehouse = self.released_goods_warehouse
		
		# Set reference fields
		se.custom_authority_good_release = self.name
		
		# Add items with released_qty > 0 or partial_released_qty > 0
		has_items = False
		for item in self.items:
			# Determine quantity: use released_qty if present, otherwise use partial_released_qty
			qty = 0
			if (item.released_qty or 0) > 0:
				qty = item.released_qty
			elif (item.partial_released_qty or 0) > 0:
				qty = item.partial_released_qty
			
			if qty > 0:
				se.append("items", {
					"item_code": item.item_code,
					"qty": qty,
					"s_warehouse": source_warehouse,
					"t_warehouse": self.released_goods_warehouse,
					"batch_no": item.batch_no,
					# DO NOT copy serial_and_batch_bundle - let ERPNext create new one
					# "serial_and_batch_bundle": getattr(item, "serial_and_batch_bundle", None),
					"use_serial_batch_fields": 1,  # Enable serial/batch fields
					"manufacturing_date": item.manufacturing_date,
					"expiry_date": item.expiry_date,
					"uom": frappe.db.get_value("Item", item.item_code, "stock_uom")
				})
				has_items = True
		
		# Only insert and submit if there are items
		if not has_items:
			frappe.throw(_("No items with released quantities found"))
		
		try:
			# Insert and submit Stock Entry
			se.insert()
			se.submit()
			
			frappe.msgprint(
				_("Stock Entry {0} created for released quantities").format(se.name),
				alert=True,
				indicator='green'
			)
			
			return se
			
		except Exception as e:
			frappe.log_error(
				message=f"Failed to create released Stock Entry for AGR {self.name}: {str(e)}",
				title="Authority Good Release - Released Stock Entry Failed"
			)
			frappe.throw(
				_("Failed to create Stock Entry for released quantities: {0}").format(str(e))
			)

	def create_final_release_stock_entry(self):
		"""
		Create Stock Entry for final release quantities
		Transfers final released quantity from released_goods_warehouse to sales_warehouse or onco_warehouse
		
		Returns:
			Stock Entry document
		"""
		# Validate released_goods_warehouse is set
		if not self.released_goods_warehouse:
			frappe.throw(_("Released Goods Warehouse is required to create final release stock entry"))
		
		# Validate sales_warehouse is set
		if not self.sales_warehouse:
			frappe.throw(_("Sales Warehouse is required to create final release stock entry"))
		
		# Create new Stock Entry document
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.from_warehouse = self.released_goods_warehouse
		
		# Set reference fields
		se.custom_authority_good_release = self.name
		se.custom_final_release = 1
		
		# Add items with final released quantities
		has_items = False
		for item in self.items:
			# Determine target warehouse: check if item is oncology item
			if self.is_oncology_item(item.item_code):
				target_warehouse = self.onco_warehouse if self.onco_warehouse else self.sales_warehouse
			else:
				target_warehouse = self.sales_warehouse
			
			# Determine quantity: use the final released quantity (previously total_unreleased_qty, now added to released_qty)
			# When final_released = "Yes", the calculate_quantities() method adds total_unreleased_qty to released_qty
			# So we need to use the released_qty which now contains the final released quantity
			qty = item.released_qty or 0
			
			if qty > 0:
				se.append("items", {
					"item_code": item.item_code,
					"qty": qty,
					"s_warehouse": self.released_goods_warehouse,
					"t_warehouse": target_warehouse,
					"batch_no": item.batch_no,
					"serial_no": getattr(item, "serial_no", None),
					"serial_and_batch_bundle": getattr(item, "serial_and_batch_bundle", None),
					"use_serial_batch_fields": getattr(item, "use_serial_batch_fields", 0),
					"manufacturing_date": item.manufacturing_date,
					"expiry_date": item.expiry_date,
					"uom": frappe.db.get_value("Item", item.item_code, "stock_uom")
				})
				has_items = True
		
		# Only insert and submit if there are items
		if not has_items:
			frappe.throw(_("No items with final released quantities found"))
		
		try:
			# Insert and submit Stock Entry
			se.insert()
			se.submit()
			
			frappe.msgprint(
				_("Stock Entry {0} created for final release quantities").format(se.name),
				alert=True,
				indicator='green'
			)
			
			return se
			
		except Exception as e:
			frappe.log_error(
				message=f"Failed to create final release Stock Entry for AGR {self.name}: {str(e)}",
				title="Authority Good Release - Final Release Stock Entry Failed"
			)
			frappe.throw(
				_("Failed to create Stock Entry for final release quantities: {0}").format(str(e))
			)
	
	def is_oncology_item(self, item_code):
		"""
		Check if item is an oncology item
		Checks item's item_group to determine if it's an oncology item
		
		Args:
			item_code (str): Item code to check
		
		Returns:
			bool: True if oncology item, False otherwise
		"""
		if not item_code:
			return False
		
		try:
			# Get item document
			item_doc = frappe.get_doc("Item", item_code)
			
			# Check if item_group contains "Oncology" or "Onco" (case-insensitive)
			if item_doc.item_group:
				item_group_lower = item_doc.item_group.lower()
				if "oncology" in item_group_lower or "onco" in item_group_lower:
					return True
			
			# You can add additional checks here if needed
			# For example, check custom fields or other attributes
			
			return False
			
		except Exception as e:
			frappe.log_error(
				message=f"Failed to check if item {item_code} is oncology item: {str(e)}",
				title="Authority Good Release - Is Oncology Item Check Failed"
			)
			# Return False by default if check fails
			return False

	def create_material_transfer(self, target_warehouse, qty_field, purpose):
		"""Helper to create a Material Transfer Stock Entry"""
		source_warehouse = "Imported Finished Phr Receipt and Inspection Warehouse  - Onco"
		
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.custom_shipment_ref = self.shipment_no
		se.custom_agr_ref = self.name
		
		has_items = False
		for item in self.items:
			qty = getattr(item, qty_field, 0)
			if qty > 0 and item.release_status == "Released":
				se.append("items", {
					"item_code": item.item_code,
					"qty": qty,
					"s_warehouse": source_warehouse,
					"t_warehouse": target_warehouse,
					"batch_no": item.batch_no,
					"serial_no": getattr(item, "serial_no", None),
					"serial_and_batch_bundle": getattr(item, "serial_and_batch_bundle", None),
					"use_serial_batch_fields": getattr(item, "use_serial_batch_fields", 0),
					"uom": frappe.db.get_value("Item", item.item_code, "stock_uom")
				})
				has_items = True

		if has_items:
			se.insert()
			se.submit()
			frappe.msgprint(_("Stock Entry {0} created for {1}.").format(se.name, purpose))

	def create_sample_transfer(self):
		"""Specific transfer for samples to Sample Store"""
		source_warehouse = "Imported Finished Phr Receipt and Inspection Warehouse  - Onco"
		target_warehouse = "Imported Finished Phr Sample warehouse - Onco"
		
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.custom_shipment_ref = self.shipment_no
		
		# For samples, we usually take from the first item
		if self.items:
			item = self.items[0]
			se.append("items", {
				"item_code": item.item_code,
				"qty": self.no_of_samples,
				"s_warehouse": source_warehouse,
				"t_warehouse": target_warehouse,
				"batch_no": item.batch_no,
				"serial_no": getattr(item, "serial_no", None),
				"serial_and_batch_bundle": getattr(item, "serial_and_batch_bundle", None),
				"use_serial_batch_fields": getattr(item, "use_serial_batch_fields", 0),
				"uom": frappe.db.get_value("Item", item.item_code, "stock_uom")
			})
			se.insert()
			se.submit()
			frappe.msgprint(_("Sample Stock Entry {0} created.").format(se.name))

	@frappe.whitelist()
	def fetch_items_from_purchase_receipt_report(self):
		"""Fetch items from Purchase Receipt Report"""
		if not self.shipment_no:
			frappe.throw("Please select a Shipment first")
		
		# Find Purchase Receipt Report linked to this shipment
		purchase_receipt_reports = frappe.get_all("Purchase Receipt Report", 
			filters={"custom_shipment_ref": self.shipment_no}, 
			fields=["name"])
		
		if not purchase_receipt_reports:
			frappe.throw("No Purchase Receipt Report found for this shipment")
		
		# Clear existing items
		self.items = []
		
		# This will be enhanced in Phase 3 to actually fetch from Purchase Receipt Report
		frappe.msgprint("Item fetching from Purchase Receipt Report will be implemented in Phase 3")


@frappe.whitelist()
def fetch_items_from_purchase_receipt_report(shipment_no):
	"""Fetch items from Purchase Receipt Report for Authority Good Release"""
	# Find Purchase Receipt Report linked to this shipment
	purchase_receipt_reports = frappe.get_all("Purchase Receipt Report", 
		filters={"custom_shipment_ref": shipment_no}, 
		fields=["name"])
	
	if not purchase_receipt_reports:
		frappe.throw("No Purchase Receipt Report found for this shipment")
	
	# Get the first Purchase Receipt Report (assuming one per shipment for now)
	prr_name = purchase_receipt_reports[0].name
	prr_doc = frappe.get_doc("Purchase Receipt Report", prr_name)
	
	items = []
	# This will be enhanced in Phase 3 to fetch actual items from Purchase Receipt Report
	# For now, return empty list
	frappe.msgprint("Item fetching will be implemented in Phase 3")
	return items

@frappe.whitelist()
def create_stock_entry(authority_good_release):
	"""Create Stock Entry from Authority Good Release"""
	agr_doc = frappe.get_doc("Authority Good Release", authority_good_release)
	
	if agr_doc.stock_entry_created:
		frappe.throw("Stock Entry already created")
	
	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.stock_entry_type = "Material Transfer"
	stock_entry.from_warehouse = agr_doc.warehouse_from
	stock_entry.to_warehouse = agr_doc.warehouse_to
	stock_entry.authority_good_release = agr_doc.name
	
	# Add items to stock entry
	for item in agr_doc.items:
		if item.net_released_qty > 0:
			stock_entry.append("items", {
				"item_code": item.item_code,
				"qty": item.net_released_qty,
				"s_warehouse": agr_doc.warehouse_from,
				"t_warehouse": agr_doc.warehouse_to,
				"batch_no": item.batch_no,
				"serial_no": getattr(item, "serial_no", None),
				"serial_and_batch_bundle": getattr(item, "serial_and_batch_bundle", None),
				"use_serial_batch_fields": getattr(item, "use_serial_batch_fields", 0)
			})
		
		# Handle sample quantities
		if item.sample_qty and agr_doc.sample_warehouse:
			stock_entry.append("items", {
				"item_code": item.item_code,
				"qty": item.sample_qty,
				"s_warehouse": agr_doc.warehouse_from,
				"t_warehouse": agr_doc.sample_warehouse,
				"batch_no": item.batch_no,
				"serial_no": getattr(item, "serial_no", None),
				"serial_and_batch_bundle": getattr(item, "serial_and_batch_bundle", None),
				"use_serial_batch_fields": getattr(item, "use_serial_batch_fields", 0)
			})
	
	if stock_entry.items:
		stock_entry.insert()
		stock_entry.submit()
		
		# Update Authority Good Release
		agr_doc.stock_entry_created = stock_entry.name
		agr_doc.save()
		
		return stock_entry.name
	else:
		frappe.throw("No items to transfer")


@frappe.whitelist()
def create_subsequent_release(source_agr):
	"""
	Create a new Authority Good Release to release shortage control quantities
	from a previous AGR that had shortage control
	"""
	# Get the source AGR document
	source_doc = frappe.get_doc("Authority Good Release", source_agr)
	
	# Validate that source AGR has shortage control quantities
	if source_doc.total_shortage_control_qty <= 0:
		frappe.throw(_("No shortage control quantities available to release"))
	
	# Create new AGR document
	new_agr = frappe.new_doc("Authority Good Release")
	
	# Track the original AGR (the first one in the chain)
	# If source_doc has an original_agr, use that; otherwise, source_doc IS the original
	original_agr = source_doc.get("original_agr") or source_agr
	
	# Copy header fields from source
	new_agr.incoming_check_report = source_doc.incoming_check_report
	new_agr.original_agr = original_agr  # Store reference to first AGR in chain
	new_agr.shipment_no = source_doc.shipment_no
	new_agr.invoice_no = source_doc.invoice_no
	new_agr.date = frappe.utils.today()
	new_agr.release_type = source_doc.release_type
	new_agr.lrb_subtype = source_doc.lrb_subtype
	new_agr.abi_subtype = source_doc.abi_subtype
	new_agr.source_warehouse = source_doc.source_warehouse
	new_agr.released_goods_warehouse = source_doc.released_goods_warehouse
	new_agr.sample_warehouse = source_doc.sample_warehouse
	
	# Add a prominent note about the source AGR in remarks
	new_agr.remarks = f"Subsequent release created from {source_agr} to release shortage control quantities ({source_doc.total_shortage_control_qty} units)."
	
	# Copy items with shortage control quantities as the new requested quantities
	for source_item in source_doc.items:
		if source_item.shortage_control_qty > 0:
			new_item = new_agr.append("items", {})
			new_item.item_code = source_item.item_code
			new_item.item_name = source_item.item_name
			new_item.batch_no = source_item.batch_no
			new_item.serial_no = source_item.serial_no
			new_item.serial_and_batch_bundle = source_item.serial_and_batch_bundle
			new_item.use_serial_batch_fields = source_item.use_serial_batch_fields
			new_item.manufacturing_date = source_item.manufacturing_date
			new_item.expiry_date = source_item.expiry_date
			new_item.invoice_quantity = source_item.invoice_quantity
			new_item.over_quantity = source_item.over_quantity
			new_item.damage_quantity = source_item.damage_quantity
			
			# Keep actual_quantity the same as the original (total received quantity)
			new_item.actual_quantity = source_item.actual_quantity
			
			# The shortage control qty from previous AGR becomes the requested qty for this AGR
			new_item.requested_qty = source_item.shortage_control_qty
			
			# Auto-fill released_qty with the full shortage control amount (user can edit if needed)
			new_item.released_qty = source_item.shortage_control_qty
			
			# No more shortage control (releasing everything)
			new_item.shortage_control_qty = 0
			
			# Net released is what's being released now
			new_item.net_released_qty = source_item.shortage_control_qty
			
			# No samples
			new_item.withdrew_sample_qty = 0
	
	# Insert the new AGR (don't submit yet - let user review and edit)
	# Bypass validation during insert since user might want to adjust quantities
	new_agr.flags.ignore_validate = True
	new_agr.insert(ignore_permissions=True)
	
	# Calculate totals using the same method as validate
	new_agr.calculate_totals()
	
	# Now adjust totals to be cumulative across the chain
	# Get all previous AGRs in the chain to calculate cumulative released qty
	all_agrs_in_chain = frappe.get_all(
		"Authority Good Release",
		filters={
			"incoming_check_report": source_doc.incoming_check_report,
			"docstatus": 1,
			"name": ["!=", new_agr.name]
		},
		fields=["total_released_qty", "total_sample_qty"]
	)
	
	# Calculate cumulative released quantity
	cumulative_released = sum(agr.get("total_released_qty", 0) for agr in all_agrs_in_chain)
	cumulative_sample = sum(agr.get("total_sample_qty", 0) for agr in all_agrs_in_chain)
	
	# Update totals to show cumulative values
	# total_released_qty should be cumulative (previous releases + current release)
	new_agr.total_released_qty = cumulative_released + new_agr.total_net_released_qty
	new_agr.total_sample_qty = cumulative_sample + new_agr.total_sample_qty
	
	# Save the calculated totals
	new_agr.flags.ignore_validate = True
	new_agr.save(ignore_permissions=True)
	
	frappe.msgprint(
		_("New Authority Good Release {0} created for releasing shortage control quantities from {1}. Please fill in the Released Qty for each item.").format(
			new_agr.name, source_agr
		),
		alert=True,
		indicator='green'
	)
	
	return new_agr.name
