# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class CDAssetEmployee(Document):
	def autoname(self):
		self.name = f'{self.employee}'
	
	def validate(self):
		self.employee = self.employee
