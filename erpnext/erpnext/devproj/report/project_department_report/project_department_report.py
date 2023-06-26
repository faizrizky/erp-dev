# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    # data = []
    project_name = filters.get("project")

    tasks = frappe.get_all("Task", filters={"project": project_name, "status": ("!=", "Cancelled")})
    total_tasks = len(tasks)

    print(f"Total tasks in the selected project: {total_tasks}")

    data = frappe.db.get_all(
        "Task",
        # filters=filters,
        fields=[
            "name",
            "status",
            "progress",
            "project",
            "_assign"
        ],
        order_by="name",
        # group_by="_user_tags"
    )

    task_data = {}
    for task in data:
        subject = frappe.db.get_value('Task', task.name, '_assign')
        if subject is not None:
            result = json.loads(subject)
            for emp in result:
                emp_name = frappe.db.get_value('User', emp, 'full_name')
                branch = frappe.db.get_value("User", emp, "role")
                if branch not in task_data:
                    task_data[branch] = []
                task_data[branch].append({
                    "task_name": task.name,
                    "employee_name": emp_name,
                    "project": task.project
                })

    # Filter result_data by project
    filtered_data = []

    if filters and filters.get("project"):
        project_filter = filters.get("project")
        for branch, tasks in task_data.items():
            filtered_tasks = [
                task for task in tasks
                if task["project"] == project_filter
            ]
            if filtered_tasks:
                filtered_data.append({
                    "branch": branch,
                    "tasks": filtered_tasks
                })
    else:
        filtered_data = [
            {"branch": branch, "tasks": tasks}
            for branch, tasks in task_data.items()
        ]

    # total_task_count = sum(len(result["tasks"]) for result in filtered_data)
    # print("Total tasks in filtered data:", filtered_data)

    
    for result in filtered_data:
        tasks = result["tasks"]
        # print("Total tasks in filtered data:",sum(len(tasks)))
        # completed_tasks = sum(1 for task in tasks if task.get("status") == "Completed")
        # result["completed_tasks"] = completed_tasks
        for task in tasks:
            task_status = frappe.db.get_value("Task", task["task_name"], "status")
            task["status"] = task_status

    # Count total tasks by branch
    task_count_by_branch = {}
    for result in filtered_data:
        branch = result["branch"]
        tasks = result["tasks"]
        task_count_by_branch[branch] = [(task["task_name"], task["employee_name"], task["status"]) for task in tasks]

    # for branch, tasks in task_count_by_branch.items():
    #     print("Tasks in Branch '{}':".format(branch))
    #     for task_name, employee_name, status in tasks:
    #         print("- Task: {}, Employee: {}, Status: {}".format(task_name, employee_name, status))
    #     print()

    # total_tasks = sum(len(tasks) for tasks in task_data.values())
    # print(total_tasks)

    total_filtered_task = []

    for result in filtered_data:
        tasks = result["tasks"]
        task_names = [task["task_name"] for task in tasks]

        for task_name in task_names:
            if task_names.count(task_name) == 1 and task_name not in total_filtered_task:
                total_filtered_task.append(task_name)

    total_unique_tasks = len(total_filtered_task)
    print("Total unique tasks in filtered data:", total_filtered_task)
    print("Total unique tasks in filtered data:", len(total_filtered_task))


    for result in filtered_data:
        tasks = result["tasks"]
        department_task = len(tasks)
        # print("department_task: ", department_task)
        completed_tasks = sum(1 for task in tasks if task.get("status") == "Completed")
        # total_tasks = sum(1 for task in tasks)
        departement_progress = (completed_tasks / department_task) * 100 if department_task > 0 else 0
        task_completion = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        result["total_task_completed"] = completed_tasks
        result["department_task"] = department_task
        result["employee_name"] = ""  # Add employee_name field
        result["departement_progress"] = "{:.2f}%".format(departement_progress)
        result["task_completion"] = "{:.2f}%".format(task_completion)
        print("task_completion: ",task_completion)


        task_count_by_employee = {}  # Dictionary to store task count for each employee

        for task in tasks:
            employee_name = task["employee_name"]
            if employee_name not in task_count_by_employee:
                task_count_by_employee[employee_name] = 0
            task_count_by_employee[employee_name] += 1

        concatenated_str = "<ol style='padding-left: 15px;'>"
        employee_list = []
        for emp, count in task_count_by_employee.items():
            employee_list.append("<li>{} ({} Task)</li>".format(emp, count))

        employee_names = "<br>".join(employee_list)
        result["employee_name"] = employee_names

        concatenated_str += employee_names
        concatenated_str += "</ol>"

        result["concatenated_str"] = concatenated_str

    sum_task_completion = sum(float(result["task_completion"].replace("%", "")) for result in filtered_data)
    print("Sum of Task Completion: {:.2f}%".format(sum_task_completion))

   

    

    chart = get_chart_data(filtered_data)
    # print(chart)
    report_summary = get_report_summary(filtered_data,sum_task_completion, total_tasks)

    # print(json.dumps(chart,  sort_keys=True, indent=4))



    return columns, filtered_data, task_count_by_branch,chart, report_summary



# return columns, result_data, None

# employee_name = frappe.db.get_value("User", task._assign, "employee_name")
# branch = frappe.db.get_value("Employee", employee_name, "branch")
# print("User Name: {}, Task Name : {} Branch: {}".format(task._assign, task.name, branch))
# print("Employee Name: {}, Branch: {}".format(employee_name, branch))


# total_tasks = frappe.db.count("Task", filters={"project": task.project})

# task["completed_tasks"] = frappe.db.count(
# 			"Task", filters={"project": task.name, "status": "Completed"}
# 			)
# task["overdue_tasks"] = frappe.db.count(
# 			"Task", filters={"project": task.name, "status": "Overdue"}
# 			)
# print("Total tasks for project {}: {}".format(task.project, total_tasks))


# for project in data:
# 	project["total_tasks"] = frappe.db.count("Task", filters={"project": project.name})
# 	project["completed_tasks"] = frappe.db.count(
# 		"Task", filters={"project": project.name, "status": "Completed"}
# 	)
# 	project["overdue_tasks"] = frappe.db.count(
# 		"Task", filters={"project": project.name, "status": "Overdue"}
# 	)

# chart = get_chart_data(data)
# report_summary = get_report_summary(data)

# return columns, data, None


def get_columns():
    return [
        {
            "fieldname": "branch",
            "label": _("Team"),
            "fieldtype": "Link",
            "options": "Branch",
            "width": 300,
        },
        {
            "fieldname": "concatenated_str",
            "label": _("Employee Name (Task Taken)"),
            "fieldtype": "Data",
            "width": 410,
        },
        {
            "fieldname": "department_task",
            "label": _("Dept. Task"),
            "fieldtype": "Data",
            # "options": "Project Type",
            "width": 100,
        },
        {"fieldname": 
            "total_task_completed", 
            "label": _("Dept. Task Completed"), 
            "fieldtype": "Data", 
            "width": 170},
        {
            "fieldname": "departement_progress",
            "label": _("Dept. Progress"),
            "fieldtype": "Data",
            "width": 120,
        },
        {"fieldname": 
            "task_completion", 
            "label": _("Completion %"),
            "fieldtype": "Data", 
            "width": 110
        },

        # {"fieldname": "percent_complete", "label": _("Completion"), "fieldtype": "Data", "width": 120},
        # {
        #     "fieldname": "expected_start_date",
        #     "label": _("Start Date"),
        #     "fieldtype": "Date",
        #     "width": 120,
        # },
        # {"fieldname": "expected_end_date", "label": _("End Date"), "fieldtype": "Date", "width": 120},
    ]



def get_chart_data(data):
    labels = []
    total = []
    completed = []
    overdue = []

    for project in data:
        labels.append(project["branch"])
        total.append(project["department_task"])
        completed.append(project["total_task_completed"])
        overdue.append(project["department_task"] - project["total_task_completed"])

    return {
        "data": {
            "labels": labels[:30],
            "datasets": [
                {"name": "Uncompleted", "values": overdue[:30]},
                {"name": "Completed", "values": completed[:30]},
                {"name": "Total Tasks", "values": total[:30]},
            ],
        },
        "type": "bar",
        "colors": ["#e24c4c", "#8ccf54", "#1673c5"],
        "barOptions": {"stacked": False},
    }


def get_report_summary(data, sum_task_completion, total_task):
    if not data:
        return None
    
    total_progress = sum_task_completion
    avg_completion = round(sum_task_completion / len(data), 2)
    # total = sum([project["department_task"] for project in data])
    total = total_task
    total_overdue = sum([project["department_task"] - project["total_task_completed"] for project in data])
    completed = sum([project["total_task_completed"] for project in data])

    return [
        {
            "value": total_progress,
            "indicator": "Green" if total_progress > 50 else "Red",
            "label": _("Total Progress"),
            "datatype": "Percent",
        },
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
            "label": _("Uncompleted Tasks"),
            "datatype": "Int",
        },
    ]
