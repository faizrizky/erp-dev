# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import json

import frappe
from frappe import _, throw
from frappe.desk.form.assign_to import clear, close_all_assignments
from frappe.model.mapper import get_mapped_doc
from frappe.utils import add_days, cstr, date_diff, flt, get_link_to_form, getdate, today
from frappe.utils.nestedset import NestedSet
from datetime import datetime
from datetime import timedelta
from frappe.utils import nowdate
from frappe import db



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
		# self.validate_sprint()
		self.validate_sub_task()
		self.validate_completed_task()
		self.update_depends_on()
		self.validate_dependencies_for_template_task()
		self.validate_duration_programmer(self.exp_start_date,self.review_date)
		self.validate_duration_qa(self.exp_start_date,self.completed_on,self.qa_open_date,self.qa_testing_date)[0]
			
		self.handle_completed_task()
		# self.calculate_total_day_on_data_report()
		# self.get_exp_dates_from_sd_data_report()

	def get_exp_dates_from_sd_data_report(self):
		subject = frappe.db.get_value('Task', self.name, '_assign')

		if subject is not None and self.review_date is not None:
			result = json.loads(subject)
			exp_start_dates = []  # Initialize as empty lists before the loop
			exp_end_dates = []  # Initialize as empty lists before the loop
			
			for emp in result:
				emp_name = frappe.db.get_value('User', emp, 'full_name')
				sd_data_report = frappe.get_doc('SD Data Report', {'employee_name': emp_name, 'project_name': self.project})

				# Access the list of child table rows (SD Data Report Item) from the SD Data Report document
				sd_data_report_items = sd_data_report.get('task')

				for item in sd_data_report_items:
					task_name = item.task_name.split('-')[0].strip()

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

			# Handle the case when the smallest_exp_start_date and largest_exp_end_date are 0 or None
			if smallest_exp_start_date is None or smallest_exp_start_date == 0:
				smallest_exp_start_date = "No valid start date found."
			if largest_exp_end_date is None or largest_exp_end_date == 0:
				largest_exp_end_date = "No valid end date found."


			print("Smallest exp_start_date:", smallest_exp_start_date)
			print("Largest exp_end_date:", largest_exp_end_date)

		return exp_start_dates, exp_end_dates


	def calculate_total_day_on_data_report(self):
		subject = frappe.db.get_value('Task', self.name, '_assign')
		if self.status == "Completed":
			if subject is not None and self.review_date is not None:
				result = json.loads(subject)
				for emp in result:
					emp_name = frappe.db.get_value('User', emp, 'full_name')

					# Get the 'SD Data Report' document by name
					doc = frappe.get_doc('SD Data Report', {'employee_name': emp_name, 'project_name': self.project})

					# Access the value of the 'total_days', 'start_date', and 'end_date' fields directly from the document
					start_date_value = doc.start_date
					end_date_value = doc.end_date

					# Perform the update with the calculated value
					frappe.db.set_value('SD Data Report',
										{'employee_name': emp_name, 'project_name': self.project},
										'total_days', self.validate_duration_programmer(start_date_value, end_date_value))
			else:
				frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Review Date")))

	def validate_working_date(self, branch):
		subject = frappe.db.get_value('Task', self.name, '_assign')
		
		if subject is not None:
				result = json.loads(subject)
				for emp in result:
					emp_name = frappe.db.get_value('User', emp, 'full_name')

					

					# Get the 'SD Data Report' document by name
					doc = frappe.get_doc('SD Data Report', {'employee_name': emp_name, 'project_name': self.project})

					start_date = doc.start_date
					end_date = doc.end_date

					# print("BRANCH : ", doc.employee_name)
					# print("START DATE FROM DATA REPORT : ", doc.start_date)
					# print("END DATE FROM DATA REPORT : ", doc.end_date)
				
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

				# print("INI BRANCH CHECKER : ",branch_checker)

				# print("BRANCH : ",branch)
				# print("COMPLETION : ",d.completion)

				#Check Print
				# print("status before : ", status_before)
				# print("status : ", self.status)
				# print(employee_name," ",branch)
				# print("JUMLAH CHECKER NAME : ", jumlah_total_elemen_checker_name)


				# if d.completion == 1 and d.qa_completion == 1 and self.status == "Completed":
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

							# self.validate_working_date(branch)






					# update_employee_weight(emp_name,self.project,-self.task_weight,branch, self.programmer_total_day,self.name,self.name,len(self.sub_task),self.status)
					# update_employee_weight(emp_name,self.project,-self.task_weight,branch, self.qa_total_day,self.name,self.name,len(self.sub_task),self.status)


			# query = """
			# 		SELECT _assign FROM `tabTask` WHERE tabTask.name = %(task_name)s
			# 		"""

			# # Execute the query with parameters
			# task_name = self.name
			# results = []
			# # frappe.db.sql(query, {"task_name": task_name}, as_dict=True, callback=lambda row: results.append(row))
			# query_results = frappe.db.sql(query, {"task_name": task_name}, as_dict=True)

			# for row in query_results:
			# 	print(row)
			# 	results.append(row)
			# # print(results)

			# # Process the results
			# if results:
			# 	first_row = results[0]
			# 	print(first_row)
			# 	# if assign_array:

       			# 	 print(", ".join(str(element) for element in assign_array))

		# employee_name_query = """
		# 	SELECT employee_name FROM `tabEmployee` WHERE tabEmployee.user_id = %(employee_name)s
		# 	"""
		# employee_name = row._assign
		# results = frappe.db.sql(employee_name_query, {"employee_name": employee_name}, as_dict=True)
		# print(results)
		# employee_name = frappe.db.get_value("Employee", d.employee_name, "employee_name")
		# print(employee_name)
		# checker_name = frappe.db.get_value("Employee", d.checker_name, "employee_name")
		# branch = frappe.db.get_value("Employee", d.employee_name, "branch")
		# if self.status == "Completed":
		# 	update_employee_weight(employee_name,self.project,self.task_weight,branch, self.programmer_total_day,d.subject,self.name,len(self.sub_task))

		# 	update_employee_weight(checker_name,self.project,d.qa_weight,branch, self.qa_total_day,d.subject,self.name,len(self.sub_task))



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
			frappe.throw(_("{0} Cannot be greater than {1}").format(frappe.bold("QA Start Working Date"),frappe.bold("QA End Working Date")))

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

	# def before_save(doc):
	#     # Set the "read-only" flag to True if a certain condition is met
	# 	if doc.some_field == "Some Value":
	# 		doc.read_only = 1

	def validate_sub_task(self):

		if self.is_group == 1 and len(self.sub_task) > 0 :
			frappe.throw(_("{0} cannot have {1}")
							.format(frappe.bold("Parent Task"), frappe.bold("Sub Task")))
		arr = []
		arr_qa = []
		check_val = dict([])
		has_error = []

		if len(self.sub_task) > 0:
			for d in self.sub_task:
				# check if the same pa aji
				if d.subject not in check_val :
					check_val[d.subject] = 1
				else:
					check_val[d.subject] += 1

				if check_val[d.subject] <= 1:

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
					has_error.append(d.subject)

			if len(has_error) > 0 : 
				frappe.throw(_("{0} name in {1} cannot be same").format(frappe.bold((" , ").join(has_error)),frappe.bold("Sub Task Table")))

			percentage_programmer = (count_true_programmer / len(self.sub_task)) * 100
			percentage_qa = (count_true_qa / len(self.sub_task)) * 100

			self.individual_progress = percentage_programmer
			self.qa_progress = percentage_qa

			# print("Total Percentage : "+ str(percentage))

		else:
			print("Manual Percentage")

		# # if d.task and d.task not in depends_on_tasks:
		# # 	depends_on_tasks += d.task + ","

		# boolean_arr = [d.completion == True for d.completion in self.sub_task]
		# print(boolean_arr) 
		# # Menghitung jumlah True dalam array boolean
		# count_true = sum(boolean_arr)
		# print(count_true)  # Output: 3
		# # percentage = (count_true / len(d)) * 100
		# # print(percentage)  # Output: 60.0


	def validate_status_child(self):

		if self.status != self.get_db_value("status") and self.status == "Open":
			for d in self.depends_on:
				task_subject = frappe.db.get_value('Task', d.task, ['subject'])
				frappe.db.set_value('Task', task_subject, 'status', 'Open')


	def validate_on_going_sprint(self):

		# events = frappe.get_list(	
		# 				"Event", filters={"status": "Open"}, fields=["name", "starts_on"]
		# 			)
		# for event in events:
		# 	if (event.starts_on and getdate(event.starts_on) == getdate(nowdate())):
		# 		# ongoing=frappe.db.set_value('Task', event.name, 'ongoing_sprint', event.name)
		# 		self.ongoing_sprint = frappe.db.get_value("Event",event.name,'name')
		# 		# task_subject = frappe.db.get_value('Event', event.name, 'name')
		# 		# print(task_subject)
		# 		# asd =frappe.db.set_value('Task', task_subject, 'ongoing_sprint', event.name)
		# 		# print(asd)
		# 		# print(ongoing_sprint)
		# print(self.multi_sprint.items());

		# event = frappe.db.get_list('Event', pluck='starts_on',
		# filters={
		# 	# 'starts_on': ['<=', getdate(nowdate())],
		# 	"name" : ["in", self.multi_sprint]
		# },
		# 				fields=['starts_on', 'name'],
		# 				order_by='starts_on desc',
		# 				page_length=2,
		# 				as_list=False
		# 				)
		# assigment_sprint = frappe.db.get_list('Assignment Sprint', 
		# filters={
		# 	'parent': self.name
		# },
		# 				fields=['parent', 'name', 'sprint_id'],
		# 				page_length=10000,
		# 				as_list=False
		# 				)


		# self.exp_start_date = event[1] if event[1] else event[0]

		arr = [] 
		for items in self.multi_sprint:
			doc = frappe.get_doc('Event', items.sprint_id)

			arr.append(doc.starts_on)
			arr.append(doc.ends_on)

		if (len(arr) <= 0):
			frappe.throw(_("You need to fill {0} field in Category Sprint to continue").format(frappe.bold("Sprint")))

		# print(min(arr),max(arr))
		self.exp_start_date =min(arr)
		self.exp_end_date = max(arr)



		# for items in self.multi_sprint:
		# 	doc = frappe.get_doc('Event', items.sprint_id)
		# 	arr.append(doc.starts_on)
		# 	if (doc.ends_on):
		# 		if (getdate(doc.ends_on) >= getdate(nowdate())):
		# 			# self.ongoing_sprint = doc
		# 			# print("ends on",doc.ends_on)
		# 			# min_val = max(arr)
		# 			# self.ongoing_sprint = frappe.db.get_value("Event",doc.name,'name')
		# 			self.exp_end_date = frappe.db.get_value("Event",doc.name,'ends_on')
		# 		elif (doc.starts_on):

		# 			if (getdate(doc.starts_on) <= getdate(nowdate())):
		# 				# self.ongoing_sprint = doc
		# 				print(doc)
		# 				# min_val = max(arr)
		# 				# self.ongoing_sprint = frappe.db.get_value("Event",doc.name,'name')
		# 				self.exp_start_date = frappe.db.get_value("Event",doc.name,'starts_on')
		# 				self.exp_end_date = frappe.db.get_value("Event",doc.name,'ends_on')




		# 	# print("Minimum value in the array:", min_val)
		# if (len(arr) <= 0):
		# 	# 	# self.ongoing_sprint = ""
		# 	# self.exp_start_date = ""
		# 	# self.exp_end_date = ""
		# 	frappe.throw(_("You need to fill {0} field in Category Sprint to continue").format(frappe.bold("Sprint")))



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
			self.completed_on = getdate(today())

	days = 0
	d1 = 0
	d2 = 0

	def validate_duration_integration(self):
		if self.start_date_integration is not None and self.end_date_integration is not None:
			self.integration_start = str(self.start_date_integration)
			self.integration_end = str(self.end_date_integration)

			self.integration1 = datetime.strptime(self.integration_start, "%Y-%m-%d")
			self.integration2 = datetime.strptime(self.integration_end, "%Y-%m-%d")

			self.daydiffIntegration = self.integration2.weekday() - self.integration1.weekday()
			self.daysIntegration = ((self.integration2-self.integration1).days - self.daydiffIntegration) / 7 * 5 + min(self.daydiffIntegration,5) - (max(self.integration2.weekday() - 4, 0) % 5) + 1

			if self.daysIntegration < 0:
				self.total_day_integration = 0
			else:
				self.total_day_integration = self.daysIntegration


	def validate_duration_qa(self, exp_start_date, completed_on, qa_open_date, qa_testing_date):
		qa_total_idle_day = 0
		if self.qa_total_day is None:
			self.qa_total_day = 0

		if self.review_date is not None and self.qa_open_date is not None and self.qa_testing_date is not None and exp_start_date is not None and completed_on is not None:

			self.start_date = str(self.exp_start_date)
			self.end_date = str(self.completed_on)

			self.d1 = datetime.strptime(self.start_date, "%Y-%m-%d")
			self.d2 = datetime.strptime(self.end_date, "%Y-%m-%d")
			self.daydiff = self.d2.weekday() - self.d1.weekday()

			self.qa_total_day = ((self.d2 - self.d1).days - self.daydiff) / 7 * 5 + min(self.daydiff, 5) - (max(self.d2.weekday() - 4, 0) % 5) + 1

			self.qa_start = datetime.strptime(str(qa_open_date), "%Y-%m-%d")
			self.qa_end = datetime.strptime(str(qa_testing_date), "%Y-%m-%d")
			self.daydiff = self.qa_end.weekday() - self.qa_start.weekday()

			qa_total_idle_day = ((self.qa_end - self.qa_start).days - self.daydiff) / 7 * 5 + min(self.daydiff, 5) - (max(self.qa_end.weekday() - 4, 0) % 5) + 1

			self.qa_total_day = self.qa_total_day - int(self.programmer_total_day) - int(qa_total_idle_day)
			print("QA TOTAL DAY : ", self.qa_total_day)
			if self.qa_total_day < 0:
				self.qa_total_day = 0
		
		# print("QA TOTAL DAY : ", self.qa_total_day)
		# print("QA TOTAL IDLE DAY : ", self.qa_total_idle_day)
		return self.qa_total_day, qa_total_idle_day


	def validate_duration_programmer(self,start_date,end_date):

		# print("INI START DATE : ",start_date)
		# print("INI REVIEW DATE : ",end_date)
		if self.programmer_total_day is None:
			self.programmer_total_day = 0
		
		if self.status == "Pending Review" or self.status == "Completed":
			if self.review_date is not None:
				# print("START DATE : ", self.exp_start_date)
				# print("START DATE : ", self.start_date)
				# print("END DATE : ", self.end_date)
				self.date_start = str(start_date)
				self.end_date = str(end_date)

				self.d1 = datetime.strptime(self.date_start, "%Y-%m-%d")
				self.d2 = datetime.strptime(self.end_date, "%Y-%m-%d")

				self.daydiff = self.d2.weekday() - self.d1.weekday()

				self.total_day = ((self.d2-self.d1).days - self.daydiff) / 7 * 5 + min(self.daydiff,5) - (max(self.d2.weekday() - 4, 0) % 5) + 1

				if self.total_day < 0:
					self.total_day = 0

				if self.status == "Pending Review":
					self.programmer_total_day = self.total_day
					return self.programmer_total_day
				elif self.status == "Completed":
					return self.total_day
					
				# print("TOTAL HARINYA COY : ",self.programmer_total_day)
				

				# self.strdays = str(self.days).split('.')[0]

				# self.duration = self.days

				# self.programmer_total_day = self.duration

				# print("TOTAL DAYS PROGRAMMER: ", self.duration)
			else:
				frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Review Date")))

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

		checker_name_list = [x for x in self.sub_task if x.checker_name != "" and x.checker_name != None]
		# print(json.dumps([x.checker_name for x in self.sub_task]))
		jumlah_total_elemen_checker_name = len(checker_name_list)	

		if flt(self.progress or 0) > 100:
			frappe.throw(_("Progress % for a task cannot be more than 100."))

		if flt(self.individual_progress or 0) > 100 or flt(self.individual_progress) < 0:
			# frappe.throw(_("Individual Progress % for a task cannot be more than 100."))
			frappe.throw(_("Your Individual Progress is {0}. Individual Progress {1} for a task cannot be more than "+ "'{2}' or less than "+ "'{3}'")
				.format(frappe.bold(f'{self.individual_progress} %'),frappe.bold("%"),frappe.bold("100%"),frappe.bold("0%")))

		if flt(self.qa_progress or 0) > 100 or flt(self.qa_progress) < 0:
			# frappe.throw(_("Individual Progress % for a task cannot be more than 100."))
			frappe.throw(_("Your QA Task Progress is {0}. QA Task Progress {1} for a task cannot be more than "+ "'{2}' or less than "+ "'{3}'")
				.format(frappe.bold(f'{self.qa_progress} %'),frappe.bold("%"),frappe.bold("100%"),frappe.bold("0%")))

		if self.status == "Open":

			# self.exp_start_date = ""
			self.duration = 0

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
				if self.is_group != True:
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

		if self.status == "Cancelled":

			self.progress = 0

			# self.exp_end_date = ""

			# self.exp_start_date = ""

		self.progress = str(self.progress).split('.')[0]



		# if (self.is_group != True and self.status != "Open"):
		# 	if self.priority == "Low":
		# 		# if flt(self.task_weight) > 2 or flt(self.task_weight) < 1:
		# 		if flt(self.task_weight) > 10 or flt(self.task_weight) < 1:
		# 			# frappe.throw(_("Please set Weight value for " + "'" + self.priority + "'" + " " +"Priority between 1 to 2"))
		# 			frappe.throw(_("Please set {0} value for "+ "'{1}'"+ " Priority between {2}")
		# 			.format(frappe.bold("Weight"),frappe.bold(self.priority), frappe.bold("1 to 10")))

		# 		if flt(self.days) > 10:
		# 			frappe.throw(_("Difference between Start to End date is {0}, for "+ "'{1}'"+ " priority is {2}")
		# 			.format(frappe.bold(f'{self.strdays} days'),frappe.bold(self.priority), frappe.bold("< 10 days")))

		# 	if self.priority == "Medium":
		# 		# if self.status != "QA Testing" and self.status != "QA Integration Testing":
		# 		# if flt(self.task_weight) > 5 or flt(self.task_weight) < 3:
		# 		if flt(self.task_weight) > 10 or flt(self.task_weight) < 1:

		# 			# frappe.throw(_("Please set Weight value for " + "'" + self.priority + "'" + " " +"Priority between 3 to 5"))
		# 			frappe.throw(_("Please set {0} value for "+ "'{1}'"+ " Priority between {2}")
		# 			.format(frappe.bold("Weight"),frappe.bold(self.priority), frappe.bold("1 to 10")))

		# 		if flt(self.days) > 7:
		# 			frappe.throw(_("Difference between Start to End date is {0}, for "+ "'{1}'"+ " priority is {2}")
		# 				.format(frappe.bold(f'{self.strdays} days'),frappe.bold(self.priority), frappe.bold("< 7 days")))


		# 	if self.priority == "High":
		# 		# if flt(self.task_weight) > 8 or flt(self.task_weight) < 6:
		# 		if flt(self.task_weight) > 10 or flt(self.task_weight) < 1:

		# 			# frappe.throw(_("Please set Weight value for " + "'" + self.priority + "'" + " " +"Priority between 6 to 8"))
		# 			frappe.throw(_("Please set {0} value for "+ "'{1}'"+ " Priority between {2}")
		# 			.format(frappe.bold("Weight"),frappe.bold(self.priority), frappe.bold("1 to 10")))

		# 		if flt(self.days) > 5:
		# 			frappe.throw(_("Difference between Start to End date is {0}, for "+ "'{1}'"+ " priority is {2}")
		# 			.format(frappe.bold(f'{self.strdays} days'),frappe.bold(self.priority), frappe.bold("< 7 days")))


		# 	if self.priority == "Urgent":
		# 		# if flt(self.task_weight) > 10 or flt(self.task_weight) < 9:
		# 		if flt(self.task_weight) > 10 or flt(self.task_weight) < 1:

		# 			# frappe.throw(_("Please set Weight value for " + "'" + self.priority + "'" + " " +"Priority between 9 to 10"))
		# 			frappe.throw(_("Please set {0} value for "+ "'{1}'"+ " Priority between {2}")
		# 			.format(frappe.bold("Weight"),frappe.bold(self.priority), frappe.bold("1 to 10")))

		# 		if flt(self.days) > 2:
		# 			frappe.throw(_("Difference between Start to End date is {0}, for "+ "'{1}'"+ " priority is {2}")
		# 			.format(frappe.bold(f'{self.strdays} days'),frappe.bold(self.priority), frappe.bold("< 3 days")))

		# if self.priority == "Medium":


		# 	self.exp_start_date =  datetime.now().date()
		# 	self.exp_end_date = datetime.now() + timedelta(days=1)


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

		
		# if self.ongoing_sprint:
		# 	# frappe.db.set_value("DocType", docname, "fieldname", value_to_set)
		# 	# parent = frappe.db.get_value("Event", {"ongoing_sprint": parent})
		# 	parent = frappe.get_doc("Event", self.ongoing_sprint)
		# 	print(parent)
		# parent.append(
		# 		"task_list", {"doctype": "Sprint Task List", "task_id": self.name}
                #             )
		# parent.save()
		# if self.name not in [row.sprint_id for row in multi_issue_value.multi_sprint]:
		# self.ongoing_sprint.append(
		# 		"multi_sprint", {"doctype": "Assignment Sprint", "sprint_id": self.name}
                #             )
		# self.ongoing_sprint.save()


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
										"task", {"doctype": "SD Data Report Item", "task_name":  task_name + " - " +task_item.task_name,"task_weight":weight,"days":total_day,"is_parent":is_parent}
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
										"task", {"doctype": "SD Data Report Item", "task_name":  task_name,"task_weight":weight,"days":total_day,"is_parent":is_parent}
														)
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
				print("ITEM TO REMOVE : ",item_to_remove)

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
