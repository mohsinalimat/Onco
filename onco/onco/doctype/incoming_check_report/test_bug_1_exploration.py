"""
Bug 1 Exploration Test: Purchase Receipt Report Field Mapping

This test is designed to FAIL on unfixed code to confirm Bug 1 exists.
Bug 1: Purchase Receipt Report fails to correctly map inspection check fields
from Incoming Check Report due to incorrect conditional check on non-existent
field (source.seal_numbers) and potential boolean-to-integer conversion issues.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

Expected Outcome: Test FAILS - seal_numbers_match is None or not set,
confirming Bug 1 exists.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from onco.onco.doctype.incoming_check_report.incoming_check_report import make_purchase_receipt_report


class TestBug1Exploration(FrappeTestCase):
    """
    Bug Condition Exploration Test for Bug 1
    
    This test creates an Incoming Check Report with all inspection fields checked
    and verifies that the Purchase Receipt Report has correct field mappings.
    
    On UNFIXED code, this test is EXPECTED TO FAIL because:
    - seal_numbers_match will not be set due to incorrect conditional check
    - Boolean-to-integer conversions may be inconsistent
    """
    
    def setUp(self):
        """Set up test data"""
        self.cleanup_test_data()
        
    def tearDown(self):
        """Clean up test data"""
        self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """Remove any test documents created during testing"""
        # Delete test Purchase Receipt Reports
        test_prrs = frappe.get_all(
            "Purchase Receipt Report",
            filters={"custom_shipment_ref": ["like", "TEST-SHIP-%"]},
            pluck="name"
        )
        for prr in test_prrs:
            frappe.delete_doc("Purchase Receipt Report", prr, force=True)
        
        # Delete test Incoming Check Reports
        test_icrs = frappe.get_all(
            "Incoming Check Report",
            filters={"shipment": ["like", "TEST-SHIP-%"]},
            pluck="name"
        )
        for icr in test_icrs:
            frappe.delete_doc("Incoming Check Report", icr, force=True)
        
        frappe.db.commit()
    
    def test_purchase_receipt_report_field_mapping(self):
        """
        Test Purchase Receipt Report field mapping from Incoming Check Report
        
        Creates test Incoming Check Report with all inspection fields checked:
        - seal_integrity_verified = 1
        - commercial_invoice_present = 1
        - package_condition_ok = 1
        - data_logger_present = 'Yes'
        
        Expected on UNFIXED code:
        - seal_numbers_match is None or not set (BUG - incorrect conditional)
        - invoice_present should be 1 (verify boolean-to-integer conversion)
        - package_condition should be 1 (verify boolean-to-integer conversion)
        - data_logger_present should be 1 (should work correctly)
        """
        
        # Create test Incoming Check Report
        icr = frappe.get_doc({
            "doctype": "Incoming Check Report",
            "shipment": "TEST-SHIP-001",
            "purchase_receipt": "TEST-PR-001",
            # Vehicle Inspection
            "seal_integrity_verified": 1,
            "temperature_recorder_status": "Normal",
            # Document Check
            "commercial_invoice_present": 1,
            "packing_list_present": 1,
            "bill_of_lading_present": 1,
            "certificate_of_analysis_present": 1,
            # Physical Check
            "package_condition_ok": 1,
            "labels_verified": 1,
            "quantity_verified": 1,
            # Temperature Control
            "data_logger_present": "Yes",
            "temperature_range_status": "In-Range",
            # Add at least one item (required)
            "items": [{
                "item_code": "TEST-ITEM-001",
                "item_name": "Test Item",
                "batch_no": "BATCH-001",
                "invoice_quantity": 100,
                "received_quantity": 100,
                "accepted_quantity": 100,
                "damage_quantity": 0,
                "over_quantity": 0,
                "manufacturing_date": "2026-01-01",
                "expiry_date": "2028-01-01"
            }]
        })
        icr.insert()
        icr.submit()
        
        # Call make_purchase_receipt_report on UNFIXED code
        prr = make_purchase_receipt_report(icr.name)
        prr.insert()
        
        # Document counterexamples found
        counterexamples = []
        
        # Assert seal_numbers_match = 1 (EXPECTED TO FAIL on unfixed code)
        if prr.seal_numbers_match != 1:
            counterexample = (
                f"seal_numbers_match not set correctly: "
                f"expected 1, got {prr.seal_numbers_match} "
                f"(seal_integrity_verified={icr.seal_integrity_verified})"
            )
            counterexamples.append(counterexample)
            print(f"\n❌ COUNTEREXAMPLE FOUND: {counterexample}")
        
        # Assert invoice_present = 1 (verify boolean-to-integer conversion)
        if prr.invoice_present != 1:
            counterexample = (
                f"invoice_present not set correctly: "
                f"expected 1, got {prr.invoice_present} "
                f"(commercial_invoice_present={icr.commercial_invoice_present})"
            )
            counterexamples.append(counterexample)
            print(f"\n❌ COUNTEREXAMPLE FOUND: {counterexample}")
        
        # Assert package_condition = 1 (verify boolean-to-integer conversion)
        if prr.package_condition != 1:
            counterexample = (
                f"package_condition not set correctly: "
                f"expected 1, got {prr.package_condition} "
                f"(package_condition_ok={icr.package_condition_ok})"
            )
            counterexamples.append(counterexample)
            print(f"\n❌ COUNTEREXAMPLE FOUND: {counterexample}")
        
        # Assert data_logger_present = 1 (should work correctly)
        if prr.data_logger_present != 1:
            counterexample = (
                f"data_logger_present not set correctly: "
                f"expected 1, got {prr.data_logger_present} "
                f"(data_logger_present={icr.data_logger_present})"
            )
            counterexamples.append(counterexample)
            print(f"\n❌ COUNTEREXAMPLE FOUND: {counterexample}")
        
        # Print summary
        if counterexamples:
            print(f"\n{'='*70}")
            print(f"BUG 1 CONFIRMED: Found {len(counterexamples)} counterexample(s)")
            print(f"{'='*70}")
            for i, ce in enumerate(counterexamples, 1):
                print(f"{i}. {ce}")
            print(f"{'='*70}\n")
        
        # All assertions (test should fail on unfixed code)
        self.assertEqual(
            prr.seal_numbers_match, 1,
            f"seal_numbers_match should be 1 when seal_integrity_verified=1. "
            f"Got {prr.seal_numbers_match}. This confirms Bug 1: incorrect "
            f"conditional check on non-existent source.seal_numbers field."
        )
        
        self.assertEqual(
            prr.invoice_present, 1,
            f"invoice_present should be 1 when commercial_invoice_present=1. "
            f"Got {prr.invoice_present}. This may indicate boolean-to-integer "
            f"conversion issue."
        )
        
        self.assertEqual(
            prr.package_condition, 1,
            f"package_condition should be 1 when package_condition_ok=1. "
            f"Got {prr.package_condition}. This may indicate boolean-to-integer "
            f"conversion issue."
        )
        
        self.assertEqual(
            prr.data_logger_present, 1,
            f"data_logger_present should be 1 when data_logger_present='Yes'. "
            f"Got {prr.data_logger_present}."
        )


def run_bug_1_exploration():
    """
    Standalone function to run Bug 1 exploration test
    
    Usage:
        bench --site [site-name] execute onco.onco.doctype.incoming_check_report.test_bug_1_exploration.run_bug_1_exploration
    """
    print("\n" + "="*70)
    print("BUG 1 EXPLORATION TEST: Purchase Receipt Report Field Mapping")
    print("="*70 + "\n")
    print("This test is EXPECTED TO FAIL on unfixed code.")
    print("Failure confirms Bug 1 exists.\n")
    
    test = TestBug1Exploration()
    test.setUp()
    
    try:
        test.test_purchase_receipt_report_field_mapping()
        print("\n✅ TEST PASSED: All fields mapped correctly")
        print("⚠️  WARNING: Test passed unexpectedly. Bug may not exist or")
        print("   code may already be fixed.\n")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED (EXPECTED): {str(e)}")
        print("\n✅ BUG 1 CONFIRMED: Test failure confirms bug exists.\n")
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}\n")
    finally:
        test.tearDown()
    
    print("="*70 + "\n")
