# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe import _


class SDAsset(Document):
	def validate(self):
		self.status = self.get_status()

	def on_submit(self):
		self.set_status()

	def on_cancel(self):
		self.set_status()

	def set_status(self, status=None):
		"""Get and update status"""
		if not status:
			status = self.get_status()
		self.db_set("status", status)

	def get_status(self):
		"""Returns status based on whether it is draft, submitted, scrapped or depreciated"""

		if self.custodian == None:
			status = "Stored"

		elif self.custodian != None:
			status = "Borrowed"

		elif self.maintenance_required == 1:
			status = "In Maintenance"

		return status

