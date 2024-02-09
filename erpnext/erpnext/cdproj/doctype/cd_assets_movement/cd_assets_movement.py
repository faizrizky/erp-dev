# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class CDAssetsMovement(Document):
	def before_submit(self):
		self.validate_borrowed_employee()
		self.validate_condition_asset()
		self.validate_employee_transfer()

	def on_update_after_submit(self):
		#loop borrow asset list
		for borrow_asset in self.borrow_asset_list:
			condition 		= frappe.db.get_value("CD Asset", borrow_asset.asset_name, "condition") #Get condition asset
			custodian_desk 	= frappe.db.get_value('CD Room', {'room': 'Custodian Desk'}, ['room']) #Get custodian desk

			if not condition == "Good":
				return
			else:
				frappe.db.set_value('CD Asset', borrow_asset.asset_name, {
					'custodian': borrow_asset.to_employee,
					'status': 'Borrowed',
					'custodian_location': custodian_desk
				})

	def validate_condition_asset(self):
		for borrow_asset in self.borrow_asset_list:
			cd_asset = frappe.db.get_value("CD Asset", borrow_asset.asset_name, ["condition", "status", "asset_name"], as_dict=1)
			if not cd_asset.condition == "Good":
				frappe.throw(_("The asset : {0} cannot be borrowed, because current asset condition is {1}").format(frappe.bold(cd_asset.asset_name), frappe.bold(cd_asset.condition)))

		for transfer_asset in self.transfer_asset_list:
			cd_asset = frappe.db.get_value("CD Asset", transfer_asset.asset_transfer, ["condition", "status", "asset_name"], as_dict=1)
			if not cd_asset.condition == "Good":
				frappe.throw(_("The asset : {0} cannot be borrowed, because current asset condition is {1}").format(frappe.bold(cd_asset.asset_name), frappe.bold(cd_asset.condition)))

	def validate_borrowed_employee(self):
		for borrow in self.borrow_asset_list:
			if borrow.to_employee:
				current_custodian = frappe.db.get_value("CD Asset", borrow.asset_name, "custodian")
				current_employee = frappe.db.get_value("Employee", current_custodian, "employee_name")

			if current_custodian != None and current_custodian != borrow.to_employee:
				frappe.throw(_("The asset : {0} has been borrowed by the custodian : {1}").format(frappe.bold(borrow.asset_name),frappe.bold(current_employee)))
			else:
				custodianDesk = frappe.db.get_value('CD Room', {'room': 'Custodian Desk'}, ['room'])
				frappe.db.set_value('CD Asset', borrow.asset_name, {
					'custodian': borrow.to_employee,
					'status': 'Borrowed',
					'custodian_location': custodianDesk
				})
				cd_assets		= frappe.db.get_value("CD Asset", borrow.asset_name, ["name", "asset_name", "status", "condition", "type", "spesification", "note", "room"], as_dict=1)
				doc = frappe.get_doc('CD Asset Employee', borrow.to_employee)
				doc.append("assets_employee", {
					'asset_name': cd_assets.asset_name,
					'status': cd_assets.status,
					'condition': cd_assets.condition,
					'type': cd_assets.type,
					'spesification': cd_assets.spesification,
					'note': cd_assets.note,
					'room': cd_assets.room
				})
				doc.save()
				doc.reload()

	def validate_employee_transfer(self):
		for transfer in self.transfer_asset_list:
			if transfer.from_employee_transfer:
				current_custodian 	= frappe.db.get_value("CD Asset", transfer.asset_transfer, "custodian")
				current_employee 	= frappe.db.get_value("Employee", transfer.from_employee_transfer, "employee_name")
				belongs_to_employee = frappe.db.get_value("Employee", current_custodian, "employee_name")

				if current_custodian != transfer.from_employee_transfer:
					frappe.throw(_("The asset : {0} does not belong to the custodian : {1}, it belongs to {2}").format(frappe.bold(transfer.asset_transfer),frappe.bold(current_employee),frappe.bold(belongs_to_employee)))
				elif current_custodian == None:
					frappe.throw(_("The asset : {0}, current custodian is : {1}").format(frappe.bold(transfer.asset_transfer), frappe.bold(current_custodian)))
				else:
					frappe.db.set_value('CD Asset', transfer.asset_transfer,{
						'custodian': transfer.to_employee_transfer,
						'status': 'Borrowed'
					})					
					cd_assets	= frappe.db.get_value("CD Asset", transfer.asset_transfer, ["name", "asset_name", "status", "condition", "type", "spesification", "note", "room"], as_dict=1)
					current_inventaris = frappe.db.get_value('CD Asset Inventaris', {'parent': current_custodian}, ['parent'])
					frappe.db.delete("CD Asset Inventaris", { 'parent': current_inventaris })
					doc = frappe.get_doc('CD Asset Employee', transfer.to_employee_transfer)
					doc.append("assets_employee", {
						'asset_name': cd_assets.asset_name,
						'status': cd_assets.status,
						'condition': cd_assets.condition,
						'type': cd_assets.type,
						'spesification': cd_assets.spesification,
						'note': cd_assets.note,
						'room': cd_assets.room
					})
					doc.save()
		
	@frappe.whitelist()
	def get_linked_doc(self):
		for borrow_asset in self.borrow_asset_list:
			cd_assets		= frappe.db.get_value("CD Asset", borrow_asset.asset_name, ["name", "condition", "status", "asset_name", "room"], as_dict=1)
			redirect 		= '<a href="http://192.168.101.36:10001/app/cd-asset-store">CD Asset Store</a>'

			if not cd_assets.condition == 'Good' and cd_assets.status != 'Store':
				frappe.msgprint(
					msg=_('The Asset Name : {0}, Currently Its Update From CD Asset Parent, Cause Condition From Asset : {1}. Please Return Asset To Store Location {2} From Asset Store {3}').format(frappe.bold(cd_assets.name), frappe.bold(cd_assets.condition), frappe.bold(cd_assets.room), frappe.bold(redirect)),
					title='Announcement',
					indicator='blue',
				)