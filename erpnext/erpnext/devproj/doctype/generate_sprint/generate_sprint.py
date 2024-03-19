# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta

class GenerateSprint(Document):
	def on_submit(self):
		self.create_sprint()
		
	def create_sprint(self):
			# current_year = datetime.now().year
			start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
			end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
   
			if end_date <= start_date:
				frappe.throw(
				_("{0} can not be greater than {1}").format(
					frappe.bold("End Date"), frappe.bold("Start Date")
				)
			)
    
			delta = timedelta(days=1) 
			start_of_sprint_count = 0
			end_of_sprint_count = 0
			# days_count = 0
			start_sprint_date = ""
			end_sprint_date = ""
			sprint_counter = 0
			
	
			current_date = start_date
			while current_date <= end_date:
				if current_date.weekday() < 5:
					# print("start_of_sprint_count : ", start_of_sprint_count)
					if start_of_sprint_count == 0:
						sprint_counter += 1
						print("Sprint :", sprint_counter)
						start_sprint_date = current_date.strftime("%Y-%m-%d")
						print("Start Sprint Date:", start_sprint_date)
					current_date += delta
					start_of_sprint_count += 1
					end_of_sprint_count += 1
					# days_count += 1
					# print("current_date : ", current_date.weekday())
					# print("end_of_sprint_count : ", end_of_sprint_count)
					
					
					# print("end_of_sprint_count : ", end_of_sprint_count)
					# print("now : ",  current_date.strftime("%Y-%m-%d"))
					if end_of_sprint_count == 11:
						end_sprint_date = current_date.strftime("%Y-%m-%d")
						print("End of Sprint Date:", end_sprint_date)
					
		
				else:
					# print("INI WEEKEND : ", current_date.strftime("%Y-%m-%d"))
					current_date += delta
					end_of_sprint_count += 1
					# days_count += 1
					# print("now : ",  current_date.strftime("%Y-%m-%d"))
					# print("end_of_sprint_count : ", end_of_sprint_count)

     
					if end_of_sprint_count == 14:
						print("===== Reset two weeks =====")
						if sprint_counter == 27:
							sprint_counter = 0
						start_sprint_date_new_format = datetime.strptime(start_sprint_date, "%Y-%m-%d").strftime("%d-%m-%Y")
						end_sprint_date_new_format = datetime.strptime(end_sprint_date, "%Y-%m-%d").strftime("%d-%m-%Y")
					
						doc = frappe.new_doc('Event')
						doc.subject = 'SPRINT - ' + str(sprint_counter) + ' : ' + start_sprint_date_new_format + ' - ' + end_sprint_date_new_format
						doc.event_category = "Sprint"
						doc.event_type = "Public"
						doc.status = "Soon"
						doc.starts_on = start_sprint_date
						doc.ends_on = end_sprint_date
						doc.insert()
						start_of_sprint_count = 0
						end_of_sprint_count = 0
						start_sprint_date = ""
						end_sprint_date = ""
						# print("days_count : ", days_count)
						# if days_count == 11:
				# if days_count in range(364, 366):
				# 	print("End of the Year")
				# 	break

