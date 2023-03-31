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
		self.validate_dates()
		self.validate_parent_expected_end_date()
		self.validate_parent_project_dates()
		self.validate_progress()
		self.validate_status()
		# self.validate_status_child()
		self.validate_on_going_sprint()
		self.update_depends_on()
		self.validate_dependencies_for_template_task()
		self.validate_completed_on()

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



	def validate_status_child(self):

		if self.status != self.get_db_value("status") and self.status == "Open":
			for d in self.depends_on:
				task_subject = frappe.db.get_value('Task', d.task, ['subject'])
				frappe.db.set_value('Task', task_subject, 'status', 'Open')



	def validate_on_going_sprint(self):

		events = frappe.get_list(
						"Event", filters={"status": "Open"}, fields=["name", "starts_on"]
					)
		for event in events:
			if (event.starts_on and getdate(event.starts_on) == getdate(nowdate())):
				# ongoing=frappe.db.set_value('Task', event.name, 'ongoing_sprint', event.name)
				self.ongoing_sprint = frappe.db.get_value("Event",event.name,'name')
				# task_subject = frappe.db.get_value('Event', event.name, 'name')
				# print(task_subject)
				# asd =frappe.db.set_value('Task', task_subject, 'ongoing_sprint', event.name)
				# print(asd)
				# print(ongoing_sprint)

		arr = [] 
		for items in self.multi_sprint:
			doc = frappe.get_doc('Event', items.sprint_id)
			arr.append(doc.starts_on)
			# if (doc.status == "Open"):
			# 	if (doc.starts_on and getdate(doc.starts_on) == getdate(nowdate())):
			# 		# self.ongoing_sprint = doc
			# 		# print(doc)
			# 		# min_val = max(arr)
			# 		self.ongoing_sprint = frappe.db.get_value("Event",doc.name,'name')
			# print("Minimum value in the array:", min_val)

	def validate_status(self):
		if self.is_template and self.status != "Template":
			self.status = "Template"
		if self.status != self.get_db_value("status") and self.status == "Completed":
			for d in self.depends_on:
				if frappe.db.get_value("Task", d.task, "status") not in ("Completed", "Cancelled"):
					frappe.throw(
						_(
							"Cannot complete task {0} as its dependant task {1} are not completed / cancelled."
						).format(frappe.bold(self.name), frappe.bold(d.task))
					)

			close_all_assignments(self.doctype, self.name)


	days = 0
	d1 = 0
	d2 = 0

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
			# delta = self.d2 - self.d1

		self.daydiff = self.d2.weekday() - self.d1.weekday()

		self.days = ((self.d2-self.d1).days - self.daydiff) / 7 * 5 + min(self.daydiff,5) - (max(self.d2.weekday() - 4, 0) % 5) + 1

		self.strdays = str(self.days).split('.')[0]

		self.duration = self.days

	def validate_progress(self):

		if flt(self.progress or 0) > 100:
			frappe.throw(_("Progress % for a task cannot be more than 100."))

		if flt(self.individual_progress or 0) > 100:
			# frappe.throw(_("Individual Progress % for a task cannot be more than 100."))
			frappe.throw(_("Your Individual Progress is {0}. Individual Progress {1} for a task cannot be more than "+ "'{1}'")
				.format(frappe.bold(f'{self.individual_progress} %'),frappe.bold("%"),frappe.bold("100%")))

		if self.status == "Open":

			# self.exp_start_date = ""
			self.duration = 0

			self.validate_duration()

		if self.status == "Completed":
			self.progress = 100

		if self.status == "Working":

			self.progress = 0

			# self.exp_start_date = datetime.now().date()
			if flt(self.exp_start_date == None):
				frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Expected Start Date")))

			# start_date = self.exp_start_date

			# days_to_add = 7

			# current_date = start_date

			# while days_to_add > 0:
			# 	current_date += timedelta(days=1)
			# 	if current_date.weekday() < 5:
			# 		days_to_add -= 1

			# result_date = current_date

			# self.exp_end_date = result_date

			self.start_date = str(self.exp_start_date)
			self.end_date = str(self.exp_end_date)

			self.d1 = datetime.strptime(self.start_date, "%Y-%m-%d")

			if flt(self.exp_end_date == None):
				frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Expected End Date")))
			else:
				self.d2 = datetime.strptime(self.end_date, "%Y-%m-%d")
			# delta = self.d2 - self.d1

			self.daydiff = self.d2.weekday() - self.d1.weekday()

			self.days = ((self.d2-self.d1).days - self.daydiff) / 7 * 5 + min(self.daydiff,5) - (max(self.d2.weekday() - 4, 0) % 5) + 1

			self.strdays = str(self.days).split('.')[0]

			self.duration = self.days

		if self.status == "Pending Review":
			if flt(self.individual_progress or 0) < 100:
				# frappe.throw(_("Individual Progress % for a task cannot be less than 100. Please make sure your individual progress is 100% finished"))
				frappe.throw(_("Your Individual Progress is {0}. Individual Progress {1} for a task cannot be more than "+ "'{2}'")
				.format(frappe.bold(f'{self.individual_progress} %'),frappe.bold("%"),frappe.bold("100%")))
			else:
				self.progress = 50

		if self.status == "QA Testing":

			self.progress = 80

			# start_date = datetime.now().date()

			# days_to_add = 10

			# current_date = start_date

			# while days_to_add > 0:
			# 	current_date += timedelta(days=1)
			# 	if current_date.weekday() < 5:
			# 		days_to_add -= 1

			# result_date = current_date

			# self.exp_end_date = result_date

			# self.start_date = str(self.exp_start_date)
			# self.end_date = str(self.exp_end_date)

			# self.d1 = datetime.strptime(self.start_date, "%Y-%m-%d")

			# if flt(self.exp_end_date == None):
			# 	frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Expected End Date")))
			# else:
			# 	self.d2 = datetime.strptime(self.end_date, "%Y-%m-%d")
			# # delta = self.d2 - self.d1

			# self.daydiff = self.d2.weekday() - self.d1.weekday()

			# self.days = ((self.d2-self.d1).days - self.daydiff) / 7 * 5 + min(self.daydiff,5) - (max(self.d2.weekday() - 4, 0) % 5) + 1

			# strdays = str(self.days).split('.')[0]

			# self.duration = self.days

		if self.status == "QA Integration Testing":

			self.progress = 90

			#1. harus get doc Event sprint yg sedang open, kemudian get starts_on dan ends_on nya kapan
			#2. selisihkan start time dengan ends_on sprint yg sedang berjalan

			# start_date = datetime.now().date()

			# days_to_add = 10

			# current_date = start_date

			# while days_to_add > 0:
			# 	current_date += timedelta(days=1)
			# 	if current_date.weekday() < 5:
			# 		days_to_add -= 1

			# result_date = current_date

			# self.exp_end_date = result_date

			# self.start_date = str(self.exp_start_date)
			# self.end_date = str(self.exp_end_date)

			# self.d1 = datetime.strptime(self.start_date, "%Y-%m-%d")

			# if flt(self.exp_end_date == None):
			# 	frappe.throw(_("{0} Cannot be empty").format(frappe.bold("Expected End Date")))
			# else:
			# 	self.d2 = datetime.strptime(self.end_date, "%Y-%m-%d")
			# # delta = self.d2 - self.d1

			# self.daydiff = self.d2.weekday() - self.d1.weekday()

			# self.days = ((self.d2-self.d1).days - self.daydiff) / 7 * 5 + min(self.daydiff,5) - (max(self.d2.weekday() - 4, 0) % 5) + 1

			# strdays = str(self.days).split('.')[0]

			# self.duration = self.days

		if self.status == "Cancelled":

			self.progress = 0

			# self.exp_end_date = ""

			# self.exp_start_date = ""

		self.progress = str(self.progress).split('.')[0]
		if (self.is_group != True):
			if self.priority == "Low":
				# if flt(self.task_weight) > 2 or flt(self.task_weight) < 1:
				if flt(self.task_weight) > 10 or flt(self.task_weight) < 1:
					# frappe.throw(_("Please set Weight value for " + "'" + self.priority + "'" + " " +"Priority between 1 to 2"))
					frappe.throw(_("Please set {0} value for "+ "'{1}'"+ " Priority between {2}")
					.format(frappe.bold("Weight"),frappe.bold(self.priority), frappe.bold("1 to 10")))

				if flt(self.days) > 10:
					frappe.throw(_("Difference between Start to End date is {0}, for "+ "'{1}'"+ " priority is {2}")
					.format(frappe.bold(f'{self.strdays} days'),frappe.bold(self.priority), frappe.bold("< 10 days")))

			if self.priority == "Medium":
				if self.status != "QA Testing" and self.status != "QA Integration Testing":
					# if flt(self.task_weight) > 5 or flt(self.task_weight) < 3:
					if flt(self.task_weight) > 10 or flt(self.task_weight) < 1:

						# frappe.throw(_("Please set Weight value for " + "'" + self.priority + "'" + " " +"Priority between 3 to 5"))
						frappe.throw(_("Please set {0} value for "+ "'{1}'"+ " Priority between {2}")
					.format(frappe.bold("Weight"),frappe.bold(self.priority), frappe.bold("1 to 10")))

					if flt(self.days) > 7:
						frappe.throw(_("Difference between Start to End date is {0}, for "+ "'{1}'"+ " priority is {2}")
						.format(frappe.bold(f'{self.strdays} days'),frappe.bold(self.priority), frappe.bold("< 7 days")))


			if self.priority == "High":
				# if flt(self.task_weight) > 8 or flt(self.task_weight) < 6:
				if flt(self.task_weight) > 10 or flt(self.task_weight) < 1:

					# frappe.throw(_("Please set Weight value for " + "'" + self.priority + "'" + " " +"Priority between 6 to 8"))
					frappe.throw(_("Please set {0} value for "+ "'{1}'"+ " Priority between {2}")
					.format(frappe.bold("Weight"),frappe.bold(self.priority), frappe.bold("1 to 10")))

				if flt(self.days) > 5:
					frappe.throw(_("Difference between Start to End date is {0}, for "+ "'{1}'"+ " priority is {2}")
					.format(frappe.bold(f'{self.strdays} days'),frappe.bold(self.priority), frappe.bold("< 7 days")))


			if self.priority == "Urgent":
				# if flt(self.task_weight) > 10 or flt(self.task_weight) < 9:
				if flt(self.task_weight) > 10 or flt(self.task_weight) < 1:

					# frappe.throw(_("Please set Weight value for " + "'" + self.priority + "'" + " " +"Priority between 9 to 10"))
					frappe.throw(_("Please set {0} value for "+ "'{1}'"+ " Priority between {2}")
					.format(frappe.bold("Weight"),frappe.bold(self.priority), frappe.bold("1 to 10")))

				if flt(self.days) > 2:
					frappe.throw(_("Difference between Start to End date is {0}, for "+ "'{1}'"+ " priority is {2}")
					.format(frappe.bold(f'{self.strdays} days'),frappe.bold(self.priority), frappe.bold("< 3 days")))

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
		self.unassign_todo()
		self.populate_depends_on()

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

	def populate_depends_on(self):
		if self.parent_task:
			parent = frappe.get_doc("Task", self.parent_task)
			if self.name not in [row.task for row in parent.depends_on]:
				parent.append(
					"depends_on", {"doctype": "Task Depends On", "task": self.name, "subject": self.subject}
				)
				parent.save()

		if self.ongoing_sprint:
			# print(self.ongoing_sprint)
			parent = frappe.get_doc("Event", self.ongoing_sprint)
			if self.name not in [row.task_id for row in parent.task_list]:
				parent.append(
					"task_list", {"doctype": "Sprint Task List", "task_id": self.name}
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
		if self.status not in ("Cancelled", "Completed") and self.exp_end_date:
			from datetime import datetime

			if self.exp_end_date < datetime.now().date():
				self.db_set("status", "Overdue", update_modified=False)
				self.update_project()


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
		filters={"status": ["not in", ["Cancelled", "Completed"]]},
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

