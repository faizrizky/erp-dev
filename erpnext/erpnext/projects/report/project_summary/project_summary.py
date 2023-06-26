# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = []

	data = frappe.db.get_all(
		"Project",
		filters=filters,
		fields=[
			"name",
			"status",
			"percent_complete",
			"expected_start_date",
			"expected_end_date",
			"project_type",
		],
		order_by="expected_end_date",
	)

	for project in data:
		# data2 = frappe.get_all('Task',filters={"project": project.name})
		# print("TOTAL DATA 2 : ", len(data2))
		project["total_tasks"] = frappe.db.count("Task", filters={"project": project.name,
            "status": ("!=", "Cancelled")})
		project["completed_tasks"] = frappe.db.count(
			"Task", filters={"project": project.name, "status": "Completed"}
		)
		project["overdue_tasks"] = frappe.db.count(
			"Task", filters={"project": project.name, "status": "Overdue"}
		)
		project["working_tasks"] = frappe.db.count(
			"Task", filters={"project": project.name, "status": "Working"}
		)
		project["qa_testing_tasks"] = frappe.db.count(
			"Task", filters={"project": project.name, "status": "QA Testing"}
		)
		project["integration_tasks"] = frappe.db.count(
			"Task", filters={"project": project.name, "status": "Integration"}
		)
		project["qa_integration_testing_tasks"] = frappe.db.count(
			"Task", filters={"project": project.name, "status": "QA Integration Testing"}
		)

	chart = get_chart_data(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{
			"fieldname": "name",
			"label": _("Project"),
			"fieldtype": "Link",
			"options": "Project",
			"width": 200,
		},
		{
			"fieldname": "project_type",
			"label": _("Type"),
			"fieldtype": "Link",
			"options": "Project Type",
			"width": 120,
		},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 120},
		{
			"fieldname": "working_tasks",
			"label": _("Working"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "qa_testing_tasks",
			"label": _("QA Testing"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "integration_tasks",
			"label": _("Integration"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "qa_integration_testing_tasks",
			"label": _("QA Integration Testing"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "completed_tasks",
			"label": _("Completed"),
			"fieldtype": "Data",
			"width": 120,
		},
		{"fieldname": "total_tasks", "label": _("Total Tasks"), "fieldtype": "Data", "width": 120},
		{"fieldname": "overdue_tasks", "label": _("Tasks Overdue"), "fieldtype": "Data", "width": 120},
		{"fieldname": "percent_complete", "label": _("Completion"), "fieldtype": "Data", "width": 120},
		{
			"fieldname": "expected_start_date",
			"label": _("Start Date"),
			"fieldtype": "Date",
			"width": 120,
		},
		{"fieldname": "expected_end_date", "label": _("End Date"), "fieldtype": "Date", "width": 120},
	]


def get_chart_data(data):
	labels = []
	total = []
	completed = []
	overdue = []
	working = []
	qa_testing = []
	integration = []
	qa_integration_testing = []

	for project in data:
		print(project)
		labels.append(project.name)
		if project.get("status") != "Cancelled":
			total.append(project["total_tasks"])
		total.append(project.total_tasks)
		completed.append(project.completed_tasks)
		working.append(project.working_tasks)
		qa_testing.append(project.qa_testing_tasks)
		integration.append(project.integration_tasks)
		qa_integration_testing.append(project.qa_integration_testing_tasks)

	return {
		"data": {
			"labels": labels[:30],
			"datasets": [
				{"name": _("Working"), "values": working[:30]},
				{"name": _("QA Testing"), "values": qa_testing[:30]},
				{"name": _("Integration"), "values": integration[:30]},
				{"name": _("QA Integration Testing"), "values": qa_integration_testing[:30]},
				{"name": _("Overdue"), "values": overdue[:30]},
				{"name": _("Completed"), "values": completed[:30]},
				{"name": _("Total Tasks"), "values": total[:30]},
			],
		},
		"type": "bar",
		"colors": ["#78d6ff", "#D51C8C", "#7575ff","#9055C1","#fc4f51","#8ccf54","#318AD8"],
		"barOptions": {"stacked": True},
	}


def get_report_summary(data):
	if not data:
		return None

	avg_completion = sum(project.percent_complete for project in data) / len(data)
	# total = sum([project.total_tasks for project in data])
	total = sum(project["total_tasks"] for project in data if project.get("status") != "Cancelled")
	total_overdue = sum([project.overdue_tasks for project in data])
	completed = sum([project.completed_tasks for project in data])

	return [
		{
			"value": avg_completion,
			"indicator": "Green" if avg_completion > 50 else "Red",
			"label": _("Average Completion"),
			"datatype": "Percent",
		},
		{
			"value": total,
			"indicator": "Blue",
			"label": _("Total Tasks"),
			"datatype": "Int",
		},
		{
			"value": completed,
			"indicator": "Green",
			"label": _("Completed Tasks"),
			"datatype": "Int",
		},
		{
			"value": total_overdue,
			"indicator": "Green" if total_overdue == 0 else "Red",
			"label": _("Overdue Tasks"),
			"datatype": "Int",
		},
	]
