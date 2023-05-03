import frappe


from datetime import datetime, timedelta
import random

 

@frappe.whitelist()
def get_project() :
    return frappe.db.get_list('Project', pluck='name')

@frappe.whitelist()
def get_task() :
    task  = frappe.db.get_list("Task", filters={"project" : 'VTS Desktop Remake' }, fields=["depends_on_tasks", "name", "parent_task", "exp_start_date", "exp_end_date", "progress"])

    ini_time_for_now = datetime.now()
    # new_list = [{'start': item['exp_start_date'], 'name' : item['name'], 'end': item['exp_end_date'], "id" : item['name'], 'dependencies' : item['depends_on_tasks'], 'progress' : 100, "invalid" : False}  for item in task]
    new_list = [{'start': ini_time_for_now, 'name' : item['name'], 'end': ini_time_for_now +  timedelta(days = random.randint(10,90)), "id" : item['name'], 'dependencies' : item['depends_on_tasks'], 'progress' : item['progress'], "invalid" : False}  for item in task]

    print("mudik",new_list)
    print("mudik c")
   
    return new_list