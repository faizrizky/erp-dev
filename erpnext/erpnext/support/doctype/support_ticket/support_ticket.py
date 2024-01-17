# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe
from frappe import _
from frappe.core.utils import get_parent_doc
from frappe.email.inbox import link_communication_to_document
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.query_builder import Interval
from frappe.query_builder.functions import Now
from frappe.utils import date_diff, get_datetime, now_datetime, time_diff_in_seconds
from frappe.utils.user import is_website_user
from datetime import timedelta,datetime

class SupportTicket(Document):
	
	def validate(self):
		self.validate_employee()

		self.set_name()

		self.set_responded_on()

		self.set_resolved_on()
	
	def set_responded_on(self):
		if self.status == "Replied" and self.first_responded_on != "":
			self.first_responded_on = datetime.now()

		if self.status == "Open":
			self.first_responded_on = ""
			self.resolved_time = ""
			self.resolved_time = ""

	def set_resolved_on(self):
		if self.status == "Resolved":
			self.resolved_time = datetime.now()
	
		if self.status == "Closed":
			self.estimated_rectification_date = datetime.now()
			

	def set_name(self):
		self.subject = self.name
	
	def validate_employee(self):
		if self.employee == None and not frappe.session.user == "Administrator":
			frappe.throw(_("You are not registered as an Employee yet. Please contact your supervisor to complete the registration process immediately."),
				title="Permission Denied")
