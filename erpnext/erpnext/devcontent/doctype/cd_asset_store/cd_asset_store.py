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
		cd_assets = frappe.db.get_value("CD Asset", self.asset_name, ["custodian", "asset_name"], as_dict=1)
		current_employee = frappe.db.get_value("Employee", self.custodian, "employee_name")
		belongs_to_employee = frappe.db.get_value("Employee", cd_assets.custodian, "employee_name")

		if cd_assets.custodian != self.custodian:
			frappe.throw(_("The asset : {0} does not belong to the custodian : {1}, it belongs to {2}").format(frappe.bold(self.asset_name),frappe.bold(current_employee),frappe.bold(belongs_to_employee)))

		else:
			frappe.db.delete("CD Asset Inventaris", { 'asset_name': cd_assets.asset_name })
			frappe.db.set_value('CD Asset', self.asset_name,{
				'custodian': None,
				'custodian_location': None,
				'room': self.store_asset_to,
				'status': 'Stored'
			})

	@frappe.whitelist()
	def custom_query(doctype, txt, searchfield, start, page_len, filters):
		# your logic
		filtered_list = frappe.db.get_list('CD Asset', filters={ 'status': ['!=', filters] })
		return filtered_list
