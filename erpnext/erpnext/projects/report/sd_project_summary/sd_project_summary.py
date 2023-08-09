# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _

def get_dependent_tasks(task_name, status_to_check):
    dependent_tasks = []
    parent_task = frappe.get_doc("Task", task_name)
    if parent_task.depends_on:
        for row in parent_task.depends_on:
            dependent_tasks.append(row.task)
            dependent_tasks.extend(get_dependent_tasks(row.task, status_to_check))
    return dependent_tasks

def get_dependent_task_statuses(dependent_tasks):
    task_statuses = {}
    for task_name in dependent_tasks:
        task = frappe.get_doc("Task", task_name)
        task_status = task.status
        if task_status in task_statuses:
            task_statuses[task_status] += 1
        else:
            task_statuses[task_status] = 1
    return task_statuses

def execute(filters=None):
    columns = get_columns()

    project_name = filters.get("project")
    tasks = frappe.get_all("Task", filters={"project": project_name, "status": ("!=", "Cancelled")})
    completed_tasks  = frappe.get_all("Task", filters={"project": project_name, "status": ("=", "Completed")})
    

    # Fetch projects based on filters
    projects = frappe.db.get_all(
        "Project",
        filters=filters,
        fields=[
            "name",
            "status",
            "expected_start_date",
            "expected_end_date",
            "project_type",
        ],
        order_by="expected_end_date",
    )

    

    filtered_data = []
    # Loop through projects to get tasks from depends_on table
    for project in projects:
        tasks = frappe.db.get_all(
            "Task",
            filters={
                "is_group": 1,  # Filter for tasks with is_group = 1
                "parent_task": "",
                "project": project.name,
            },
            fields=["name", "subject", "status"],
        )

        for task in tasks:
            dependent_tasks = get_dependent_tasks(task.name, "Working")
            dependent_task_statuses = get_dependent_task_statuses(dependent_tasks)
            working_dependent_count = dependent_task_statuses.get("Working", 0)
            qa_testing_dependent_count = dependent_task_statuses.get("QA Testing", 0)
            integration_dependent_count = dependent_task_statuses.get("Integration", 0)
            qa_integration_testing_dependent_count = dependent_task_statuses.get("QA Integration Testing", 0)
            overdue_dependent_count = dependent_task_statuses.get("Overdue", 0)
            completed_dependent_count = dependent_task_statuses.get("Completed", 0)
            
            # print ("Completed Dependent Count :", len(task))
            

            total_tasks_dependent_count = (
                working_dependent_count
                + qa_testing_dependent_count
                + integration_dependent_count
                + qa_integration_testing_dependent_count
                + overdue_dependent_count
                + completed_dependent_count
            )
            progress = "{:.2f}%".format((completed_dependent_count/total_tasks_dependent_count) * 100) if completed_dependent_count != 0 else "N/A"
            # print((task.name,completed_dependent_count/total_tasks_dependent_count,progress) * 100) if completed_dependent_count != 0 else "N/A"
           
			
            filtered_data.append(
                {
                    "task_name": task.name,
                    # "task_subject": task.subject,
                    # "task_status": task.status,
                    "working": working_dependent_count,
                    "qa_testing": qa_testing_dependent_count,
                    "integration": integration_dependent_count,
                    "qa_integration_testing": qa_integration_testing_dependent_count,
                    "overdue": overdue_dependent_count,
                    "completed": completed_dependent_count,
                    "total_tasks": total_tasks_dependent_count,
                    "progress": progress,
                }
            )
   
    chart = get_chart_data(filtered_data)
    summary = get_report_summary(filtered_data)

    return columns, filtered_data, None, chart, summary



def get_columns():
    # Define columns for the report
    return [
        {"label": "Category Name", "fieldname": "task_name", "width": 200},
        {"label": "Working", "fieldname": "working", "width": 120},
        {"label": "QA Testing", "fieldname": "qa_testing", "width": 120},
        {"label": "Integration", "fieldname": "integration", "width": 120},
        {"label": "QA Integration Testing", "fieldname": "qa_integration_testing", "width": 180},
        {"label": "Overdue", "fieldname": "overdue", "width": 100},
        {"label": "Completed", "fieldname": "completed", "width": 120},
        {"label": "Total Tasks", "fieldname": "total_tasks", "width": 120},
        {"label": "Progress", "fieldname": "progress", "width": 120},
    ]




def get_chart_data(data):
    labels = []
    total_tasks = []
    completed = []
    overdue = []
    working = []
    qa_testing = []
    integration = []
    qa_integration_testing = []

    for task in data:
        labels.append(task["task_name"])  # Use task name as a string
        working.append(task["working"])
        qa_testing.append(task["qa_testing"])
        integration.append(task["integration"])
        qa_integration_testing.append(task["qa_integration_testing"])
        completed.append(task["completed"])
        overdue.append(task["overdue"])  # Add this line
        total_tasks.append(task["total_tasks"])

	
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
				{"name": _("Total Tasks"), "values": total_tasks[:30]},
			],
		},
		"type": "bar",
		"colors": ["#78d6ff", "#D51C8C", "#7575ff","#9055C1","#fc4f51","#8ccf54","#318AD8"],
		"barOptions": {"stacked": True},
	}


def get_report_summary(filtered_data):
    total_completed = 0
    total_total_tasks = 0
    total_overdue = 0

    for task in filtered_data:
        print("TASK COMPLETED : ", task["completed"])
        total_completed += task["completed"]
        total_total_tasks += task["total_tasks"]
        total_overdue += task["overdue"]

    total_uncompleted_tasks = total_total_tasks - total_completed
    avg_completed = (total_completed / total_total_tasks) * 100 if total_total_tasks != 0 else 0
    avg_total_tasks = total_total_tasks if len(filtered_data) != 0 else 0
    overdue = total_overdue
    completed = total_completed

    return [
        {
            "value": avg_completed,
            "indicator": "Green" if avg_completed > 50 else "Red",
            "label": _("Average Completion"),
            "datatype": "Percent",
        },
        {
            "value": avg_total_tasks,
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
            "value": overdue,
            "indicator": "Red",
            "label": _("Overdue Tasks"),
            "datatype": "Int",
        },
        {
            "value": total_uncompleted_tasks,
            "indicator": "Red",
            "label": _("Uncompleted Tasks"),
            "datatype": "Int",
        },
    ]
