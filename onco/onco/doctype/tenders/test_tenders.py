# Copyright (c) 2026, ds and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from datetime import datetime, timedelta


class TestTenders(FrappeTestCase):
	"""Test Tenders doctype functionality"""

	def setUp(self):
		"""Set up test fixtures"""
		self.tender_doc = None

	def tearDown(self):
		"""Clean up after tests"""
		if self.tender_doc and frappe.db.exists("Tenders", self.tender_doc.name):
			frappe.delete_doc("Tenders", self.tender_doc.name, force=True)

	def create_test_tender(self, tender_type="Awarded Tenders", **kwargs):
		"""Helper to create a test tender"""
		defaults = {
			"doctype": "Tenders",
			"naming_series": "TNDR-AWR-UPA-.YYYY.-.{tender_number}.",
			"tender_type": tender_type,
			"category": "UPA Tender",
			"tender_number": "TEST-001",
			"year_of_tender": "2026",
			"hospitalagent_name": self._get_or_create_customer(),
			"date": datetime.now().date(),
			"tender_start_date": datetime.now().date(),
			"tender_end_date": (datetime.now() + timedelta(days=30)).date(),
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults)

	def _get_or_create_customer(self):
		"""Get or create a test customer"""
		if not frappe.db.exists("Customer", "Test Hospital"):
			frappe.get_doc({
				"doctype": "Customer",
				"customer_name": "Test Hospital",
				"customer_type": "Individual",
				"customer_group": "Individual"
			}).insert(ignore_permissions=True)
		return "Test Hospital"

	def test_tender_creation(self):
		"""Test basic tender creation"""
		self.tender_doc = self.create_test_tender()
		self.tender_doc.insert()
		self.assertIsNotNone(self.tender_doc.name)
		self.assertEqual(self.tender_doc.tender_type, "Awarded Tenders")

	def test_tender_date_validation(self):
		"""Test that start date must be before end date"""
		same_date = datetime.now().date()
		self.tender_doc = self.create_test_tender(
			tender_start_date=same_date,
			tender_end_date=same_date
		)

		with self.assertRaises(frappe.ValidationError):
			self.tender_doc.validate()



	def _get_or_create_item(self, item_code):
		"""Get or create a test item"""
		if not frappe.db.exists("Item", item_code):
			item = frappe.get_doc({
				"doctype": "Item",
				"item_code": item_code,
				"item_name": f"Test Item {item_code}",
				"item_group": "All Item Groups",
				"stock_uom": "Nos"
			})
			item.insert(ignore_permissions=True)
			return item
		return frappe.get_doc("Item", item_code)
