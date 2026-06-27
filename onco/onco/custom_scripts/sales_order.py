import re

import frappe
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder


class CustomSalesOrder(SalesOrder):
    def autoname(self):
        from frappe.model.naming import make_autoname

        if self.naming_series:
            self.name = make_autoname(self.naming_series, self)
        cpo_name = self.get("custom_customer_po")
        if not cpo_name or not self.name:
            return
        po_number = frappe.get_cached_value(
            "Customer Purchase Order", cpo_name, "customer_purchase_order_number"
        )
        if po_number:
            po_clean = re.sub(r'[^A-Za-z0-9_-]', '', str(po_number))
            self.name = f"{self.name}-{po_clean}"

    def validate_delivery_date(self):
        if self.get("custom_customer_po"):
            return
        super().validate_delivery_date()
