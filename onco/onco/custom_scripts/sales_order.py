import frappe
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder


class CustomSalesOrder(SalesOrder):
    def validate_delivery_date(self):
        if self.get("custom_customer_po"):
            return
        super().validate_delivery_date()
