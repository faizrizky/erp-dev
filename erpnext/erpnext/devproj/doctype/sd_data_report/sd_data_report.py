# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import json
import frappe
from datetime import datetime


class SDDataReport(Document):
	def before_save(self):

		self.get_exp_date()

		if len(self.task) <= 0:
			self.validate_task_count()

		if self.start_date and self.end_date != None:
			self.validate_total_days(self.start_date,self.end_date)
		
			
	def validate_task_count(self):

		self.task_taken = len(self.task)
		self.start_date = None
		self.end_date = None
		self.total_days = None

	def get_exp_date(self):
		exp_start_dates = []  # Initialize as empty lists before the loop
		exp_end_dates = []  # Initialize as empty lists before the loop
		for item in self.task:
			task_name = item.task_name

			if item.is_subtask :
				task_name = "-".join(item.task_name.split('-')[:-1]).strip()

			# Get the Task document using the reference field value (task_name)
			task_doc = frappe.get_doc('Task', task_name)

			# Get the exp.start_date & exp.end_date value from the Task document
			exp_start_date = task_doc.exp_start_date
			exp_end_date = task_doc.exp_end_date

			# Append the exp_start_date and exp_end_date to the respective lists
			exp_start_dates.append(exp_start_date)
			exp_end_dates.append(exp_end_date)

		smallest_exp_start_date = min(exp_start_dates) if exp_start_dates else None
		largest_exp_end_date = max(exp_end_dates) if exp_end_dates else None

		self.start_date = smallest_exp_start_date
		self.end_date = largest_exp_end_date

	def validate_total_days(self,start_date,end_date):

		if self.total_days is None:
			self.total_days = 0
		
		self.date_start = str(start_date)
		self.end_date = str(end_date)

		self.d1 = datetime.strptime(self.date_start, "%Y-%m-%d")
		self.d2 = datetime.strptime(self.end_date, "%Y-%m-%d")

		self.daydiff = self.d2.weekday() - self.d1.weekday()

		self.total_days = ((self.d2-self.d1).days - self.daydiff) / 7 * 5 + min(self.daydiff,5) - (max(self.d2.weekday() - 4, 0) % 5) + 1

		if self.total_days < 0:
			self.total_days = 0

		# print("TOTAL DAYS : ", self.total_days)

		return self.total_days
		