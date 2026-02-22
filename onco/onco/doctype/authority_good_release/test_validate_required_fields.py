"""
Unit tests for validate_required_fields() method in Authority Good Release
Tests Requirements 15.5, 15.6, 15.7, 16.2, 16.3
"""

import frappe
from frappe.tests.utils import FrappeTestCase


class TestValidateRequiredFields(FrappeTestCase):
	"""Test validate_required_fields() method"""

	def setUp(self):
		"""Set up test fixtures"""
		frappe.set_user("Administrator")

	def tearDown(self):
		"""Clean up after tests"""
		frappe.db.rollback()

	def test_release_type_required(self):
		"""Test that release_type is required"""
		# Create AGR without release_type
		agr = frappe.new_doc("Authority Good Release")
		agr.release_type = None
		
		# Should throw error
		with self.assertRaises(frappe.ValidationError) as context:
			agr.validate_required_fields()
		
		self.assertIn("Release Type is required", str(context.exception))

	def test_abr_registration_number_required(self):
		"""Test that registration_number is required for ABR"""
		# Create AGR with ABR release type but no registration_number
		agr = frappe.new_doc("Authority Good Release")
		agr.release_type = "Analysis Batch Registration"
		agr.registration_number = None
		agr.registration_date = frappe.utils.today()
		
		# Should throw error
		with self.assertRaises(frappe.ValidationError) as context:
			agr.validate_required_fields()
		
		self.assertIn("Registration Number is required", str(context.exception))

	def test_abr_registration_date_required(self):
		"""Test that registration_date is required for ABR"""
		# Create AGR with ABR release type but no registration_date
		agr = frappe.new_doc("Authority Good Release")
		agr.release_type = "Analysis Batch Registration"
		agr.registration_number = "REG-12345"
		agr.registration_date = None
		
		# Should throw error
		with self.assertRaises(frappe.ValidationError) as context:
			agr.validate_required_fields()
		
		self.assertIn("Registration Date is required", str(context.exception))

	def test_abr_with_all_required_fields(self):
		"""Test that ABR passes validation with all required fields"""
		# Create AGR with ABR release type and all required fields
		agr = frappe.new_doc("Authority Good Release")
		agr.release_type = "Analysis Batch Registration"
		agr.registration_number = "REG-12345"
		agr.registration_date = frappe.utils.today()
		
		# Should not throw error
		try:
			agr.validate_required_fields()
		except frappe.ValidationError:
			self.fail("validate_required_fields() raised ValidationError unexpectedly")

	def test_final_release_date_required(self):
		"""Test that final_release_date is required when final_released is Yes"""
		# Create AGR with final_released = Yes but no final_release_date
		agr = frappe.new_doc("Authority Good Release")
		agr.release_type = "Analysis Batch Inspection"
		agr.final_released = "Yes"
		agr.final_release_date = None
		agr.compliance_report_number = "COMP-12345"
		
		# Should throw error
		with self.assertRaises(frappe.ValidationError) as context:
			agr.validate_required_fields()
		
		self.assertIn("Final Release Date is required", str(context.exception))

	def test_compliance_report_number_required(self):
		"""Test that compliance_report_number is required when final_released is Yes"""
		# Create AGR with final_released = Yes but no compliance_report_number
		agr = frappe.new_doc("Authority Good Release")
		agr.release_type = "Analysis Batch Inspection"
		agr.final_released = "Yes"
		agr.final_release_date = frappe.utils.today()
		agr.compliance_report_number = None
		
		# Should throw error
		with self.assertRaises(frappe.ValidationError) as context:
			agr.validate_required_fields()
		
		self.assertIn("Compliance Report Number is required", str(context.exception))

	def test_final_released_with_all_required_fields(self):
		"""Test that final_released passes validation with all required fields"""
		# Create AGR with final_released = Yes and all required fields
		agr = frappe.new_doc("Authority Good Release")
		agr.release_type = "Analysis Batch Inspection"
		agr.final_released = "Yes"
		agr.final_release_date = frappe.utils.today()
		agr.compliance_report_number = "COMP-12345"
		
		# Should not throw error
		try:
			agr.validate_required_fields()
		except frappe.ValidationError:
			self.fail("validate_required_fields() raised ValidationError unexpectedly")

	def test_lrb_no_extra_validation(self):
		"""Test that LRB release type doesn't require extra fields"""
		# Create AGR with LRB release type
		agr = frappe.new_doc("Authority Good Release")
		agr.release_type = "Lot Release Batch"
		
		# Should not throw error
		try:
			agr.validate_required_fields()
		except frappe.ValidationError:
			self.fail("validate_required_fields() raised ValidationError unexpectedly")
