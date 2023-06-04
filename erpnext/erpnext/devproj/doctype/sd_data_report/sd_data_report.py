# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class SDDataReport(Document):
	def on_update(self):
		self.validate_task_count()

	def validate_task_count(self):
		print(len(self.task))
		self.task_taken = len(self.task)
