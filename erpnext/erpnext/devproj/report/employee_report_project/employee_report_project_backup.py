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

	# if filters.get("project_name"):

	# if not filters:
	# 	filters = {}
	# else:
	# 	filters.get("")



	columns = get_column2()
	conditions = get_conditions(filters)
	data = get_data(conditions, filters)

	data2 = get_data2(filters)

	# print("INI ADALAH DATA 2 : ",data2)

	# print(data)

	return columns,data2


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
		{"fieldname": "employee_name", "fieldtype": "", "label": _("User"),"height":150, "width": 200},
		{"fieldname": "branch", "fieldtype": "", "label": _("Team"),"height":150, "width": 150,"align": "left"},
		{"fieldname": "task_name", "fieldtype": "", "label": _("Task (Days)"),"height":500, "width": 350},
		{"fieldname": "task_taken", "fieldtype": "", "label": _("Task Taken")},
		{"fieldname": "total_weight", "fieldtype": "", "label": _("Total Weight"), "width": 120,"height":150},
		{"fieldname": "total_days", "fieldtype": "", "label": _("Total Days"),"height":150, "width": 150,"align": "left"},

	]

def get_data2(filters):
	# report3 = frappe.db.get_list('SD Data Report Item',
	# 	fields=['task_name']
    #     )

	# report2 = frappe.db.get_list('SD Data Report',
	# 	filters={	
    #                 'project': ['=',filters],
    #                 'project': ['!=','']
    #             },

    #         fields=['weight','employee_name', 'branch','task.task_name as who','total_days','project_name','total_days','project_name, GROUP_CONCAT(`who` SEPARATOR "<br />") AS task_name'],
    #         order_by='weight desc',
    #        	group_by = 'employee_name',
    #         # start=10,
    #         page_length=10000000,
    #         # as_list=True
    #     )
	result = frappe.db.get_all(
            "SD Data Report",
            fields=["name", "total_weight", "employee_name", "branch", "task.task_name"],
            filters=filters,
           	as_list=False,
            debug=False,
           	group_by="employee_name",
           	order_by="total_weight desc"
         			# conditions=get_conditions(filters)
	)
	# print(filters.get("team"))

	data = []

	for row in result:
		print(row.branch)

		parent_doc = frappe.get_doc("SD Data Report", row.name)
		if hasattr(parent_doc, "task") and parent_doc.task:
			child_records = parent_doc.get("task")
			concatenated_str = ""
			total_days = 0
			total_weight = 0
			task_taken = len(child_records)
			concatenated_str += "<ol style='padding-left: 15px;'>"

			for child in child_records:
				print(child.days)
				task_name = child.task_name
				task_days = str(child.days)
				total_days += child.days
				total_weight += child.task_weight
				concatenated_str +="<li>"+task_name + " ( " + task_days + " Days ) " + "<br />" 

		data.append({
						"total_weight": row.total_weight,
						"employee_name": row.employee_name,
						"branch": row.branch,
						"task_taken": task_taken,
						"task_name": concatenated_str,
						"total_days": total_days,
						"total_weight": total_weight

					})
		concatenated_str += "</ol>"
		print(f"Task: {concatenated_str}")
		concatenated_str = concatenated_str.rstrip("<br />")


	return sorted(data, key=lambda d: d['total_weight'], reverse=True) 





	# report2 = frappe.db.sql(
	# 	"""SELECT
	# 	`tabSD Data Report`.total_weight as Total_Weight,
	# 	`tabSD Data Report`.employee_name as User,
	# 	`tabSD Data Report`.branch,
	# 	`tabSD Data Report`.task_taken as Total_Task, 
	# 	`tabSD Data Report Item`.task as Total_Days
	# 	FROM 
	# 	`tabSD Data Report` AS PARENT
	# 	JOIN
	# 	`tabSD Data Report Item` as CHILD,
    # 	ON
	# 	PARENT.name = CHILD.PARENT
	# 	WHERE tabTask._assign IS NOT NULL AND alias_table.User COLLATE utf8mb4_unicode_ci = tabEmployee.user_id
	# 	AND  %s GROUP BY tabTask.project, alias_table.User 
	# 	Order By Total_Weight DESC""" % (conditions),filters, as_list=1)




def get_data(conditions,filters):


	report = frappe.db.sql(
		"""SELECT
		SUM(task_weight) as Total_Weight,
		CONCAT(
        IFNULL(tabEmployee.first_name, ''),
        ' ',
        IFNULL(tabEmployee.middle_name, ''),
        ' ',
        IFNULL(tabEmployee.last_name, '')
   		) as User,
		tabEmployee.branch,
		COUNT(*) as Total_Task, 
		GROUP_CONCAT(CONCAT(tabTask.name, ' ( ', CASE
            WHEN tabEmployee.branch = 'Quality Assurance' THEN tabTask.qa_total_day AND IFNULL(tabTask.qa_total_day, '0')
            ELSE IFNULL(tabTask.programmer_total_day, '0')
        END , ' Days ) ') SEPARATOR '<br />') AS Task,
		SUM(
        CASE
            WHEN tabEmployee.branch = 'Quality Assurance' THEN tabTask.qa_total_day
            ELSE IFNULL(tabTask.programmer_total_day, '0')
        END
    	) as Total_Days
		FROM 
		tabTask,
    	JSON_TABLE(`tabTask`._assign,"$[*]" COLUMNS(User VARCHAR(30) PATH "$")) alias_table, tabEmployee
		WHERE tabTask._assign IS NOT NULL AND alias_table.User COLLATE utf8mb4_unicode_ci = tabEmployee.user_id
		AND  %s GROUP BY tabTask.project, alias_table.User 
		Order By Total_Weight DESC""" % (conditions),filters, as_list=1)

	return report

def get_cond(filters):
	if filters.get("project_name"):
		conditions += " and `tabTask`.project = %(project_name)s"
	if filters.get("team"):
		conditions += " and `tabEmployee`.branch = %(team)s"

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
