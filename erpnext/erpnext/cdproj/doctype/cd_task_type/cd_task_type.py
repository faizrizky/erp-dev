# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class CDTaskType(Document):
	def validate(self):
		self.calculate_weight_point()
	
	def calculate_weight_point(self):
		self.weight = round((7 / self.quantity),2)
		self.testing_weight = round((self.weight * 0.05),2)
