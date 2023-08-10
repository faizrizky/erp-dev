# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.reportview import build_match_conditions
import json


def execute(filters=None):
    columns = get_column()
    data = get_data(filters)
    chart_data = get_chart_data(data)
    report_summary = get_report_summary(data)
    # print(json.dumps(chart_data, sort_keys=True, indent=4))

    return columns, data, None, chart_data, report_summary


def get_column():
    return [
        {"fieldname": "employee_name", "fieldtype": "", "label": _("User"), "height": 150, "width": 200},
        {"fieldname": "branch", "fieldtype": "", "label": _("Team"), "height": 150, "width": 320, "align": "left"},
        {"fieldname": "task_name", "fieldtype": "", "label": _("Task (Days)"), "height": 500, "width": 350},
        {"fieldname": "days", "fieldtype": "", "label": _("Days"), "height": 500, "width": 150},
        {"fieldname": "task_taken", "fieldtype": "", "label": _("Task Taken")},
        {"fieldname": "total_weight", "fieldtype": "", "label": _("Total Weight"), "width": 120, "height": 150},
        {"fieldname": "total_days", "fieldtype": "", "label": _("Total Days"), "height": 150, "width": 150,
         "align": "left"},
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
        concatenated_days = ""
        if hasattr(parent_doc, "task") and parent_doc.task:
            child_records = parent_doc.get("task")
            total_days = parent_doc.total_days
            total_weight = 0
            task_taken = len(child_records)
            concatenated_str += "<ol style='padding-left: 15px;'>"
            # concatenated_days += "<ol style='padding-left: 15px;'>"

            prev_task_name = None  # Variable to store the previous task name
            first_record = True

            for child in child_records:
                task_name = child.task_name
                task_days = str(child.days)
                total_weight += child.task_weight

                pname = task_name.split('-')[0].strip()

                # if prev_task_name and prev_task_name.split('-')[0].strip() != task_name.split('-')[0].strip():
                #     # total_days += child.days
                #     subject,exp_start_date, review_date = frappe.db.get_value('Task', pname, ['subject','exp_start_date', 'review_date'])
                    # print("subject : ", subject, " || ","exp_start_date : ", exp_start_date," || ","review_date : ",review_date)

                    # print("NAMA TASK : ", pname)

                # print("TOTAL STRING : ", task_name + " || " + str(len(task_name)/70))
                # if (len(task_name)/70) >=1.5 :
                #     concatenated_days += task_days  + "<br />" + "<br />" + "<br />" + "<br />"
                # elif (len(task_name)/70) >=1:
                #     concatenated_days += task_days  + "<br />" + "<br />" + "<br />"
                # elif (len(task_name)/70) >=0.5:
                #     concatenated_days += task_days  + "<br />" + "<br />"
                # else:
                #     concatenated_days += task_days  + "<br />"
                concatenated_days += task_days  + "<br />" + "<br />"
                if child.is_parent == 0:
                    # concatenated_str += "<li>" + task_name + " ( " + task_days + " Days ) " + "<br />"
                    concatenated_str += "<li>" + task_name + "<br />"
                    
                    
                else:
                    # concatenated_str += "<li>" + task_name + " - Integration" + " ( " + task_days + " Days ) " + "<br />"
                    concatenated_str += "<li>" + task_name + " - Integration" + "<br />"

                prev_task_name = task_name

                if first_record:
                    # total_days += child.days
                    first_record = False
    
            data.append({
                "total_weight": row.total_weight,
                "employee_name": row.employee_name,
                "branch": row.branch,
                "task_taken": task_taken,
                "days": concatenated_days,
                "task_name": concatenated_str,
                "total_days": total_days,
                "total_weight": total_weight
            })

        concatenated_str += "</ol>"

    return sorted(data, key=lambda d: d['total_weight'], reverse=True)


def get_chart_data(data):
    labels = []
    task_taken = []
    total_weight = []
    total_days = []
    # overdue_tasks = []

    for project in data:
        labels.append(project["branch"])
        task_taken.append(project["task_taken"])
        total_weight.append(project["total_weight"])
        total_days.append(project["total_days"])
        # overdue_tasks.append(project["task_taken"] - project["total_days"])

    return {
        "data": {
            "labels": labels[:30],
            "datasets": [
                {"name": "Task Taken", "values": task_taken[:30]},
                {"name": "Total Weight", "values": total_weight[:30]},
                {"name": "Total Days", "values": total_days[:30]},
            ],
        },
        "type": "bar",
        "colors": ["#8ccf54", "#1673c5", "#78d6ff"],
        "barOptions": {"stacked": False},
    }


def get_report_summary(data):
    if not data:
        return None
    total_task_taken = sum(row["task_taken"] for row in data)
    total_weight = sum(row["total_weight"] for row in data)
    total_days = sum(row["total_days"] for row in data)
    return [
        {
            "value": total_task_taken,
            "indicator": "Green",
            "label": _("Total Task Taken"),
            "datatype": "Int",
        },
        {
            "value": total_weight,
            "indicator": "Blue",
            "label": _("Total Weight"),
            "datatype": "Int",
        },
        {
            "value": total_days,
            "indicator": "Blue",
            "label": _("Total Days"),
            "datatype": "Int",
        },
    ]
