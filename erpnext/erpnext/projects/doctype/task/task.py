# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import json

import frappe
from frappe import get_roles
from frappe import _, throw
from frappe.desk.form.assign_to import clear, close_all_assignments
from frappe.model.mapper import get_mapped_doc
from frappe.utils import add_days, cstr, date_diff, flt, get_link_to_form, getdate, today,now
from frappe.utils.nestedset import NestedSet
from datetime import datetime
from datetime import timedelta, date
from frappe.utils import nowdate
from frappe import db
import re
from frappe.desk.form import assign_to



class CircularReferenceError(frappe.ValidationError):
	pass


class EndDateCannotBeGreaterThanProjectEndDateError(frappe.ValidationError):
	pass


class Task(NestedSet):
	nsm_parent_field = "parent_task"

	def get_feed(self):
		return "{0}: {1}".format(_(self.status), self.subject)

	def get_customer_details(self):
		cust = frappe.db.sql("select customer_name from `tabCustomer` where name=%s", self.customer)
		if cust:
			ret = {"customer_name": cust and cust[0][0] or ""}
			return ret
		

	def before_validate(self):		
		self.validate_task_name()
		self.sub_task_data_before_saved()
	

	def validate(self):
		self.validate_completed_on()
		self.validate_on_going_sprint()
		self.validate_dates()
		self.validate_parent_expected_end_date()
		self.validate_parent_project_dates()
		self.validate_duration()
		self.validate_progress()
		self.validate_status()
		# self.validate_status_child()
		self.validate_sub_task()
		self.validate_completed_task()
		self.update_depends_on()
		self.validate_dependencies_for_template_task()
		self.validate_duration_programmer()
		self.validate_duration_qa()			
		self.handle_completed_task()
		# self.update_sub_task_status('testo mantap djiwa aw aw aw mamacita ayaya')
		self.sub_task_data_after_saved()
		
		
	
	
		
	def validate_task_name(self):
		if self.subject.count("-") > 1 : 
				frappe.throw(_("{0} is using more than one hyphen (-). The maximum allowed hyphen (-) is one.").format(frappe.bold(self.subject),title=_("Invalid Task Name")))

	def validate_working_date(self, branch):
		subject = frappe.db.get_value('Task', self.name, '_assign')
		
		if subject is not None:
				result = json.loads(subject)
				for emp in result:
					emp_name = frappe.db.get_value('User', emp, 'full_name')

					doc = frappe.get_doc('SD Data Report', {'employee_name': emp_name, 'project_name': self.project})

					start_date = doc.start_date
					end_date = doc.end_date

					if branch == "Quality Assurance":
						if start_date is None or self.exp_start_date < start_date:
							frappe.db.set_value('SD Data Report', {'employee_name': emp_name, 'project_name': self.project}, 'start_date', self.exp_start_date)

						if end_date is None or self.exp_end_date > end_date:
							frappe.db.set_value('SD Data Report', {'employee_name': emp_name, 'project_name': self.project}, 'end_date', self.completed_on)

						# Add other operations for Quality Assurance branch
					else:
						if start_date is None or self.exp_start_date < start_date:
							frappe.db.set_value('SD Data Report', {'employee_name': emp_name, 'project_name': self.project}, 'start_date', self.exp_start_date)

						if end_date is None or self.exp_end_date > end_date:
							frappe.db.set_value('SD Data Report', {'employee_name': emp_name, 'project_name': self.project}, 'end_date', self.exp_end_date)


	
		
	def handle_completed_task(self):

		status_before = frappe.db.get_value("Task", self.name, "status")

		# print(self.name);

		checker_name_list = [x for x in self.sub_task if not x.checker_name == "" and not x.checker_name == None]
		jumlah_total_elemen_checker_name = len(checker_name_list)	

		if len(self.sub_task) > 0 :

			for d in self.sub_task:

				if flt(d.weight) > 4 or flt(d.weight) < 1:
					frappe.throw(_("Please set {0} value between {1}")
							.format(frappe.bold("Sub Task Weight"), frappe.bold("1 to 4")))


				employee_name = frappe.db.get_value("Employee", d.employee_name, "employee_name")
				checker_name = frappe.db.get_value("Employee", d.checker_name, "employee_name")
				branch = frappe.db.get_value("Employee", d.employee_name, "branch")
				branch_checker = frappe.db.get_value("Employee", d.checker_name, "branch")


				# if d.completion == 1 and d.qa_completion == 1 and self.status == "Completed":
				if d.completion == 1 and self.status == "Completed":
					update_employee_weight(employee_name,self.project,d.weight,branch, self.programmer_total_day,d.subject,self.name,len(self.sub_task),self.status,self.is_group)
					
					# self.validate_working_date(branch)

					if jumlah_total_elemen_checker_name > 0:
						if flt(d.qa_weight) > 4 or flt(d.qa_weight) < 1:
							frappe.throw(_("Please set {0} value between {1}")
										.format(frappe.bold("Sub Task QA Weight"), frappe.bold("1 to 4")))

						update_employee_weight(checker_name,self.project,d.qa_weight,branch_checker, self.qa_total_day,d.subject,self.name,len(self.sub_task),self.status,self.is_group)


				if status_before == "Completed" and self.status != "Completed":
					update_employee_weight(employee_name,self.project,-d.weight,branch, int(self.programmer_total_day),d.subject,self.name,len(self.sub_task),self.status,self.is_group)

					# self.validate_working_date(branch)

					if jumlah_total_elemen_checker_name > 0:
						if flt(d.qa_weight) > 4 or flt(d.qa_weight) < 1:
							frappe.throw(_("Please set {0} value between {1}")
										.format(frappe.bold("Sub Task QA Weight"), frappe.bold("1 to 4")))

						update_employee_weight(checker_name,self.project,-d.qa_weight,branch_checker, int(self.qa_total_day),d.subject,self.name,len(self.sub_task),self.status,self.is_group)

						# self.validate_working_date(branch_checker)	

		else:

			if flt(self.task_weight) > 4 or flt(self.task_weight) < 1:
				frappe.throw(_("Please set {0} value between {1}")
					.format(frappe.bold("Task Weight"), frappe.bold("1 to 4")))

			subject = frappe.db.get_value('Task', self.name, '_assign')
			if subject is not None:
				result = json.loads(subject)
				for emp in result:
					emp_name = frappe.db.get_value('User', emp, 'full_name')
					branch = frappe.db.get_value("User", emp, "role")
					# print("INI BRANCH : ", branch)

					# print(emp_name," ",branch)

					if self.status == "Completed":

						if branch == "Quality Assurance":
							update_employee_weight(emp_name,self.project,self.task_weight,branch, self.qa_total_day,self.name,self.name,len(self.sub_task),self.status,self.is_group)

							# self.validate_working_date(branch)
						else:
							update_employee_weight(emp_name,self.project,self.task_weight,branch, self.programmer_total_day,self.name,self.name,len(self.sub_task),self.status,self.is_group)

							# self.validate_working_date(branch)


					if status_before == "Completed" and self.status != "Completed":

						if branch == "Quality Assurance":
							update_employee_weight(emp_name,self.project,-self.task_weight,branch, -int(self.qa_total_day),self.name,self.name,len(self.sub_task),self.status,self.is_group)

							# self.validate_working_date(branch)
						else:
							update_employee_weight(emp_name,self.project,-self.task_weight,branch, -int(self.programmer_total_day),self.name,self.name,len(self.sub_task),self.status,self.is_group)



	def validate_dates(self):
		if (
			self.exp_start_date
			and self.exp_end_date
			and getdate(self.exp_start_date) > getdate(self.exp_end_date)
		):
			frappe.throw(
				_("{0} can not be greater than {1}").format(
					frappe.bold("Expected Start Date"), frappe.bold("Expected End Date")
				)
			)

		if (
			self.act_start_date
			and self.act_end_date
			and getdate(self.act_start_date) > getdate(self.act_end_date)
		):
			frappe.throw(
				_("{0} can not be greater than {1}").format(
					frappe.bold("Actual Start Date"), frappe.bold("Actual End Date")
				)
			)

		if getdate(self.qa_open_date) > getdate(self.qa_testing_date):
			frappe.throw(_("{0} cannot be greater than {1} or {1} cannot be less than {0} ").format(frappe.bold("QA Open Date"),frappe.bold("QA Testing Date")), title=("QA Date Invalid"))

			
	def validate_parent_expected_end_date(self):
		if self.parent_task:
			parent_exp_end_date = frappe.db.get_value("Task", self.parent_task, "exp_end_date")
			if parent_exp_end_date and getdate(self.get("exp_end_date")) > getdate(parent_exp_end_date):
				frappe.throw(
					_(
						"Expected End Date should be less than or equal to parent task's Expected End Date {0}."
					).format(getdate(parent_exp_end_date))
				)

	def validate_parent_project_dates(self):
		if not self.project or frappe.flags.in_test:
			return

		expected_end_date = frappe.db.get_value("Project", self.project, "expected_end_date")

		if expected_end_date:
			validate_project_dates(
				getdate(expected_end_date), self, "exp_start_date", "exp_end_date", "Expected"
			)
			validate_project_dates(
				getdate(expected_end_date), self, "act_start_date", "act_end_date", "Actual"
			)

	def validate_sub_task(self):

		if self.is_group == 1 and len(self.sub_task) > 0 :
			frappe.throw(_("{0} cannot have {1}")
							.format(frappe.bold("Parent Task"), frappe.bold("Sub Task")))
		arr = []
		arr_qa = []
		check_val = dict([])
		has_error = []
		# has_hypen= []

		if len(self.sub_task) > 0:
			for d in self.sub_task:
				# check if the same pa aji
				key = (d.sub_task, d.employee_name)
				if key not in check_val :
					check_val[key] = 1
				else:
					check_val[key] += 1
				
				# if d.sub_task.count("-") > 0:
				# 	has_hypen.append(d.sub_task)
     
				if d.completion == True:
					print(frappe.db.get_value('SD Sub Task', d.sub_task, 'status'))
					if frappe.db.get_value('SD Sub Task', d.sub_task, 'status') == "Working":
						frappe.db.set_value('SD Sub Task', d.sub_task, 'status', 'Completed')
				
				if d.completion == False:
					if frappe.db.get_value('SD Sub Task', d.sub_task, 'status') == "Completed":
						frappe.db.set_value('SD Sub Task', d.sub_task, 'status', 'Working')
					

				if check_val[key] <= 1:

					jumlah_total_elemen = len(self.sub_task)

					programmer_condition = sum(1 for x in self.sub_task if d.completion == True)
					
					sub_task_percentage_programmer = (programmer_condition / jumlah_total_elemen) * 100

					qa_condition = sum(1 for x in self.sub_task if d.qa_completion == True)
					sub_task_percentage_qa = (qa_condition / jumlah_total_elemen) * 100

					if sub_task_percentage_programmer == 100:
						arr.append(sub_task_percentage_programmer)

					if sub_task_percentage_qa == 100:
						arr_qa.append(sub_task_percentage_qa)

					# print(sub_task_percentage)
					count_true_programmer = len(arr)
					count_true_qa = len(arr_qa)
				else:
					has_error.append(d.sub_task)

			if len(has_error) > 0 : 
				frappe.throw(_("Name in the {0} cannot be same").format(frappe.bold("Sub Task Table")),title=_("Invalid Sub Task Name"))
			
			percentage_programmer = (count_true_programmer / len(self.sub_task)) * 100
			percentage_qa = (count_true_qa / len(self.sub_task)) * 100
   


			self.individual_progress = percentage_programmer
			self.qa_progress = percentage_qa


	def validate_status_child(self):
		if self.status != self.get_db_value("status") and self.status == "Open":
			for d in self.depends_on:
				task_subject = frappe.db.get_value('Task', d.task, ['subject'])
				frappe.db.set_value('Task', task_subject, 'status', 'Open')


	def validate_on_going_sprint(self):
		if self.ongoing_sprint != "" and self.ongoing_sprint != None:
			if all(self.ongoing_sprint not in item.sprint_id for item in self.multi_sprint):
				self.append('multi_sprint', {'sprint_id': self.ongoing_sprint})

		arr = [] 
		if len(self.multi_sprint) > 0:
			for items in self.multi_sprint:
				doc = frappe.get_doc('Event', items.sprint_id)

				arr.append(doc.starts_on)
				arr.append(doc.ends_on)

			self.exp_start_date =min(arr)
			self.exp_end_date = max(arr)
		else:
			self.exp_start_date = None
			self.exp_end_date = None
			self.duration = None

	def validate_status(self):
		if self.is_template and self.status != "Template":
			self.status = "Template"
		if self.status != self.get_db_value("status") and self.status == "Completed":
			for d in self.depends_on:
				if frappe.db.get_value("Task", d.task, "status") not in ("Completed", "Cancelled", ""):
					frappe.throw(
						_(
							"Cannot complete task {0} as its dependant task {1} are not completed / cancelled."
						).format(frappe.bold(self.name), frappe.bold(d.task))
					)

			close_all_assignments(self.doctype, self.name)

	def validate_completed_task(self):
		if self.status == "Completed":
			self.completed_by = frappe.session.user

			if self.completed_on == None:
				self.completed_on = getdate(today())
		else:
			self.completed_on = None

	def calculate_daydiff(self, start_date, end_date, total_day):
		total_day_diff = 0
		self.start = datetime.strptime(str(start_date), "%Y-%m-%d")
		self.end = datetime.strptime(str(end_date), "%Y-%m-%d")
		self.daydiff = self.end.weekday() - self.start.weekday()

		total_day_diff = ((self.end - self.start).days - self.daydiff) / 7 * 5 + min(self.daydiff, 5) - (max(self.end.weekday() - 4, 0) % 5) + 1

		if total_day_diff < 0:
				total_day = 0
		else:
			total_day = total_day_diff

		return total_day


	def validate_duration_qa(self):
		qa_testing = 0
		qa_integration_testing = 0

		if self.qa_total_day is None:
			self.qa_total_day = 0

		if self.qa_open_date != None and self.qa_testing_date != None:
			qa_testing = self.calculate_daydiff(self.qa_open_date, self.qa_testing_date, self.qa_total_day)

		if self.end_date_integration != None and self.completed_on != None:	
			qa_integration_testing = self.calculate_daydiff(self.end_date_integration, self.completed_on, self.qa_total_day)
		
		self.qa_total_day = qa_testing + qa_integration_testing
			
		return self.qa_total_day


	def validate_duration_programmer(self):

		working_total_days = 0
		integration_total_days = 0

		if self.programmer_total_day is None:
			self.programmer_total_day = 0
		
		if self.status == "Pending Review" or self.status == "Completed":
			if self.review_date is None:
				frappe.throw(_("{0} Cannot be empty").format(frappe.bold(self.name + " : Review Date"),title=_("Review Date is Empty")))
		
		if self.exp_start_date != None and self.review_date != None:
			working_total_days = self.calculate_daydiff(self.exp_start_date,self.review_date,self.programmer_total_day)

		if self.start_date_integration != None and self.end_date_integration != None:
			integration_total_days = self.calculate_daydiff(self.start_date_integration, self.end_date_integration, self.programmer_total_day)

		self.programmer_total_day = working_total_days + integration_total_days
	

	def validate_duration(self):
		if self.ongoing_sprint != "" and self.ongoing_sprint != None:

			if flt(self.exp_start_date == None):
				frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Expected Start Date")))

			self.start_date = str(self.exp_start_date)
			self.end_date = str(self.exp_end_date)

			self.d1 = datetime.strptime(self.start_date, "%Y-%m-%d")

			if flt(self.exp_end_date == None):
				frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Expected End Date")))
			else:
				self.d2 = datetime.strptime(self.end_date, "%Y-%m-%d")

			self.d2 = datetime.strptime(self.end_date, "%Y-%m-%d")
			self.daydiff = self.d2.weekday() - self.d1.weekday()

			self.duration = ((self.d2-self.d1).days - self.daydiff) / 7 * 5 + min(self.daydiff,5) - (max(self.d2.weekday() - 4, 0) % 5) + 1

	def validate_progress(self):

		checker_name_list = [x for x in self.sub_task if x.checker_name != "" and x.checker_name != None]
		
		jumlah_total_elemen_checker_name = len(checker_name_list)	

		if flt(self.progress or 0) > 100:
			frappe.throw(_("Progress % for a task cannot be more than 100."))

		if flt(self.individual_progress or 0) > 100 or flt(self.individual_progress) < 0:
			
			frappe.throw(_("Your Individual Progress is {0}. Individual Progress {1} for a task cannot be more than "+ "'{2}' or less than "+ "'{3}'")
				.format(frappe.bold(f'{self.individual_progress} %'),frappe.bold("%"),frappe.bold("100%"),frappe.bold("0%")))

		if flt(self.qa_progress or 0) > 100 or flt(self.qa_progress) < 0:
			
			frappe.throw(_("Your QA Task Progress is {0}. QA Task Progress {1} for a task cannot be more than "+ "'{2}' or less than "+ "'{3}'")
				.format(frappe.bold(f'{self.qa_progress} %'),frappe.bold("%"),frappe.bold("100%"),frappe.bold("0%")))

		if self.status == "Open":

			self.duration = 0

			self.qa_total_day = 0

			self.programmer_total_day = 0

			# self.validate_duration()

		if self.status == "Completed":

			if flt(self.individual_progress or 0) < 100:			
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("Individual Progress"),frappe.bold(f'{self.individual_progress}%'),frappe.bold("Pending Review"),frappe.bold("Working"),frappe.bold("100%")))
			elif flt(self.qa_progress or 0) < 100 and len(self.sub_task) > 0 and jumlah_total_elemen_checker_name > 0:		
				# print("jumlah_total_elemen_checker_name : ",jumlah_total_elemen_checker_name)
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("QA Task Progress"),frappe.bold(f'{self.qa_progress}%'),frappe.bold("Integration"),frappe.bold("QA Testing"),frappe.bold("100%")))
			else:
				self.progress = 100

		if self.status == "Working":

			self.progress = 0

			self.review_date = None

			self.completed_on = None

			# self.validate_duration()

		if self.status == "Pending Review":
			if flt(self.individual_progress or 0) < 100:
				# frappe.throw(_("Individual Progress % for a task cannot be less than 100. Please make sure your individual progress is 100% finished"))
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("Individual Progress"),frappe.bold(f'{self.individual_progress}%'),frappe.bold("Pending Review"),frappe.bold("Working"),frappe.bold("100%")))
			else:
				self.progress = 50

		if self.status == "QA Open":
			if flt(self.individual_progress or 0) < 100:
				# frappe.throw(_("Individual Progress % for a task cannot be less than 100. Please make sure your individual progress is 100% finished"))
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("Individual Progress"),frappe.bold(f'{self.individual_progress}%'),frappe.bold("Pending Review"),frappe.bold("Working"),frappe.bold("100%")))
			else:
				self.progress = 50

				if self.review_date is None:
					self.review_date = getdate(today())

				if self.qa_open_date is None:
					self.qa_open_date = getdate(today())


		if self.status == "QA Testing":
			if flt(self.individual_progress or 0) < 100:
				# frappe.throw(_("Individual Progress % for a task cannot be less than 100. Please make sure your individual progress is 100% finished"))
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("Individual Progress"),frappe.bold(f'{self.individual_progress}%'),frappe.bold("Pending Review"),frappe.bold("Working"),frappe.bold("100%")))
			else:
				self.progress = 60

				if self.qa_testing_date is None:
					self.qa_testing_date = getdate(today())

		if self.status == "Integration":

			if flt(self.individual_progress or 0) < 100:
				# frappe.throw(_("Individual Progress % for a task cannot be less than 100. Please make sure your individual progress is 100% finished"))
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("Individual Progress"),frappe.bold(f'{self.individual_progress}%'),frappe.bold("Pending Review"),frappe.bold("Working"),frappe.bold("100%")))

			elif flt(self.qa_progress or 0) < 100 and len(self.sub_task) > 0 and jumlah_total_elemen_checker_name > 0:		
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("QA Task Progress"),frappe.bold(f'{self.qa_progress}%'),frappe.bold("Integration"),frappe.bold("QA Testing"),frappe.bold("100%")))
			else:
				self.progress = 80

				if self.start_date_integration is None:
					self.start_date_integration = getdate(today())

		if self.status == "QA Integration Testing":
			if flt(self.individual_progress or 0) < 100:			
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("Individual Progress"),frappe.bold(f'{self.individual_progress}%'),frappe.bold("Pending Review"),frappe.bold("Working"),frappe.bold("100%")))
    
			elif flt(self.qa_progress or 0) < 100 and len(self.sub_task) > 0 and jumlah_total_elemen_checker_name > 0:		
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("QA Task Progress"),frappe.bold(f'{self.qa_progress}%'),frappe.bold("Integration"),frappe.bold("QA Testing"),frappe.bold("100%")))
			else:
				if self.is_group != True:
					self.progress = 90
     
				if self.end_date_integration is None:
					self.end_date_integration = getdate(today())

		if self.status == "Cancelled":

			self.progress = 0

		self.progress = str(self.progress).split('.')[0]


	def validate_dependencies_for_template_task(self):
		if self.is_template:
			self.validate_parent_template_task()
			self.validate_depends_on_tasks()

	def validate_parent_template_task(self):
		if self.parent_task:
			if not frappe.db.get_value("Task", self.parent_task, "is_template"):
				parent_task_format = """<a href="#Form/Task/{0}">{0}</a>""".format(self.parent_task)
				frappe.throw(_("Parent Task {0} is not a Template Task").format(parent_task_format))

	def validate_depends_on_tasks(self):
		if self.depends_on:
			for task in self.depends_on:
				if not frappe.db.get_value("Task", task.task, "is_template"):
					dependent_task_format = """<a href="#Form/Task/{0}">{0}</a>""".format(task.task)
					frappe.throw(_("Dependent Task {0} is not a Template Task").format(dependent_task_format))

	def validate_completed_on(self):
		if self.completed_on and getdate(self.completed_on) > getdate():
			frappe.throw(_("Completed On cannot be greater than Today"))

	def update_depends_on(self):
		depends_on_tasks = ""
		for d in self.depends_on:
			if d.task and d.task not in depends_on_tasks:
				depends_on_tasks += d.task + ","
		self.depends_on_tasks = depends_on_tasks

	def update_nsm_model(self):
		frappe.utils.nestedset.update_nsm(self)

	def on_update(self):
		self.update_nsm_model()
		self.check_recursion()
		self.reschedule_dependent_tasks()
		self.update_project()
		# self.unassign_todo()
		self.populate_depends_on()
		self.populate_ongoing_sprint()

	def unassign_todo(self):
		if self.status == "Completed":
			close_all_assignments(self.doctype, self.name)
		if self.status == "Cancelled":
			clear(self.doctype, self.name)
	
	def sub_task_data_before_saved(self):
		query = """
			SELECT
				td.sub_task, td.employee_name, td.checker_name
			FROM 
				`tabAssignment Sub Task` td
			WHERE
				td.parent = %s
		"""

		result = frappe.db.sql(query, (self.name,), as_dict=True)

		return result

	def sub_task_data_after_saved(self):
		formatted_data_employee = []
		formatted_data_checker = []
		
		for row in self.sub_task:
			if hasattr(row, 'sub_task') and hasattr(row, 'employee_name'):
				formatted_data_checker.append({"sub_task": row.sub_task,"checker_name": row.checker_name})

			existing_in_sub_task = frappe.db.get_value('SD Sub Task', row.sub_task, '_assign')

			existing_in_task = json.loads(existing_in_sub_task) if existing_in_sub_task else []
			print("existing_in_task: ", existing_in_task)
   
			emp_checker = frappe.db.get_value('Employee', {'name': row.checker_name}, ['user_id'])

			print("checker name: ", row.checker_name)
   
			if emp_checker not in existing_in_task and emp_checker is not None:
				
				print("existing_in_task: ", existing_in_task)
				existing_in_task.append(emp_checker)
     
				updated_assign_str = json.dumps(existing_in_task)

				assign_to.clear("SD Sub Task", row.sub_task)

				assign_to.add(
					dict(
						assign_to=updated_assign_str,
						doctype="SD Sub Task",
						name=row.sub_task,
						notify=True,
						date=getdate(date.today()),
					)
				)
    
		for row in self.sub_task:
			if hasattr(row, 'sub_task') and hasattr(row, 'employee_name'):
				formatted_data_employee.append({"sub_task": row.sub_task, "employee_name": row.employee_name})

			existing_in_sub_task = frappe.db.get_value('SD Sub Task', row.sub_task, '_assign')

			existing_in_task = json.loads(existing_in_sub_task) if existing_in_sub_task else []
			print("existing_in_task: ", existing_in_task)
   
			emp_name = frappe.db.get_value('User', {'full_name': row.employee_name}, ['email'])

			print("emp name: ", row.checker_name)

			if emp_name not in existing_in_task:
     
				existing_in_task.append(emp_name)
				print("existing_in_task: ", existing_in_task)

				updated_assign_str = json.dumps(existing_in_task)

				assign_to.clear("SD Sub Task", row.sub_task)

				assign_to.add(
					dict(
						assign_to=updated_assign_str,
						doctype="SD Sub Task",
						name=row.sub_task,
						notify=True,
						date=getdate(date.today()),
					)
				)

		sub_tasks_array1 = set((item['sub_task'], item['employee_name']) for item in self.sub_task_data_before_saved())
  
		
		sub_tasks_array2 = set((item['sub_task'], item['employee_name'])  for item in formatted_data_employee)
  
		sub_tasks_checker1 = set((item['sub_task'], item['checker_name']) for item in self.sub_task_data_before_saved())

		sub_tasks_checker2 = set((item['sub_task'],item['checker_name'])  for item in formatted_data_checker)
  
		deleted_sub_tasks = sub_tasks_array1 - sub_tasks_array2
		deleted_sub_tasks_checkers = sub_tasks_checker1 - sub_tasks_checker2
  
		for deleted_sub_task_checker, checker_name in deleted_sub_tasks_checkers:
			print("Checker dihapus: ", deleted_sub_task_checker)
			employee_checker_email = frappe.db.get_value('Employee', {'name': checker_name}, ['user_id'])
			assign_to.remove("SD Sub Task", deleted_sub_task_checker, employee_checker_email)

		for deleted_sub_task, employee_name in deleted_sub_tasks:
			print("Sub task dihapus: ", deleted_sub_task)
			employee_email = frappe.db.get_value('Employee', {'name': employee_name}, ['user_id'])
			frappe.db.set_value('SD Sub Task', deleted_sub_task, 'status', 'Open')
			assign_to.remove("SD Sub Task", deleted_sub_task, employee_email)

	def update_sub_task_status(self,sub_task):
     
		sub_task_list = frappe.db.get_list('SD Sub Task',
							filters={
								'status': 'Open',
								'name': sub_task
							},
							fields=['name'],
							)
			
		if sub_task_list:
			subject = sub_task_list[0].get('name')

			if str(subject) == str(sub_task):
				frappe.db.set_value('SD Sub Task', subject, 'status', 'Working')
	
	def update_timesheet_date(self, data):
		employee_info = frappe.db.get_value('Employee', {'user_id': frappe.session.user}, ['name', 'employee_name'], as_dict=1)
		
		if data:
			start_date = data.parent_doc.start_date
			end_date = data.parent_doc.end_date
			sub_task = data.sub_task
			# if data.sub_task != None:
			# 	sub_task = data.sub_task
			# else:
			# 	sub_task = "-"
			activity_type = data.activity_type
			actual_time_str = data.hours_count
			task = data.task
			project = data.project

			timesheet_msg_displayed = frappe.session.get('timesheet_msg_displayed', False)
			if getdate(start_date) < getdate(end_date):
				if not timesheet_msg_displayed:
					user_roles = get_roles()
					if "Administrator" not in user_roles:
						frappe.msgprint(
							title='Hayooooo lupa submit ya? From oyabun',
							msg='You have submitted the timesheet on the following day, please be more disciplined in submitting your timesheet.',
						)
					frappe.session['timesheet_msg_displayed'] = True

     
			self.update_sub_task_status(sub_task)
			
			try:
				actual_time_timedelta = datetime.strptime(actual_time_str, "%H:%M:%S") - datetime.strptime("00:00:00", "%H:%M:%S")
			except ValueError:
				try:
					actual_time_timedelta = datetime.strptime(actual_time_str, "%Y-%m-%d %H:%M:%S") - datetime.strptime("00:00:00", "%H:%M:%S")
				except ValueError:
					try:
						
						days, time_str = actual_time_str.split(", ")
						days = int(days.split()[0])
						hours, minutes, seconds = map(int, time_str.split(":"))
						actual_time_timedelta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
					except ValueError:
						raise ValueError("Unknown time format: {}".format(actual_time_str))



			data = frappe.get_doc("Task", task)
			# existing_row = next((row for row in data.timesheets_data if row.employee_name == employee_info.name and row.project == project), None)
			existing_row = next((row for row in data.timesheets_data if row.employee_name == employee_info.name and row.sub_task == sub_task), None)
			# print("Existing Row:", bool(existing_row))
			# for row in data.timesheets_data:
			# 	print(f"Row: {row.sub_task}, {row.activity_type}")
			if existing_row:
				existing_total_hours_str = existing_row.get("total_working_hours", "00:00:00")
	
				try:
					existing_total_hours_timedelta = datetime.strptime(existing_total_hours_str, "%H:%M:%S") - datetime.strptime("00:00:00", "%H:%M:%S")
				except ValueError:
					try:
						
						existing_total_hours_timedelta = datetime.strptime(existing_total_hours_str, "%Y-%m-%d %H:%M:%S") - datetime.strptime("00:00:00", "%H:%M:%S")
					except ValueError:
						try:
							
							days, time_str = existing_total_hours_str.split(", ")
							days = int(days.split()[0])
							hours, minutes, seconds = map(int, time_str.split(":"))
							existing_total_hours_timedelta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
						except ValueError:
							
							raise ValueError("Unknown time format: {}".format(existing_total_hours_str))

				
				new_total_hours_timedelta = existing_total_hours_timedelta + actual_time_timedelta
	
				new_total_hours_str = str(new_total_hours_timedelta)
				
				# Update existing row
				# print("Updating Data : " + employee_info.name, str(new_total_hours_str), str(task), str(sub_task))
				existing_row.update({
					"total_working_hours": new_total_hours_str,
					"from_date": start_date,
					"to_date": end_date
				})

				if getdate(start_date) < getdate(end_date):
					user_roles = get_roles()
					print(user_roles)
     
					existing_late_submit_count = existing_row.get("late_submit_count")
					existing_late_submit_count += 1

					# Check if the user has either "administrator" or "lead" role
					# if "Administrator" not in user_roles and "Lead" not in user_roles:
					if "Administrator" not in user_roles:
						print("Updating Late Submite Timesheet : " + employee_info.name, str(new_total_hours_str), str(task), str(sub_task))
						existing_row.update({
							"late_submit_count": existing_late_submit_count,
						})
				
			else:
				# Add a new row
				# print("Appending new Data : " + employee_info.name, str(actual_time_timedelta), str(task), str(sub_task))
				existing_late_submit_count = 0
				if getdate(start_date) < getdate(end_date):
					user_roles = get_roles()
					
					if "Administrator" not in user_roles:
						existing_late_submit_count += 1

				new_timesheet_data = {
					"doctype": "SD Assignment Timesheets Data",
					"employee_name": employee_info.name,
					"sub_task": sub_task,
					"activity_type": activity_type,
					"project": project,
					"total_working_hours": actual_time_timedelta,
					"from_date": start_date,
					"to_date": end_date
				}

				if existing_late_submit_count:
					new_timesheet_data["late_submit_count"] = existing_late_submit_count

				data.append("timesheets_data", new_timesheet_data)
			
			data.save()
			
		else:
			frappe.throw(
			title='Timesheet Invalid',
			msg='Timesheet is invalid, contact your leader / supervisor',
			)
		

	def update_time_and_costing(self):
		tl = frappe.db.sql(
			"""select min(from_time) as start_date, max(to_time) as end_date,
			sum(billing_amount) as total_billing_amount, sum(costing_amount) as total_costing_amount,
			sum(hours) as time from `tabTimesheet Detail` where task = %s and docstatus=1""",
			self.name,
			as_dict=1,
		)[0]
		if self.status == "Open":
			self.status = "Working"
		self.total_costing_amount = tl.total_costing_amount
		self.total_billing_amount = tl.total_billing_amount
		self.actual_time = tl.time
		self.act_start_date = tl.start_date
		self.act_end_date = tl.end_date

	def update_project(self):
		if self.project and not self.flags.from_project:
			frappe.get_cached_doc("Project", self.project).update_project()

	def check_recursion(self):
		if self.flags.ignore_recursion_check:
			return
		check_list = [["task", "parent"], ["parent", "task"]]
		for d in check_list:
			task_list, count = [self.name], 0
			while len(task_list) > count:
				tasks = frappe.db.sql(
					" select %s from `tabTask Depends On` where %s = %s " % (d[0], d[1], "%s"),
					cstr(task_list[count]),
				)
				count = count + 1
				for b in tasks:
					if b[0] == self.name:
						frappe.throw(_("Circular Reference Error"), CircularReferenceError)
					if b[0]:
						task_list.append(b[0])

				if count == 15:
					break

	def reschedule_dependent_tasks(self):
		end_date = self.exp_end_date or self.act_end_date
		if end_date:
			for task_name in frappe.db.sql(
				"""
				select name from `tabTask` as parent
				where parent.project = %(project)s
					and parent.name in (
						select parent from `tabTask Depends On` as child
						where child.task = %(task)s and child.project = %(project)s)
			""",
				{"project": self.project, "task": self.name},
				as_dict=1,
			):
				task = frappe.get_doc("Task", task_name.name)
				if (
					task.exp_start_date
					and task.exp_end_date
					and task.exp_start_date < getdate(end_date)
					and task.status == "Open"
				):
					task_duration = date_diff(task.exp_end_date, task.exp_start_date)
					task.exp_start_date = add_days(end_date, 1)
					task.exp_end_date = add_days(task.exp_start_date, task_duration)
					task.flags.ignore_recursion_check = True
					task.save()

	def has_webform_permission(self):
		project_user = frappe.db.get_value(
			"Project User", {"parent": self.project, "user": frappe.session.user}, "user"
		)
		if project_user:
			return True

	def populate_ongoing_sprint(self):
		#save for later
		if self.ongoing_sprint:
			# print(self.ongoing_sprint)
			parent = frappe.get_doc("Event", self.ongoing_sprint)

			# print("SPRINT STATUS : ",parent.status)

			if parent.status == "Open":
				if self.name not in [row.task_id for row in parent.task_list]:
					parent.append(
						"task_list", {"doctype": "Sprint Task List", "task_id": self.name}
					)
					parent.save()


	def populate_depends_on(self):

		if self.parent_task:
			parent = frappe.get_doc("Task", self.parent_task)
			if self.name not in [row.task for row in parent.depends_on]:
				parent.append(
					"depends_on", {"doctype": "Task Depends On", "task": self.name, "subject": self.subject}
				)
				parent.save()

	
	def on_trash(self):
		if check_if_child_exists(self.name):
			throw(_("Child Task exists for this Task. You can not delete this Task."))

		self.update_nsm_model()

	def after_delete(self):
		self.update_project()

	def update_status(self):
		if self.status not in ("Cancelled", "Completed", "QA Open", "Integration", "Parent Task", "Backlog") and self.exp_end_date:
			from datetime import datetime

			if self.exp_end_date + timedelta(days=2) < datetime.now().date():
				self.db_set("status", "Overdue", update_modified=False)
				self.update_project()



# @frappe.whitelist()
def validate_sprint():

	event = frappe.db.get_list('Event', pluck='name',
		filters={
			'starts_on': ['<=', getdate(nowdate())],
			'event_category': ['=', 'Sprint']
		},
						fields=['starts_on', 'name'],
						order_by='starts_on desc',
						page_length=2,
						as_list=False
						)
	# print(event)

	assigment_sprint = frappe.db.get_list('Assignment Sprint', 
		filters={
			'sprint_id': ['in',event]
		},
						fields=['parent', 'name', 'sprint_id'],
						page_length=10000,
						as_list=False
						)
	# print(assigment_sprint)

	before_assignment_task = []
	ongoing_sprint = []
	# print(event[0])
	for task in assigment_sprint:
		if task.sprint_id == event[0]:
			ongoing_sprint.append(task.parent)
		else:
			before_assignment_task.append(task.parent)

	sql_bulk = """UPDATE `tabTask` SET `ongoing_sprint` =%(status)s WHERE `name` in {name}"""
	# sql_bulk = """UPDATE `tabTask` SET `ongoing_sprint` =%(status)s WHERE `name` in {name}"""

	ongoing_sprint_val = {"status" : event[0]}

	before_assignment_task_val = {"status" : ""}
 
	print(sql_bulk.format(name = "('" + "', ".join(ongoing_sprint) + "')"))
	frappe.db.sql(sql_bulk.format(name = "('" + "', '".join(before_assignment_task) + "')"), before_assignment_task_val, debug=True)
	frappe.db.commit()
	frappe.db.sql(sql_bulk.format(name = "('" + "', '".join(ongoing_sprint) + "')"), ongoing_sprint_val,  debug=True, auto_commit=0, update=True, as_dict=1)
	frappe.db.commit()

def create_doc():
		doc = frappe.get_doc({
				'doctype': 'SD Daily Report Timesheets',
				'date': datetime.now().date()
			})
		doc.insert()

		tes_append()
  
def tes_append():
	end_date_today = getdate(now())
	
	timesheets = frappe.get_list('SD Timesheets',
								filters={
									'end_date': ['>=', end_date_today],
									'docstatus': '0'
								},
								)

	data_report_timesheets = frappe.get_list('SD Daily Report Timesheets',
								
								)
 
	data = frappe.get_doc("SD Daily Report Timesheets", data_report_timesheets[0])
	if data:
		for timesheet in timesheets:
			timesheet_doc = frappe.get_doc('SD Timesheets', timesheet.name)
			child_table = timesheet_doc.get('time_logs')

			if child_table:
				last_row = child_table[-1]
				actual_time = last_row.get('hours_count')
				employee_name = timesheet_doc.get('employee_name')
				branch = timesheet_doc.get('branch')
				if actual_time is None:
				
					data.append(
						"timesheets_data", {"doctype": "SD Daily Report Timesheets Items", "employee_name": employee_name, "status": "Timer Not Stopped","department": branch, "timesheets": timesheet.name,
						"hours_count": actual_time}
					)
					
				if actual_time is not None:
					data.append(
						"timesheets_data", {"doctype": "SD Daily Report Timesheets Items", "employee_name": employee_name, "status": "Not Submitted","department": branch, "timesheets": timesheet.name,
						"hours_count": actual_time}
					)
				
	data.save()

@frappe.whitelist()
def check_if_child_exists(name):
	child_tasks = frappe.get_all("Task", filters={"parent_task": name})
	child_tasks = [get_link_to_form("Task", task.name) for task in child_tasks]
	return child_tasks


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_project(doctype, txt, searchfield, start, page_len, filters):
	from erpnext.controllers.queries import get_match_cond

	meta = frappe.get_meta(doctype)
	searchfields = meta.get_search_fields()
	search_columns = ", " + ", ".join(searchfields) if searchfields else ""
	search_cond = " or " + " or ".join(field + " like %(txt)s" for field in searchfields)

	return frappe.db.sql(
		""" select name {search_columns} from `tabProject`
		where %(key)s like %(txt)s
			%(mcond)s
			{search_condition}
		order by name
		limit %(page_len)s offset %(start)s""".format(
			search_columns=search_columns, search_condition=search_cond
		),
		{
			"key": searchfield,
			"txt": "%" + txt + "%",
			"mcond": get_match_cond(doctype),
			"start": start,
			"page_len": page_len,
		},
	)


@frappe.whitelist()
def set_multiple_status(names, status):
	names = json.loads(names)
	for name in names:
		task = frappe.get_doc("Task", name)
		task.status = status
		task.save()


def set_tasks_as_overdue():
	tasks = frappe.get_all(
		"Task",
		filters={"status": ["not in", ["Cancelled", "Completed", "QA Open", "Integration"]]},
		fields=["name", "status", "review_date"],
	)
	for task in tasks:
		if task.status == "Pending Review":
			if getdate(task.review_date) > getdate(today()):
				continue
		frappe.get_doc("Task", task.name).update_status()


@frappe.whitelist()
def make_timesheet(source_name, target_doc=None, ignore_permissions=False):
	def set_missing_values(source, target):
		target.append(
			"time_logs",
			{
				"hours": source.actual_time,
				"completed": source.status == "Completed",
				"project": source.project,
				"task": source.name,
			},
		)

	doclist = get_mapped_doc(
		"Task",
		source_name,
		{"Task": {"doctype": "Timesheet"}},
		target_doc,
		postprocess=set_missing_values,
		ignore_permissions=ignore_permissions,
	)

	return doclist


@frappe.whitelist()
def get_children(doctype, parent, task=None, project=None, is_root=False):

	filters = [["docstatus", "<", "2"]]

	if task:
		filters.append(["parent_task", "=", task])
	elif parent and not is_root:
		# via expand child
		filters.append(["parent_task", "=", parent])
	else:
		filters.append(['ifnull(`parent_task`, "")', "=", ""])

	if project:
		filters.append(["project", "=", project])

	tasks = frappe.get_list(
		doctype,
		fields=["name as value", "subject as title", "is_group as expandable"],
		filters=filters,
		order_by="name",
	)

	# return tasks
	return tasks


@frappe.whitelist()
def add_node():
	from frappe.desk.treeview import make_tree_args

	args = frappe.form_dict
	args.update({"name_field": "subject"})
	args = make_tree_args(**args)

	if args.parent_task == "All Tasks" or args.parent_task == args.project:
		args.parent_task = None

	frappe.get_doc(args).insert()


@frappe.whitelist()
def add_multiple_tasks(data, parent):
	data = json.loads(data)
	new_doc = {"doctype": "Task", "parent_task": parent if parent != "All Tasks" else ""}
	new_doc["project"] = frappe.db.get_value("Task", {"name": parent}, "project") or ""

	for d in data:
		if not d.get("subject"):
			continue
		new_doc["subject"] = d.get("subject")
		new_task = frappe.get_doc(new_doc)
		new_task.insert()


def on_doctype_update():
	frappe.db.add_index("Task", ["lft", "rgt"])


def validate_project_dates(project_end_date, task, task_start, task_end, actual_or_expected_date):
	if task.get(task_start) and date_diff(project_end_date, getdate(task.get(task_start))) < 0:
		frappe.throw(
			_("Task's {0} Start Date cannot be after Project's End Date.").format(actual_or_expected_date)
		)

	if task.get(task_end) and date_diff(project_end_date, getdate(task.get(task_end))) < 0:
		frappe.throw(
			_("Task's {0} End Date cannot be after Project's End Date.").format(actual_or_expected_date)
		)

def update_employee_weight(employee_name,project,weight,branch,total_day,subject,task_name,has_sub_task,status,is_parent):
	user = frappe.get_doc(doctype='SD Data Report', employee_name=employee_name,project_name=project, branch=branch,is_parent = is_parent, total_days=total_day)

	task_item = frappe.get_doc(doctype='SD Data Report Item', task_name=subject)

	if not frappe.db.exists({"doctype": "SD Data Report", "employee_name": employee_name, "project_name": project}):
		user.db_insert()

	weights, name, tot= frappe.db.get_value('SD Data Report',{'employee_name':employee_name,'project_name': project},['weight','name','total_days'])

	user.name = name
	user.branch = branch
	user.total_days = total_day

	parent = frappe.get_doc("SD Data Report", user.name)
	if int(has_sub_task) > 0:
		if status == "Completed" :
			
			if task_name + " - " +task_item.task_name not in [row.task_name for row in parent.task]:
				parent.append(
										"task", {"doctype": "SD Data Report Item", "task_name":  task_name + " - " +task_item.task_name,"task_weight":weight,"days":total_day,"is_parent":is_parent, 'is_subtask' : True}
														)
				parent.save()
				# user.db_update()

		elif status != "Completed":
			item_to_remove = task_name + " - " + task_item.task_name
			item_to_remove_parent = task_name

			if any(row.task_name == item_to_remove for row in parent.task):
				parent.task = [row for row in parent.task if row.task_name != item_to_remove and row.task_name != item_to_remove_parent]
				parent.save()

			parent.save()

	else:
		if status == "Completed" :
			if task_name not in [row.task_name for row in parent.task]:
				parent.append(
										"task", {"doctype": "SD Data Report Item", "task_name":  task_name,"task_weight":weight,"days":total_day,"is_parent":is_parent, 'is_subtask' : False}
														)
				parent.save()

		elif status != "Completed":
			
			item_to_remove = task_item.task_name

			if any(row.task_name == item_to_remove for row in parent.task):
				parent.task = [row for row in parent.task if row.task_name != item_to_remove]
				parent.save()

			parent.save()