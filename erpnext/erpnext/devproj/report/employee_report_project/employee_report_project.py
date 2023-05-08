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

	if filters.get("project_name"):
		if not filters:
			filters = {}
		else:
			filters.get("project_name")

		columns = get_column()
		conditions = get_conditions(filters)
		data = get_data(conditions, filters)

		print(data)

		return columns,data


def get_column():
	return [
		_("Total Weight") + "::120",
		_("User") + "::250",
		_("Projects") + ":Link/Project:150",
		# _("From Datetime") + "::140",
		# _("To Datetime") + "::140",
		# _("Hours") + "::70",
		# _("Activity Type") + "::120",
		# _("Task") + ":Link/Task:150",
		# _("Project") + ":Link/Project:120",
		# _("Status") + "::70",
		# _("Weight") + "::150",
	]



def get_data(conditions,filters):
	report = frappe.db.sql(
		"""SELECT
		sum(task_weight) as Total_Weight,
		User,
		project
		FROM 
		tabTask,
    	JSON_TABLE(`tabTask`._assign,"$[*]" COLUMNS(User VARCHAR(30) PATH "$")) alias_table
		WHERE _assign IS NOT NULL
		AND %s
		GROUP BY User""" % (conditions),filters, as_list=1)

	return report

def get_conditions(filters):
	conditions = "`tabTask`.docstatus = 0"
	print("PROJECT NAME : ", filters.get("project_name"))
	if filters.get("project_name"):
		conditions += f" and `tabTask`.project = '{filters.get('project_name')}'"

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
