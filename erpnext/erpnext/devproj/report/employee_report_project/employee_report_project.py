# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.reportview import build_match_conditions

# def execute(filters=None):
# 	if not filters:
# 		filters = {}
# 	elif filters.get("from_date") or filters.get("to_date"):
# 		filters["from_time"] = "00:00:00"
# 		filters["to_time"] = "24:00:00"


# 	columns = get_column()
# 	conditions = get_conditions(filters)
# 	data = get_data(conditions, filters)

# 	return columns, data

def execute(filters=None):

	# if filters.get("team"):
	# 	filters["team"] = "%{0}%".format(filters.get('team'))	

	if filters.get("project_name"):

		# if not filters:
		# 	filters = {}
		# else:
		# 	filters.get("project_name")



		columns = get_column2()
		conditions = get_conditions(filters)
		data = get_data(conditions, filters)

		print(data)

		return columns,data


def get_column():
	return [
		_("Total Weight") + "::120",
		_("User") + "::250",
		_("Projects") + ":Link/Project:150",
		# _("To Datetime") + "::140",
		# _("Hours") + "::70",
		# _("Activity Type") + "::120",
		_("Task Taken") + ":Link/Task:100",
		_("Task") + "::500",
		_("Completed On") + "::200",
		# _("Project") + ":Link/Project:120",
		# _("Status") + "::70",
		# _("Weight") + "::150",
	]

def get_column2():
	return [
		{"fieldname": "Total_Weight", "fieldtype": "", "label": _("Total Weight"), "width": 120,"height":150},
		{"fieldname": "User", "fieldtype": "", "label": _("User"),"height":150, "width": 200},
		{"fieldname": "Team", "fieldtype": "", "label": _("Team"),"height":150, "width": 150,"align": "left"},
		{"fieldname": "project", "fieldtype": "", "label": _("Projects"),"height":150, "width": 150},
		{"fieldname": "Total_Task", "fieldtype": "", "label": _("Task Taken")},
		{"fieldname": "Task", "fieldtype": "", "label": _("Task"),"height":500, "width": 350},
		{"fieldname": "Completed_On", "fieldtype": "", "label": _("Completed On"),"height":150, "width": 150,"align": "left"},

	]


def get_data(conditions,filters):
	report = frappe.db.sql(
		"""SELECT
		sum(task_weight) as Total_Weight,
		CONCAT(
        IFNULL(tabEmployee.first_name, ''),
        ' ',
        IFNULL(tabEmployee.middle_name, ''),
        ' ',
        IFNULL(tabEmployee.last_name, '')
   		) as User,
		tabEmployee.branch,
		tabTask.project,
		count(*) as Total_Task, 
		group_concat(tabTask.name SEPARATOR '<br/>') as Task,
		group_concat(completed_on SEPARATOR '<br/>') as Completed_On
		FROM 
		tabTask,
    	JSON_TABLE(`tabTask`._assign,"$[*]" COLUMNS(User VARCHAR(30) PATH "$")) alias_table, tabEmployee
		WHERE tabTask._assign IS NOT NULL AND alias_table.User COLLATE utf8mb4_unicode_ci = tabEmployee.user_id
		AND  %s GROUP BY tabTask.project,
    alias_table.User""" % (conditions),filters, as_list=1)

	return report

def get_conditions(filters):
	conditions = "`tabTask`.docstatus = 0"
	print("PROJECT NAME : ", filters.get("project_name"))
	if filters.get("project_name"):
		conditions += " and `tabTask`.project = %(project_name)s"
	if filters.get("team"):
		conditions += " and `tabEmployee`.branch = %(team)s"

	match_conditions = build_match_conditions("Task")
	if match_conditions:
		conditions += " and %s" % match_conditions

	return conditions

# def get_data2(conditions, filters):
# 	time_sheet = frappe.db.sql(
# 		"""SELECT 
# 		`tabSD Timesheets`.start_date, 
# 		`tabSD Timesheets`.name, 
# 		`tabSD Timesheets`.employee_name,
# 		`tabTimesheet Detail`.from_time, 
# 		`tabTimesheet Detail`.to_time, 
# 		`tabTimesheet Detail`.hours_count,
# 		`tabTimesheet Detail`.task, 
# 		`tabTimesheet Detail`.project
# 		FROM 
# 		`tabTimesheet Detail`, 
# 		`tabSD Timesheets` 
# 		WHERE 
# 		`tabTimesheet Detail`.parent = `tabSD Timesheets`.name 
# 		AND %s 

# 		ORDER BY `tabSD Timesheets`.start_date""" % (conditions), filters, as_list=1)

# 	return time_sheet
