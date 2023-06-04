# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.reportview import build_match_conditions


def execute(filters=None):
	columns = get_column()
	data = get_data(filters)
	chart_data = get_chart_data(data)
	report_summary = get_report_summary(data)

	return columns, data, [chart_data], report_summary


def get_column():
	return [
		{"fieldname": "employee_name", "fieldtype": "", "label": _("User"),"height":150, "width": 200},
		{"fieldname": "branch", "fieldtype": "", "label": _("Team"),"height":150, "width": 150,"align": "left"},
		{"fieldname": "task_name", "fieldtype": "", "label": _("Task (Days)"),"height":500, "width": 350},
		{"fieldname": "task_taken", "fieldtype": "", "label": _("Task Taken")},
		{"fieldname": "total_weight", "fieldtype": "", "label": _("Total Weight"), "width": 120,"height":150},
		{"fieldname": "total_days", "fieldtype": "", "label": _("Total Days"),"height":150, "width": 150,"align": "left"},
	]


def get_data(filters):
	result = frappe.db.get_all(
		"SD Data Report",
		fields=["name", "total_weight", "employee_name", "branch", "task.task_name"],
		filters=filters,
		as_list=False,
		debug=False,
		group_by="employee_name",
		order_by="total_weight desc"
	)

	data = []
	for row in result:
		parent_doc = frappe.get_doc("SD Data Report", row.name)
		concatenated_str = ""
		if hasattr(parent_doc, "task") and parent_doc.task:
			child_records = parent_doc.get("task")
			total_days = 0
			total_weight = 0
			task_taken = len(child_records)
			concatenated_str += "<ol style='padding-left: 15px;'>"

			for child in child_records:
				task_name = child.task_name
				task_days = str(child.days)
				total_days += child.days
				total_weight += child.task_weight
				concatenated_str += "<li>" + task_name + " ( " + task_days + " Days ) " + "<br />"

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

	return sorted(data, key=lambda d: d['total_weight'], reverse=True)


def get_chart_data(data):
	labels = []
	total_tasks = []
	completed_tasks = []
	overdue_tasks = []

	for project in data:
		labels.append(project["branch"])
		total_tasks.append(project["task_taken"])
		completed_tasks.append(project["total_days"])
		overdue_tasks.append(project["task_taken"] - project["total_days"])

	return {
		"data": {
			"labels": labels[:30],
			"datasets": [
				{"name": "Overdue", "values": overdue_tasks[:30]},
				{"name": "Completed", "values": completed_tasks[:30]},
				{"name": "Total Tasks", "values": total_tasks[:30]},
			],
		},
		"type": "bar",
		"colors": ["#e24c4c", "#8ccf54", "#1673c5"],
		"barOptions": {"stacked": True},
	}


def get_report_summary(data):
	if not data:
		return None
	total_weight = sum(row["total_weight"] for row in data)
	total_days = sum(row["total_days"] for row in data)
	return [
		{
			"value": total_weight,
			"indicator": "Green",
			"label": _("Completed Tasks"),
			"datatype": "Int",
		},
		{
			"value": total_days,
			"indicator": "Green" if total_days == 0 else "Red",
			"label": _("Overdue Tasks"),
			"datatype": "Int",
		},
	]
