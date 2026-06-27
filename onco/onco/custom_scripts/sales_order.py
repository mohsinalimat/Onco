import re

import frappe
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder


class CustomSalesOrder(SalesOrder):
    def autoname(self):
        from frappe.model.naming import make_autoname

        order_type = self.get("custom_order_type_1")
        series_map = {
            "Private Direct Order": "SAL-ORD-PRV-DIR-.YYYY.-.#####",
            "Private Tenders Order": "SAL-ORD-PRV-TEN-.YYYY.-.#####",
            "UPA Tender Order": "SAL-ORD-UPA-TEN-.YYYY.-.#####",
            "UPA Direct Order": "SAL-ORD-UPA-DIR-.YYYY.-.#####",
            "UPA Distributor Order": "SAL-ORD-UPA-DIS-.YYYY.-.#####",
        }
        series = series_map.get(order_type) or self.naming_series
        if series:
            self.name = make_autoname(series, self)
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
