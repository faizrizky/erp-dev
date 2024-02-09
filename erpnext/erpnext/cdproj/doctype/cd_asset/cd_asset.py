# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class CDAsset(Document):
	def autoname(self):
		if self.sarpras_type == 'General':
			self.name = f'{self.asset_name} - {self.room}'
		elif self.sarpras_type == 'Employee':
			self.name = f'{self.asset_name} - {self.employee} - {self.room}'

	def before_save(self) : 
		if self.sarpras_type == 'General':
			self.asset_name = f'{self.asset_name}'
		elif self.sarpras_type == 'Employee':
			self.asset_name = f'{self.asset_name} {self.employee}'

	def on_update(self) :
		return

	def validate(self) :
		self.employee = self.employee