app_name = "onco"
app_title = "Onco"
app_publisher = "ds"
app_description = "ds"
app_email = "ds@ds.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "onco",
# 		"logo": "/assets/onco/logo.png",
# 		"title": "Onco",
# 		"route": "/onco",
# 		"has_permission": "onco.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/onco/css/onco.css"
# app_include_js = "/assets/onco/js/onco.js"

# include js, css files in header of web template
# web_include_css = "/assets/onco/css/onco.css"
# web_include_js = "/assets/onco/js/onco.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "onco/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Purchase Invoice": "public/js/p_inv.override.js",
    "Supplier Quotation": "public/js/supplier_quotation.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Stock Entry": "public/js/stock_entry_incoming_check.js",
    "Purchase Receipt": "public/js/purchase_receipt_incoming_check.js"
}
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "onco/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "onco.utils.jinja_methods",
# 	"filters": "onco.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "onco.install.before_install"
# after_install = "onco.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "onco.uninstall.before_uninstall"
# after_uninstall = "onco.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "onco.utils.before_app_install"
# after_app_install = "onco.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "onco.utils.before_app_uninstall"
# after_app_uninstall = "onco.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "onco.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Purchase Order": "onco.onco.purchase_order.CustomPurchaseOrder",
	"Purchase Invoice": "onco.onco.purchase_invoice_naming.CustomPurchaseInvoice"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Purchase Receipt": {
		"validate": "onco.onco.doctype.shipments.shipments.on_purchase_receipt_validate",
		"on_submit": "onco.onco.doctype.shipments.shipments.on_purchase_receipt_submit"
	},
	"Stock Entry": {
		"before_save": "onco.onco.stock_entry_hooks.before_save"
	},
	"Sales Invoice": {
		"validate": "onco.onco.tender_validation.validate_sales_invoice_tender_price"
	},
	"Purchase Order": {
		"validate": "onco.onco.custom_scripts.purchase_order.validate",
		"on_submit": "onco.onco.custom_scripts.purchase_order.on_submit",
		"on_cancel": "onco.onco.custom_scripts.purchase_order.on_cancel"
	},
	"Purchase Invoice": {
		"before_insert": "onco.onco.purchase_invoice.before_insert",
		"validate": "onco.onco.purchase_invoice.validate",
		"on_submit": "onco.onco.purchase_invoice.on_submit"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"onco.tasks.send_expiry_reminders"
	]
}

# Testing
# -------

# before_tests = "onco.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "onco.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "onco.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["onco.utils.before_request"]
# after_request = ["onco.utils.after_request"]

# Job Events
# ----------
# before_job = ["onco.utils.before_job"]
# after_job = ["onco.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"onco.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

