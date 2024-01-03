# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import random
from frappe import _
from frappe.model.document import Document

class CDAssetStore(Document):
	def autoname(self):
		asset = frappe.db.get_value("CD Asset", self.asset_name, "asset_name")
		self.name = f"{asset} - {random.randint(100, 1000)}"

	def before_submit(self):
		self.validate_employee()

	def validate_employee(self):
		current_custodian = frappe.db.get_value("CD Asset", self.asset_name, "custodian")
		current_employee = frappe.db.get_value("Employee", self.custodian, "employee_name")
		current_userid = frappe.db.get_value("Employee", current_custodian, "user_id")
		belongs_to_employee = frappe.db.get_value("Employee", current_custodian, "employee_name")
		
		# if frappe.session.user != current_userid:
		# 	frappe.throw(_("You are not permitted to return item : ( {0} ) that have been borrowed by someone else. The actual Custodian is {1}").format(frappe.bold(self.asset_name),frappe.bold(belongs_to_employee)))

		if current_custodian != self.custodian:
			frappe.throw(_("The asset : {0} does not belong to the custodian : {1}, it belongs to {2}").format(frappe.bold(self.asset_name),frappe.bold(current_employee),frappe.bold(belongs_to_employee)))

		else:
			frappe.db.set_value('CD Asset', self.asset_name, 'custodian', None)
			frappe.db.set_value('CD Asset', self.asset_name, 'custodian_location', None)
			frappe.db.set_value('CD Asset', self.asset_name, 'room', self.store_asset_to)
			frappe.db.set_value('CD Asset', self.asset_name, 'status', 'Stored')
