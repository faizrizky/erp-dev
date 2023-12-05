# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe

import json
import frappe
from frappe import _, throw
from frappe.desk.form.assign_to import clear, close_all_assignments
from frappe.model.mapper import get_mapped_doc
from frappe.utils import add_days, cstr, date_diff, flt, get_link_to_form, getdate, today
from frappe.utils.nestedset import NestedSet
from datetime import datetime
from datetime import timedelta
from frappe.utils import nowdate, get_datetime, get_time
from frappe import db
import re



class CircularReferenceError(frappe.ValidationError):
	pass


class EndDateCannotBeGreaterThanProjectEndDateError(frappe.ValidationError):
	pass


class CDTask(NestedSet):
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

	nsm_parent_field = "parent_cd_task"

	def get_feed(self):
		return "{0}: {1}".format(_(self.status), self.subject)

	def get_customer_details(self):
		cust = frappe.db.sql("select customer_name from `tabCustomer` where name=%s", self.customer)
		if cust:
			ret = {"customer_name": cust and cust[0][0] or ""}
			return ret
		

	# def before_validate(self):		
	# 	self.validate_task_name()

	def validate(self):
		self.validate_task_status_by_role()
		self.validate_completed_on()
		#self.validate_on_going_sprint()
		self.validate_dates()
		self.validate_parent_expected_end_date()
		self.validate_parent_project_dates()
		self.validate_progress()
		self.validate_status()
		self.validate_weight()
		# self.validate_status_child()
		# self.validate_sprint()
		self.validate_duration()
		self.validate_sub_task()
		self.validate_start_end_working_task()
		self.update_depends_on()
		self.validate_dependencies_for_template_task()
		self.calculate_assignment_task_hours()
		self.calculate_total_working_hours()
		self.calculate_total_hours()
		self.validate_completed_task()

		#self.validate_duration_programmer(self.exp_start_date,self.completed_on)
		#self.validate_duration_qa(self.exp_start_date,self.completed_on,self.qa_open_date,self.qa_testing_date)[0]
		#self.handle_completed_task()

	def validate_task_name(self):
		if self.subject.count("-") > 1 : 
				frappe.throw(_("{0} is using more than one hyphen (-). The maximum allowed hyphen (-) is one.").format(frappe.bold(self.subject),title=_("Invalid Task Name")))
	
	def validate_task_status_by_role(self):
		user_roles = frappe.get_roles(frappe.session.user)
    
		excluded_roles = ['HOD Content Division', 'Administrator']

		if self.status == "Open" and not any(role.lower() in map(str.lower, user_roles) for role in excluded_roles):
			print(frappe.session.user)
			print(frappe.get_roles(frappe.session.user))
			frappe.throw(_("You are not eligable to change the status to {0}. Please contact your Leader.").format(frappe.bold("Open")),title=_("Permission denied to change the status to Open"))

	def handle_completed_task(self):

		status_before = frappe.db.get_value("CD Task", self.name, "status")

		checker_name_list = [x for x in self.sub_task if not x.checker_name == "" and not x.checker_name == None]
		jumlah_total_elemen_checker_name = len(checker_name_list)	

		if len(self.sub_task) > 0 :

			for d in self.sub_task:

				# print("CHECKER NAME iS : ", d.checker_name)

				if flt(d.weight) > 4 or flt(d.weight) < 1:
					frappe.throw(_("Please set {0} value between {1}")
							.format(frappe.bold("Sub Task Weight"), frappe.bold("1 to 4")))


				employee_name = frappe.db.get_value("Employee", d.employee_name, "employee_name")
				checker_name = frappe.db.get_value("Employee", d.checker_name, "employee_name")
				branch = frappe.db.get_value("Employee", d.employee_name, "branch")
				branch_checker = frappe.db.get_value("Employee", d.checker_name, "branch")

				if d.completion == 1 and self.status == "Completed":
					update_employee_weight(employee_name,self.project,d.weight,branch, self.programmer_total_day,d.subject,self.name,len(self.sub_task),self.status,self.is_group)
					
					# self.validate_working_date(branch)

					if jumlah_total_elemen_checker_name > 0:
						if flt(d.qa_weight) > 4 or flt(d.qa_weight) < 1:
							frappe.throw(_("Please set {0} value between {1}")
										.format(frappe.bold("Sub Task QA Weight"), frappe.bold("1 to 4")))

						update_employee_weight(checker_name,self.project,d.qa_weight,branch_checker, self.qa_total_day,d.subject,self.name,len(self.sub_task),self.status,self.is_group)

						# self.validate_working_date(branch_checker)
						
					# update_employee_weight(checker_name,self.project,d.qa_weight,branch,self.qa_total_day,d.subject)


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
		self.validate_table_dates(self.testing_table, "testing_start_date", "testing_end_date", "Testing")

		self.validate_table_dates(self.revision_table, "revision_start_date", "revision_end_date", "Revision")

		self.validate_table_dates(self.revision_table, "revision_testing_start_date", "revision_testing_end_date", "Revision Testing")

				# if (self.exp_start_date and hasattr(d, "revision_start_date") and getattr(d, "revision_start_date") < getdate(self.exp_start_date)):
				# 	frappe.throw(
				# 		_("{0} can not be less than {1}").format(
				# 			frappe.bold("Revision Start Date"), frappe.bold("Expected Start Date")))

	def validate_table_dates(self,data_table, start_field, end_field,type):
		count = 0
		if len(data_table) > 0:
			status_before = frappe.db.get_value("CD Task", self.name, "status")
			parent_doc = frappe.get_doc('CD Task', self.name)
			status_before_testing_completed = ""
			status_before_testing_revision_completed = ""
			status_before_revision_completed = 0
			for d in data_table:
				
				count += 1
				exp_start_date = getdate(self.exp_start_date)
				exp_end_date = getdate(self.exp_end_date)

				if self.status == "Open":
					setattr(d,"testing_start_date", None)
					setattr(d,"testing_end_date", None)
					setattr(d,"testing_total_hours", None)
					setattr(d,"testing_completed", False)
					setattr(d,"revision_start_date", None)
					setattr(d,"revision_end_date", None)
					setattr(d,"revision_total_hours", None)
					setattr(d,"revision_completed", False)
					setattr(d,"revision_testing_start_date", None)
					setattr(d,"revision_testing_end_date", None)
					setattr(d,"revision_testing_total_hours", None)
					setattr(d,"testing_revision_completed", False)
					
				if self.status != "Open" and self.status != "Ongoing":
					if (hasattr(d, start_field) and hasattr(d, end_field) and getdate(getattr(d, end_field)) < getdate(getattr(d, start_field))):
								frappe.throw(_("In row {0} with Subject : {1}, {2} can not be greater than {3} in the {4}").format(frappe.bold(count),frappe.bold(d.subject), frappe.bold(type + " " +"End Date"), frappe.bold(type + " " + "Start Date"), frappe.bold(type + " " + "Table.")),title=_("Invalid Date"))
					
					if type == "Testing":

						if getattr(d,"testing_start_date") == None or getattr(d,"testing_start_date") == "":
							frappe.throw(_("In no {0} with Subject : {1}, {2} in {3} cannot be empty. Please review the information in the {4}.").format(frappe.bold(count),frappe.bold(d.subject),frappe.bold("Testing Start Date"),frappe.bold("Testing"),frappe.bold(type + " " + "Table")),title=_("Testing Start Date is Empty"))

						# print("ATAS", parent_doc.testing_table)
						for child in parent_doc.testing_table:
							# print("CHILD STATUS BEFORE: ",child.testing_completed)
							status_before_testing_completed = child.testing_completed
							# print("status_before_testing_completed 1 : ",status_before_testing_completed)

						if self.exp_start_date and hasattr(d,"testing_start_date"):
							start_date = getdate(getattr(d,"testing_start_date"))

						if self.exp_start_date and hasattr(d, "testing_end_date"):
							end_date = getdate(getattr(d, "testing_end_date"))
						
						# print("STATUS AFTER : ",getattr(d,"testing_completed"))
						# print("status_before_testing_completed 2 : ",status_before_testing_completed)
						if status_before_testing_completed == False and getattr(d,"testing_completed") == True :
							if getattr(d,"testing_completed") == True :
								setattr(d,"testing_end_date", datetime.now() + timedelta(hours=7))
							else :
								setattr(d,"testing_end_date", None)
								setattr(d,"testing_total_hours", None)
						elif getattr(d,"testing_completed") == False:
							setattr(d,"testing_end_date", None)

						if getattr(d,"testing_start_date") == None or getattr(d,"testing_start_date") == "":
							setattr(d,"testing_total_hours", None)
						
						if getattr(d,"testing_completed") != True and getattr(d,"testing_start_date") == "" and getattr(d,"testing_start_date") == None:
							frappe.throw(_("In no {0} with Subject : {1}, {2} in {3} is {4}. Please review the information in the {5}.").format(frappe.bold(count),frappe.bold(d.subject),frappe.bold(type + " " +"Start Date"),frappe.bold("Testing"),frappe.bold("empty"),frappe.bold("Testing"),frappe.bold(type + " " + "Table")),title=_(type + " " +"Start Date is Empty"))

					elif type == "Revision":
						if getattr(d,"revision_start_date") == None or getattr(d,"revision_start_date") == "":
							frappe.throw(_("In no {0} with Subject : {1}, {2} in {3} cannot be empty. Please review the information in the {4}.").format(frappe.bold(count),frappe.bold(d.subject),frappe.bold("Revision Start Date"),frappe.bold("Revision Testing"),frappe.bold(type + " " + "Table")),title=_("Revision Start Date is Empty"))
						
						# Accessing values from the 'revision_table' child table
						for child in parent_doc.revision_table:
							# print("CHILD STATUS BEFORE: ",child.revision_completed)
							status_before_revision_completed = child.revision_completed

						# status_revision_completed = frappe.db.get_value("CD Task", self.name, "status")
						if self.exp_start_date and hasattr(d,"revision_start_date"):
							start_date = getdate(getattr(d,"revision_start_date"))

						if self.exp_start_date and hasattr(d, "revision_end_date"):
							end_date = getdate(getattr(d, "revision_end_date"))

						# print("STATUS AFTER : ",getattr(d,"revision_completed"))
						if status_before_revision_completed == False and getattr(d,"revision_completed") == True :
							if getattr(d,"revision_completed") == True :
								setattr(d,"revision_end_date", datetime.now() + timedelta(hours=7))
							
							else :
								setattr(d,"revision_end_date", None)
								setattr(d,"revision_total_hours", None)
						elif getattr(d,"revision_completed") == False:
							setattr(d,"revision_end_date", None)


						if getattr(d,"revision_start_date") == None or getattr(d,"revision_start_date") == "":
							setattr(d,"revision_total_hours", None)
						
						if getattr(d,"revision_completed") != True and getattr(d,"revision_start_date") == "" and getattr(d,"revision_start_date") == None:
							frappe.throw(_("In no {0} with Subject : {1}, {2} in {3} is {4}. Please review the information in the {5}.").format(frappe.bold(count),frappe.bold(d.subject),frappe.bold(type + " " +"Start Date"),frappe.bold("Revision Testing"),frappe.bold("empty"),frappe.bold("Revision"),frappe.bold(type + " " + "Table")),title=_(type + " " +"Start Date is Empty"))

					elif type == "Revision Testing":
						# print("REVISION TESTING START DATE : ",getattr(d,"revision_testing_start_date"))
						if getattr(d,"revision_completed") == True and getattr(d,"testing_revision_completed") == True:
							if getattr(d,"revision_testing_start_date") == None or getattr(d,"revision_testing_start_date") == "":
								frappe.throw(_("In no {0} with Subject : {1}, {2} in {3} cannot be empty. Please review the information in the {4}.").format(frappe.bold(count),frappe.bold(d.subject),frappe.bold("Revision Start Testing Date"),frappe.bold("Revision Testing"),frappe.bold(type + " " + "Table")),title=_("Revision Start Testing Date is Empty"))

						for child in parent_doc.revision_table:
							# print("CHILD STATUS BEFORE: ",child.testing_revision_completed)
							status_before_testing_revision_completed = child.testing_revision_completed
							
						if self.exp_start_date and hasattr(d,"revision_testing_start_date"):
							start_date = getdate(getattr(d,"revision_testing_start_date"))
							
						if self.exp_start_date and hasattr(d, "revision_testing_end_date"):
							end_date = getdate(getattr(d, "revision_testing_end_date"))

						if status_before_testing_revision_completed == False and getattr(d,"testing_revision_completed") == True :
							if getattr(d,"testing_revision_completed") == True:
								setattr(d,"revision_testing_end_date", datetime.now() + timedelta(hours=7))
							else:
								setattr(d,"revision_testing_end_date", None)
								setattr(d,"revision_testing_total_hours", None)
						elif getattr(d,"testing_revision_completed") == False:
							setattr(d,"revision_testing_end_date", None)

						#perlu diubah validation messagenya
						if getattr(d,"revision_testing_start_date") == None or getattr(d,"revision_testing_start_date") == "":
							setattr(d,"revision_testing_total_hours", None)
						elif get_time(get_datetime(getattr(d, "revision_testing_start_date"))) < get_time(get_datetime(getattr(d, "revision_end_date"))):
								frappe.throw(_("In {0} with Subject: {1}, {2} in {3} cannot be less than {4} in {5}. Please review the information in the {6}.").format(
									frappe.bold(count),
									frappe.bold(d.subject),
									frappe.bold(type + " " + "Start Time"),
									frappe.bold("(" + type + " " + "Table)"),
									frappe.bold("Revision End Time"),
									frappe.bold("(Revision Time Details Section)"),
									frappe.bold(type + " " + "Table")),
									title=_("Invalid Time"))
						elif get_time(get_datetime(getattr(d, "revision_testing_start_date"))) > get_time(get_datetime(getattr(d, "revision_testing_end_date"))):
								frappe.throw(_("In {0} with Subject: {1}, {2} in {3} can not be greater than {4} in {3}. Please review the information in the {5}.").format(
									frappe.bold(count),
									frappe.bold(d.subject),
									frappe.bold(type + " " + "Start Date"),
									frappe.bold("(" + type + " " + "Table)"),
									frappe.bold(type + " " + "End Date"),
									frappe.bold(type + " " + "Table")),
									title=_("Invalid Time"))

						if getattr(d,"testing_revision_completed") == True and getattr(d,"testing_type") == "":
							frappe.throw(_("In no {0} with Subject : {1}, {2} in {3} cannot be empty. Please review the information in the {4}.").format(frappe.bold(count),frappe.bold(d.subject),frappe.bold("Revision Testing Type"),frappe.bold("Revision Testing"),frappe.bold(type + " " + "Table")),title=_("Revision Testing Type is Empty"))

						if getattr(d,"revision_completed") != True and getattr(d,"testing_revision_completed") == True:
							frappe.throw(_("In no {0} with Subject : {1}, {2} in {3} cannot be fulfilled because {4} is not Completed. Please review the information in the {5}.").format(frappe.bold(count),frappe.bold(d.subject),frappe.bold(type + " " +"Start Date"),frappe.bold("Revision Testing"),frappe.bold("Revision"),frappe.bold(type + " " + "Table")),title=_("Revision is Not Completed"))
						
						
						if self.status == "Completed" and status_before == "Revision":
							if getattr(d,"testing_revision_completed") != True:
								frappe.throw(_("Status cannot be {0} because in no {1} with Subject : {2}, {3} is not Checked. Please review the information in the {4}.").format(frappe.bold("Completed"),frappe.bold(count),frappe.bold(d.subject),frappe.bold("Testing Revision Completed"),frappe.bold(type + " " + "Table")),title=_("Revision is Not Completed"))

					if start_date < exp_start_date:
						frappe.throw(_("In no {0} with Subject : {1}, {2} in {3} can not be less than {4} in {5}. Please review the information in the {6}.").format(frappe.bold(count),frappe.bold(d.subject),frappe.bold(type + " " +"Start Date"),frappe.bold("(" + type + " " + "Table)"), frappe.bold("Start Date" + " "), frappe.bold("(Task Timeline Section)"),frappe.bold(type + " " + "Table")),title=_("Invalid Date"))
					
					if end_date > exp_end_date:
						frappe.throw(_("In no {0} with Subject : {1}, {2} in {3} can not be greater than {4} in {5}. Please review the information in the {6}.").format(
							frappe.bold(count),
							frappe.bold(d.subject),
							frappe.bold(type + " " +"End Date" + "(" + str(end_date) + ")"),
							frappe.bold("(" + type + " " + "Table)"), 
							frappe.bold("End Date" + "(" + str(exp_end_date) + ")" + " "), 
							frappe.bold("(Task Timeline Section)"),
							frappe.bold(type + " " + "Table")),
							title=_("Invalid Date"))

				

				
				
				
	def validate_parent_expected_end_date(self):
		if self.parent_cd_task:
			parent_exp_end_date = frappe.db.get_value("CD Task", self.parent_cd_task, "exp_end_date")
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
		check_val = dict([])
		has_error = []
		has_hypen= []

		if len(self.sub_task) > 0:

			total_weight = 0

			for d in self.sub_task:
				# check if the same pa aji
				if d.subject not in check_val :
					check_val[d.subject] = 1
				else:
					check_val[d.subject] += 1
				
				if d.subject.count("-") > 0:
					has_hypen.append(d.subject)

				if check_val[d.subject] <= 1:

					jumlah_total_elemen = len(self.sub_task)

					programmer_condition = sum(1 for x in self.sub_task if d.completion == True)
					sub_task_percentage_programmer = (programmer_condition / jumlah_total_elemen) * 100

					if sub_task_percentage_programmer == 100:
						arr.append(sub_task_percentage_programmer)
					'''
					qa_condition = sum(1 for x in self.sub_task if d.qa_completion == True)
					sub_task_percentage_qa = (qa_condition / jumlah_total_elemen) * 100

					if sub_task_percentage_qa == 100:
						arr_qa.append(sub_task_percentage_qa)
					'''
					# print(sub_task_percentage)
					count_true_programmer = len(arr)

					total_weight += d.weight

				else:
					has_error.append(d.subject)

	
			if len(has_error) > 0 : 
				frappe.throw(_("{0} Name in the {1} cannot be same").format(frappe.bold((" , ").join(has_error)),frappe.bold("Sub Task Table")),title=_("Invalid Sub Task Name"))
			
			if len(has_hypen) > 0:
				frappe.throw(_("{0} Name in the {1} cannot contain a hyphen (-)").format(frappe.bold((" , ").join(has_hypen)),frappe.bold("Sub Task Table")),title=_("Invalid Sub Task Name"))

			if total_weight > self.task_weight:
				frappe.throw(_("Your {3} is : {0} in the {1}. {3} in {1} cannot more than Task Weight : {2}").format(frappe.bold(total_weight),frappe.bold("Sub Task Table"),frappe.bold(self.task_weight),frappe.bold("Total Weight")),title=_("Invalid Sub Task Name"))
		
			percentage_programmer = (count_true_programmer / len(self.sub_task)) * 100

			self.progress = percentage_programmer

		else:
			print("Manual Percentage")

	'''
	def validate_status_child(self):

		if self.status != self.get_db_value("status") and self.status == "Open":
			for d in self.depends_on:
				task_subject = frappe.db.get_value('Task', d.task, ['subject'])
				frappe.db.set_value('Task', task_subject, 'status', 'Open')


	
	def validate_on_going_sprint(self):

		arr = [] 
		for items in self.multi_sprint:
			doc = frappe.get_doc('Event', items.sprint_id)

			arr.append(doc.starts_on)
			arr.append(doc.ends_on)

		if (len(arr) <= 0):
			frappe.throw(_("You need to fill {0} field in Category Sprint to continue").format(frappe.bold("Sprint")))

		self.exp_start_date =min(arr)
		self.exp_end_date = max(arr)
	'''

	def validate_status(self):
		if self.is_template and self.status != "Template":
			self.status = "Template"
		if self.status != self.get_db_value("status") and self.status == "Completed":
			for d in self.depends_on:
				if frappe.db.get_value("CD Task", d.task, "status") not in ("Completed", "Cancelled", ""):
					frappe.throw(
						_(
							"Cannot complete task {0} as its dependant task {1} are not completed / cancelled."
						).format(frappe.bold(self.name), frappe.bold(d.task))
					)

			close_all_assignments(self.doctype, self.name)

	def validate_weight(self):
		if flt(self.task_weight) > 100 or flt(self.task_weight) < 1 and self.is_group != True:
				frappe.throw(_("Please set {0} value between {1}")
					.format(frappe.bold("Task Weight"), frappe.bold("1 to 100")))
				
	def validate_start_end_working_task(self):
		if self.status == "Open":
			self.total_hours = None
			self.start_working_hours = None
			self.end_working_hours = None
			# self.start_testing_hours = None
			self.completed_on = None
			self.revision_start_date = None
			self.revision_end_date = None
			self.total_revision_hours = None
			self.total_working_hours = None
			self.total_testing_hours = None
			self.testing_table = []
			self.revision_table = []

		if self.status == "Ongoing":
			self.start_working_hours = datetime.now() + timedelta(hours=7)
			self.total_working_hours = None
			self.total_testing_hours = None

		if self.status == "Testing Open":
			self.end_working_hours = datetime.now() + timedelta(hours=7)	
		
		# if self.status == "Ongoing Testing":
		# 	self.start_testing_hours = datetime.now() + timedelta(hours=7)	

		if self.status == "Revision":
			self.revision_start_date = datetime.now() + timedelta(hours=7)
		
		if self.status == "Completed":
			# self.revision_start_date = datetime.now() + timedelta(hours=7)
			self.completed_on = datetime.now() + timedelta(hours=7)	

	def check_format(self,input_str):
		self.match = re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', input_str)
		if self.match:
			return "%Y-%m-%d %H:%M:%S"

		self.match = re.match(r'\d{1,2}:\d{2}:\d{2}', input_str)
		if self.match:
			return "%H:%M:%S"

		return None	

	def duration_to_timedelta(self,duration_str):
		self.parts = duration_str.split(', ')
		self.days = 0
		self.time_parts = self.parts[-1].split(':')
		if len(self.parts) == 2:
			self.days = int(self.parts[0].split()[0])
		self.hours, self.minutes, self.seconds = map(int, self.time_parts)
		return timedelta(days=self.days, hours=self.hours, minutes=self.minutes, seconds=self.seconds)

	def validate_completed_task(self):
		if self.status == "Completed":
			self.completed_by = frappe.session.user

			if self.completed_on == "" or self.completed_on is None:
				frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Completed On")))
				#self.completed_on = datetime.now() + timedelta(hours=7)

	def calculate_total_hours(self):
		# print(self.total_testing_hours)
		if self.status != "Open":
			if self.total_working_hours != None:
				self.check_format(self.total_working_hours)
				duration1 = self.duration_to_timedelta(self.total_working_hours)
			else:
				self.total_working_hours = "0:00:00"
				duration1 = self.duration_to_timedelta(self.total_working_hours)

			# Validate and format the total_testing_hours
			if self.total_testing_hours != None:
				self.check_format(self.total_testing_hours)
				duration2 = self.duration_to_timedelta(self.total_testing_hours)
			else:
				self.total_testing_hours = "0:00:00"
				duration2 = self.duration_to_timedelta(self.total_testing_hours)

			# Validate and format the total_revision_hours
			if self.total_revision_hours != None:
				self.check_format(self.total_revision_hours)
				duration3 = self.duration_to_timedelta(self.total_revision_hours)
			else :
				self.total_revision_hours = "0:00:00"
				self.check_format(self.total_revision_hours)
				duration3 = self.duration_to_timedelta(self.total_revision_hours)
			
			if self.revision_testing_total_hours != None:
				self.check_format(self.revision_testing_total_hours)
				duration4 = self.duration_to_timedelta(self.revision_testing_total_hours)
			else:
				self.revision_testing_total_hours = "0:00:00"
				self.check_format(self.revision_testing_total_hours)
				duration4 = self.duration_to_timedelta(self.revision_testing_total_hours)
		

			total_duration = duration1 + duration2 + duration3 + duration4

			total_duration_str = str(total_duration)

			self.total_hours = str(total_duration_str)
			
			return self.total_hours
	
	def calculate_table_total_hours(self,data_table, start_field, end_field, total_field):
		total_seconds = 0
		for d in data_table:
			if hasattr(d, end_field) and getattr(d, end_field) != "":	
				if getattr(d,start_field) != None and getattr(d,end_field) != None:
					start_date_str = str(getattr(d, start_field)).split('.')[0]
					end_date_str = str(getattr(d, end_field)).split('.')[0]

					date_format = "%Y-%m-%d %H:%M:%S" if len(start_date_str) > 10 else "%H:%M:%S"
					start_date = datetime.strptime(start_date_str, date_format)
					end_date = datetime.strptime(end_date_str, date_format)

					time_difference = end_date - start_date
					setattr(d, total_field, str(time_difference))

					# Calculate the total time in seconds for the current item
					days, seconds = time_difference.days, time_difference.seconds
					total_seconds_item = days * 86400 + seconds
					total_seconds += total_seconds_item

		# Calculate the total time in the format 'D days, H:MM:SS'
		total_time = str(timedelta(seconds=total_seconds))
		return total_time

	def calculate_assignment_task_hours(self):
		if len(self.testing_table) > 0:
			self.total_testing_hours = self.calculate_table_total_hours(self.testing_table, "testing_start_date", "testing_end_date", "testing_total_hours")
		else:
			self.total_testing_hours = None

		if len(self.revision_table) > 0:
			self.total_revision_hours = self.calculate_table_total_hours(self.revision_table, "revision_start_date", "revision_end_date", "revision_total_hours")
		else:
			self.total_revision_hours = None

		if len(self.revision_table) > 0 and self.total_revision_hours != "":
			self.revision_testing_total_hours = self.calculate_table_total_hours(self.revision_table, "revision_testing_start_date", "revision_testing_end_date", "revision_testing_total_hours")
		else:
			self.revision_testing_total_hours = None


		
	"""	
	def calculate_assignment_task_hours2(self,table_name,start_hours,end_hours,total_hours):
		arr = []
		total_seconds = 0
		count = 0

		if len(self.testing_table) > 0:
			for d in self.testing_table:
				count += 1
				if d.end_testing_hours != "":
					if (d.start_testing_hours and d.end_testing_hours and getdate(d.end_testing_hours) < getdate(d.start_testing_hours)):
						frappe.throw(_("In row {0} with Subject : {1} , {2} can not be greater than {3} in the Testing Table").format(frappe.bold(count),frappe.bold(d.subject), frappe.bold("End Testing Date"), frappe.bold("Start Testing Date")))

					if d.completed == True and (d.end_testing_hours == "" or d.end_testing_hours == None):
						d.end_testing_hours = datetime.now() + timedelta(hours=7)

					start_date_str = str(d.start_testing_hours).split('.')[0]
					end_date_str = str(d.end_testing_hours).split('.')[0]

					date_format = "%Y-%m-%d %H:%M:%S" if len(start_date_str) > 10 else "%H:%M:%S"
					start_date = datetime.strptime(start_date_str, date_format)
					end_date = datetime.strptime(end_date_str, date_format)

					time_difference = end_date - start_date
					d.testing_total_hours = str(time_difference)
					print(d.testing_total_hours)

					arr.append(d.testing_total_hours)

			for time_str in arr:
				# Split the time string
				parts = time_str.split(', ')
				if len(parts) > 1:
					days_part = parts[0]
					time_part = parts[1]
				else:
					days_part = "0 days"
					time_part = time_str

				days = int(days_part.split()[0])
				time_parts = time_part.split(':')
				hours = int(time_parts[0])
				minutes = int(time_parts[1])
				seconds = int(time_parts[2])

				# Calculate the total time in seconds for the current item
				total_seconds_item = days * 86400 + hours * 3600 + minutes * 60 + seconds
				print(total_seconds_item)

				# Add the time for the current item to the total_seconds
				total_seconds += total_seconds_item

			# Calculate the total time in the format 'D days, H:MM:SS'
			total_time = str(timedelta(seconds=total_seconds))

			self.total_testing_hours = total_time

		if len(self.revision_table) > 0:
			for d in self.revision_table:
				count += 1
				if d.end_revision_hours != "":
					if (d.start_revision_hours and d.end_revision_hours and getdate(d.end_revision_hours) < getdate(d.start_revision_hours)):
						frappe.throw(_("In row {0} with Subject : {1} , {2} can not be greater than {3} in the Testing Table").format(frappe.bold(count),frappe.bold(d.subject), frappe.bold("End Testing Date"), frappe.bold("Start Testing Date")))

					if d.revision_completed == True and (d.end_revision_hours == "" or d.end_revision_hours == None):
						d.end_revision_hours = datetime.now() + timedelta(hours=7)

					start_date_str = str(d.start_revision_hours).split('.')[0]
					end_date_str = str(d.end_revision_hours).split('.')[0]

					date_format = "%Y-%m-%d %H:%M:%S" if len(start_date_str) > 10 else "%H:%M:%S"
					start_date = datetime.strptime(start_date_str, date_format)
					end_date = datetime.strptime(end_date_str, date_format)

					time_difference = end_date - start_date
					d.revision_total_hours = str(time_difference)
					print(d.revision_total_hours)

					arr.append(d.revision_total_hours)

			for time_str in arr:
				# Split the time string
				parts = time_str.split(', ')
				if len(parts) > 1:
					days_part = parts[0]
					time_part = parts[1]
				else:
					days_part = "0 days"
					time_part = time_str

				days = int(days_part.split()[0])
				time_parts = time_part.split(':')
				hours = int(time_parts[0])
				minutes = int(time_parts[1])
				seconds = int(time_parts[2])

				# Calculate the total time in seconds for the current item
				total_seconds_item = days * 86400 + hours * 3600 + minutes * 60 + seconds
				print(total_seconds_item)

				# Add the time for the current item to the total_seconds
				total_seconds += total_seconds_item

			# Calculate the total time in the format 'D days, H:MM:SS'
			total_time = str(timedelta(seconds=total_seconds))

			self.total_revision_hours = total_time

		return arr
	"""

	days = 0
	d1 = 0
	d2 = 0

	def calculate_total_working_hours(self):
		
		date_format = "%Y-%m-%d %H:%M:%S"

		if self.status != "Open" and self.status != "Ongoing" :
			if not self.start_working_hours:
				frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Start Working Hours")))
			if not self.end_working_hours:
				frappe.throw(_("{0} Cannot be empty").format(frappe.bold("End Working Hours")))

			start_date_str = str(self.start_working_hours).split('.')[0]
			end_date_str = str(self.end_working_hours).split('.')[0]

			start_date = datetime.strptime(start_date_str, date_format)
			end_date = datetime.strptime(end_date_str, date_format)

			time_difference = end_date - start_date
			self.total_working_hours = str(time_difference).split('.')[0]

			if self.status == "Completed":
				# if not self.start_testing_hours:
				# 	frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Start Testing Hours")))
				if not self.completed_on:
					frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Completed On")))
				"""
				print("STATUS BEFORE : ",status_before)
				if status_before == "Revision":
					print("MASUK")
					if not self.revision_start_date:
						frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Revision Start Date")))
					# if not self.revision_end_date:
					# 	frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Revision End Date")))

					start_date_str = str(self.revision_start_date).split('.')[0]
					end_date_str = str(self.completed_on).split('.')[0]

					start_date = datetime.strptime(start_date_str, date_format)
					end_date = datetime.strptime(end_date_str, date_format)

					time_difference = end_date - start_date

					self.total_revision_hours = str(time_difference).split('.')[0]
				"""

				#Versi 1 Testing
				"""
				start_date_str = str(self.start_testing_hours).split('.')[0]
				end_date_str = str(self.end_testing_hours).split('.')[0]

				start_date = datetime.strptime(start_date_str, date_format)
				end_date = datetime.strptime(end_date_str, date_format)

				time_difference = end_date - start_date
				self.total_testing_hours = str(time_difference).split('.')[0]
				"""

			# return self.total_working_hours, self.total_testing_hours, self.total_revision_hours
			return self.total_working_hours

	def validate_duration(self):
		if flt(self.exp_start_date == None):
			frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Expected Start Date")))

		self.start_date = str(self.exp_start_date)
		self.end_date = str(self.exp_end_date)

		self.d1 = datetime.strptime(self.start_date, "%Y-%m-%d")

		if flt(self.exp_end_date == None):
			frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Expected End Date")))
		else:
			self.d2 = datetime.strptime(self.end_date, "%Y-%m-%d")
		# 	# delta = self.d2 - self.d1

		self.d2 = datetime.strptime(self.end_date, "%Y-%m-%d")
		self.daydiff = self.d2.weekday() - self.d1.weekday()

		self.duration = ((self.d2-self.d1).days - self.daydiff) / 7 * 5 + min(self.daydiff,5) - (max(self.d2.weekday() - 4, 0) % 5) + 1
	
		# self.strdays = str(self.days).split('.')[0]

		# self.duration = self.days

	def validate_progress(self):
		if flt(self.progress or 0) > 100 or flt(self.progress) < 0:
			# frappe.throw(_("Individual Progress % for a task cannot be more than 100."))
			frappe.throw(_("Your Overall Task Progress is {0}. Overall Task Progress {1} for a task cannot be more than "+ "'{2}' or less than "+ "'{3}'")
				.format(frappe.bold(f'{self.progress} %'),frappe.bold("%"),frappe.bold("100%"),frappe.bold("0%")))
		

		if self.status == "Open":

			self.duration = 0
			self.progress = 0

		if self.status == "Completed":

			if flt(self.progress or 0) < 100 and len(self.sub_task) > 0:			
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("Overall Task Progress"),frappe.bold(f'{self.progress}%'),frappe.bold("Completed"),frappe.bold("Ongoing"),frappe.bold("100%")))
			else:
				self.progress = 100
			

		if self.status == "Ongoing":

			self.progress = 50

			self.review_date = None

			self.completed_on = None
		
		if self.status == "Testing Open":
			self.progress = 80
			
		if self.status == "Ongoing Testing":
			self.progress = 90

		if self.status == "Revision":
			self.progress = 0

		'''
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
					# print("START INTEGRATION : ", self.start_date_integration)

		if self.status == "QA Integration Testing":
			if flt(self.individual_progress or 0) < 100:			
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("Individual Progress"),frappe.bold(f'{self.individual_progress}%'),frappe.bold("Pending Review"),frappe.bold("Working"),frappe.bold("100%")))
			elif flt(self.qa_progress or 0) < 100 and len(self.sub_task) > 0 and jumlah_total_elemen_checker_name > 0:		
				# print("jumlah_total_elemen_checker_name : ",jumlah_total_elemen_checker_name)
				frappe.throw(_("Your {0} is {1}. Please check your {0} field. {0} cannot be set in {2} status, please back to {3} status, and set your {0} again. Then set back to {2} and save it. Things to Note is {0} cannot less than {4} in {2} status.")
				.format(frappe.bold("QA Task Progress"),frappe.bold(f'{self.qa_progress}%'),frappe.bold("Integration"),frappe.bold("QA Testing"),frappe.bold("100%")))
			else:
				if self.is_group != True:
					self.progress = 90
				# print("END INTEGRATION : ", self.end_date_integration)
				if self.end_date_integration is None:
					self.end_date_integration = getdate(today())
			#1. harus get doc Event sprint yg sedang open, kemudian get starts_on dan ends_on nya kapan
			#2. selisihkan start time dengan ends_on sprint yg sedang berjalan
		'''
		if self.status == "Cancelled":

			self.progress = 0

		self.progress = str(self.progress).split('.')[0]

	def validate_dependencies_for_template_task(self):
		if self.is_template:
			self.validate_parent_template_task()
			self.validate_depends_on_tasks()

	def validate_parent_template_task(self):
		if self.parent_cd_task:
			if not frappe.db.get_value("CD Task", self.parent_cd_task, "is_template"):
				parent_cd_task_format = """<a href="#Form/Task/{0}">{0}</a>""".format(self.parent_cd_task)
				frappe.throw(_("Parent Task {0} is not a Template Task").format(parent_cd_task_format))

	def validate_depends_on_tasks(self):
		if self.depends_on:
			for task in self.depends_on:
				if not frappe.db.get_value("CD Task", task.task, "is_template"):
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
		#self.populate_ongoing_sprint()

	def unassign_todo(self):
		if self.status == "Completed":
			close_all_assignments(self.doctype, self.name)
		if self.status == "Cancelled":
			clear(self.doctype, self.name)

	def update_time_and_costing(self):
		tl = frappe.db.sql(
			"""select min(from_time) as start_date, max(to_time) as end_date,
			sum(billing_amount) as total_billing_amount, sum(costing_amount) as total_costing_amount,
			sum(hours) as time from `tabTimesheet Detail` where task = %s and docstatus=1""",
			self.name,
			as_dict=1,
		)[0]
		if self.status == "Open":
			self.status = "Ongoing"
		self.total_costing_amount = tl.total_costing_amount
		self.total_billing_amount = tl.total_billing_amount
		self.actual_time = tl.time
		self.act_start_date = tl.start_date
		self.act_end_date = tl.end_date

	def update_project(self):
		if self.project and not self.flags.from_project:
			frappe.get_cached_doc("CD Project", self.project).update_project()

	def check_recursion(self):
		if self.flags.ignore_recursion_check:
			return
		check_list = [["task", "parent"], ["parent", "task"]]
		for d in check_list:
			task_list, count = [self.name], 0
			while len(task_list) > count:
				tasks = frappe.db.sql(
					" select %s from `tabCD Task Depends On` where %s = %s " % (d[0], d[1], "%s"),
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
				select name from `tabCD Task` as parent
				where parent.project = %(project)s
					and parent.name in (
						select parent from `tabCD Task Depends On` as child
						where child.task = %(task)s and child.project = %(project)s)
			""",
				{"project": self.project, "task": self.name},
				as_dict=1,
			):
				task = frappe.get_doc("CD Task", task_name.name)
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

		if self.parent_cd_task:
			parent = frappe.get_doc("CD Task", self.parent_cd_task)
			if self.name not in [row.task for row in parent.depends_on]:
				parent.append(
					"depends_on", {"doctype": "CD Task Depends On", "task": self.name, "subject": self.subject}
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
			'starts_on': ['<=', getdate(nowdate())]
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

@frappe.whitelist()
def check_if_child_exists(name):
	child_tasks = frappe.get_all("CD Task", filters={"parent_cd_task": name})
	child_tasks = [get_link_to_form("CD Task", task.name) for task in child_tasks]
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
		filters.append(["parent_cd_task", "=", task])
	elif parent and not is_root:
		# via expand child
		filters.append(["parent_cd_task", "=", parent])
	else:
		filters.append(['ifnull(`parent_cd_task`, "")', "=", ""])

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

	if args.parent_cd_task == "All Tasks" or args.parent_cd_task == args.project:
		args.parent_cd_task = None

	frappe.get_doc(args).insert()


@frappe.whitelist()
def add_multiple_tasks(data, parent):
	data = json.loads(data)
	new_doc = {"doctype": "Task", "parent_cd_task": parent if parent != "All Tasks" else ""}
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
		# print("blm ada")
		user.db_insert()

	# print("udah ada")
	# weights, name, tot= frappe.db.get_value('SD Data Report',{'employee_name':employee_name,'project_name': project},['weight','name','total_days'])
	# weights, name, qa_idle_day= frappe.db.get_value('SD Data Report',{'employee_name':employee_name,'project_name': project},['weight','name','qa_idle_total_day'])
	weights, name, tot= frappe.db.get_value('SD Data Report',{'employee_name':employee_name,'project_name': project},['weight','name','total_days'])

	user.name = name
	user.branch = branch
	# print("NAME : ",user.employee_name)
	# print("qa_idle_day : ",user.qa_idle_total_day)
	user.total_days = total_day

	parent = frappe.get_doc("SD Data Report", user.name)
	if int(has_sub_task) > 0:
		if status == "Completed" :
			# user.weight = qa_idle_total_day
			# user.qa_idle_total_day = user.qa_idle_total_day + qa_idle_total_day
			# user.total_days = tot + int(total_day)
			if task_name + " - " +task_item.task_name not in [row.task_name for row in parent.task]:
				parent.append(
										"task", {"doctype": "SD Data Report Item", "task_name":  task_name + " - " +task_item.task_name,"task_weight":weight,"days":total_day,"is_parent":is_parent, 'is_subtask' : True}
														)
				parent.save()
				# user.db_update()

		elif status != "Completed":
			# user.weight = weights + weight
			# user.qa_idle_total_day = user.qa_idle_total_day + qa_idle_total_day
			# user.total_days = tot + int(total_day)
			item_to_remove = task_name + " - " + task_item.task_name
			item_to_remove_parent = task_name

			# print("PARENT TASK NAME : ", item_to_remove_parent)

			if any(row.task_name == item_to_remove for row in parent.task):
				parent.task = [row for row in parent.task if row.task_name != item_to_remove and row.task_name != item_to_remove_parent]
				parent.save()

			# if any(row.task_name+ " - " +task_item.task_name == item_to_remove_parent for row in parent.task):
			# 	parent.save()

			parent.save()

			# user.db_update()
	else:
		if status == "Completed" :
			# user.weight = weights + weight
			# user.qa_idle_total_day = qa_idle_day + qa_idle_total_day
			# user.total_days = tot + int(total_day)
			if task_name not in [row.task_name for row in parent.task]:
				parent.append(
										"task", {"doctype": "SD Data Report Item", "task_name":  task_name,"task_weight":weight,"days":total_day,"is_parent":is_parent, 'is_subtask' : False}
														)
				# print(task_name)
				parent.save()
				# user.db_update()

		elif status != "Completed":
			# user.weight = weights + weight
			# user.qa_idle_total_day = qa_idle_day - qa_idle_total_day
			# user.total_days = tot + int(total_day)
			item_to_remove = task_item.task_name
			# print("ITEM TO REMOVE : ",item_to_remove)

			if any(row.task_name == item_to_remove for row in parent.task):
				parent.task = [row for row in parent.task if row.task_name != item_to_remove]
				parent.save()

			parent.save()

			# user.db_update()
		# user.save()
	# else:
	# 	print("blm ada")

	# 	print(user.name)
	# 	user.db_insert()


	# 	weights, name = frappe.db.get_value('SD Data Report',{'employee_name':employee_name,'project_name': project},['weight','name'])
	# 	# print(user.weight)

	# 	user.name = name
	# 	user.branch = branch
	# 	user.total_days = total_day
	# 	user.weight = weight
	# 	parent = frappe.get_doc("SD Data Report", user.name)

	# 	if int(has_sub_task) > 0:
	# 		if task_name + " - " +task_item.task_name not in [row.task_name for row in parent.task]:
	# 			# user.weight = weights + weight
	# 			parent.append(
	# 									"task", {"doctype": "SD Data Report Item", "task_name":  task_name + " - " +task_item.task_name}
	# 													)
	# 			parent.save()
	# 			user.db_update()
	# 	else:
	# 		if task_item.task_name not in [row.task_name for row in parent.task]:
	# 			# user.weight = weights + weight
	# 			parent.append(
	# 									"task", {"doctype": "SD Data Report Item", "task_name":  task_name}
	# 													)
	# 			parent.save()


	# 			user.db_update()


def update_employee_weight2(employee_name,project,weight,branch,total_day,subject,task_name,has_sub_task,status):
	user = frappe.get_doc(doctype='SD Data Report', employee_name=employee_name,project_name=project, branch=branch, total_days=total_day)
	task_item = frappe.get_doc(doctype='SD Data Report Item', task_name=subject)

	# print("PROJECT NAME : ", user.project_name)
	# print(task_item)
	# project = frappe.get_doc({"doctype":"SD Data Report", "employee_name":employee_name, "project":project})
	if frappe.db.exists({"doctype": "SD Data Report", "employee_name": employee_name, "project_name": project}):
		# print("udah ada")
		weights, name = frappe.db.get_value('SD Data Report',{'employee_name':employee_name,'project_name': project},['weight','name'])
		user.name = name
		user.branch = branch
		user.total_days = total_day

		parent = frappe.get_doc("SD Data Report", user.name)
		if int(has_sub_task) > 0:
			if task_name + " - " +task_item.task_name not in [row.task_name for row in parent.task]:
				user.weight = weights + weight
				parent.append(
										"task", {"doctype": "SD Data Report Item", "task_name":  task_name + " - " +task_item.task_name}
														)
				parent.save()
				user.db_update()

			elif status != "Completed":
				user.weight = weights + weight
				item_to_remove = task_name + " - " + task_item.task_name

				if any(row.task_name == item_to_remove for row in parent.task):
					parent.task = [row for row in parent.task if row.task_name != item_to_remove]
					parent.save()

				parent.save()

				user.db_update()
		else:
			if task_name not in [row.task_name for row in parent.task]:
				user.weight = weights + weight
				parent.append(
										"task", {"doctype": "SD Data Report Item", "task_name":  task_name}
														)
				parent.save()
				user.db_update()

			elif status != "Completed":
				user.weight = weights + weight
				item_to_remove = task_item.task_name
				# print("ITEM TO REMOVE : ",item_to_remove)

				if any(row.task_name == item_to_remove for row in parent.task):
					parent.task = [row for row in parent.task if row.task_name != item_to_remove]
					parent.save()

				parent.save()

				user.db_update()
		# user.save()
	else:
		# print("blm ada")

		# print(user.name)
		user.db_insert()


		weights, name = frappe.db.get_value('SD Data Report',{'employee_name':employee_name,'project_name': project},['weight','name'])
		# print(user.weight)

		user.name = name
		user.branch = branch
		user.total_days = total_day
		user.weight = weight
		parent = frappe.get_doc("SD Data Report", user.name)

		if int(has_sub_task) > 0:
			if task_name + " - " +task_item.task_name not in [row.task_name for row in parent.task]:
				# user.weight = weights + weight
				parent.append(
										"task", {"doctype": "SD Data Report Item", "task_name":  task_name + " - " +task_item.task_name}
														)
				parent.save()
				user.db_update()
		else:
			if task_item.task_name not in [row.task_name for row in parent.task]:
				# user.weight = weights + weight
				parent.append(
										"task", {"doctype": "SD Data Report Item", "task_name":  task_name}
														)
				parent.save()


				user.db_update()

