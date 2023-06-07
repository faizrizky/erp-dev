# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class SDStoreAsset(Document):
	def before_submit(self) : 
		self.validate_employee()

	def validate(self):
		self.validate_asset()
		# self.validate_location()
		# self.validate_employee()

	def validate_asset(self):


		status = frappe.db.get_value("SD Asset", self.asset_name, ["status"])

		if status in ("Missing", "In Maintenance"):
			frappe.throw(_("{0} is {1}. {2} asset cannot be transferred").format(frappe.bold(self.asset_name),frappe.bold(status),frappe.bold(status)))

	def validate_employee(self):

		current_custodian = frappe.db.get_value("SD Asset", self.asset_name, "custodian")
		current_employee = frappe.db.get_value("Employee", self.custodian, "employee_name")
		belongs_to_employee = frappe.db.get_value("Employee", current_custodian, "employee_name")

		if current_custodian != self.custodian:
			frappe.throw(_("The asset : {0} does not belong to the custodian : {1}, it belongs to {2}").format(frappe.bold(self.asset_name),frappe.bold(current_employee),frappe.bold(belongs_to_employee)))

		else:
			frappe.db.set_value('SD Asset', self.asset_name, 'custodian', None)
			frappe.db.set_value('SD Asset', self.asset_name, 'status', 'Stored')
			frappe.db.set_value('SD Asset',self.asset_name, 'asset_location', self.asset_location)

