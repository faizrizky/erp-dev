# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe import _
from frappe.utils import (
	add_days,
	add_months,
	cint,
	date_diff,
	flt,
	get_datetime,
	get_last_day,
	getdate,
	month_diff,
	nowdate,
	today,
)
from frappe.model.document import Document

class SDAssets(Document):
	def validate(self):

		self.status = self.get_status()
		self.update_maintenance_status()

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
		if self.docstatus == 0:
			status = "Stored"
		elif self.docstatus == 1:
			status = "Borrowed"


		elif self.docstatus == 2:
			status = "Cancelled"
		return status

	def update_maintenance_status():
		assets = frappe.get_all(
			"SD Assets", filters={"maintenance_required": 1}
		)
		print(assets)
		for asset in assets:
			asset = frappe.get_doc("SD Assets", asset.name)

			asset.set_status("In Maintenance")
