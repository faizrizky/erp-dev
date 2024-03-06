// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

var isBool = false;
var arrUser = [];
frappe.ui.form.AssignTo = class AssignTo {
  constructor(opts) {
    $.extend(this, opts);

    this.btn = this.parent
      .find(".add-assignment-btn")
      .on("click", () => this.add());
    this.btn_wrapper = this.btn.parent();

    var cdRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("hod content");

    let sdLeadRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("leader software");
    // if (!(sdLeadRole || cdRole || frappe.session.user === "Administrator")) {
    //   this.parent.find(".add-assignment-btn").remove();
    // }

    this.refresh();
  }
  refresh() {
    if (this.frm.doc.__islocal) {
      this.parent.toggle(false);
      return;
    }
    this.parent.toggle(true);
    this.render(this.frm.get_docinfo().assignments);
  }
  render(assignments) {
    this.frm.get_docinfo().assignments = assignments;

    let assignments_wrapper = this.parent.find(".assignments");

    assignments_wrapper.empty();
    let assigned_users = assignments.map((d) => d.owner);

    if (!assigned_users.length) {
      assignments_wrapper.hide();
      return;
    }

    let avatar_group = frappe.avatar_group(assigned_users, 5, {
      align: "left",
      overlap: true,
    });

    assignments_wrapper.show();
    assignments_wrapper.append(avatar_group);
    avatar_group.click(() => {
      new frappe.ui.form.AssignmentDialog({
        assignments: assigned_users,
        frm: this.frm,
      });
    });
  }
  add() {
    var me = this;

    // frappe.throw("you not allowed");

    if (this.frm.is_new()) {
      frappe.throw(__("Please save the document before assignment"));
      return;
    }

    if (!me.assign_to) {
      me.assign_to = new frappe.ui.form.AssignToDialog({
        method: "frappe.desk.form.assign_to.add",
        doctype: me.frm.doctype,
        docname: me.frm.docname,
        frm: me.frm,
        callback: function (r) {
          me.render(r.message);
        },
      });
    }
    me.assign_to.dialog.clear();
    me.assign_to.dialog.show();
  }
  remove(owner) {
    if (this.frm.is_new()) {
      frappe.throw(__("Please save the document before removing assignment"));
      return;
    }

    return frappe
      .xcall("frappe.desk.form.assign_to.remove", {
        doctype: this.frm.doctype,
        name: this.frm.docname,
        assign_to: owner,
      })
      .then((assignments) => {
        this.render(assignments);
      });
  }
};

frappe.ui.form.AssignToDialog = class AssignToDialog {
  constructor(opts) {
    $.extend(this, opts);

    this.make();
    this.set_description_from_doc();
  }

  make() {
    let me = this;

    me.dialog = new frappe.ui.Dialog({
      title: __("Add to ToDo"),
      fields: me.get_fields(),
      primary_action_label: __("Add"),
      primary_action: function () {
        let args = me.dialog.get_values();

        if (args && args.assign_to) {
          me.dialog.set_message("Assigning...");

          frappe.call({
            method: me.method,
            args: $.extend(args, {
              doctype: me.doctype,
              name: me.docname,
              assign_to: args.assign_to,
              bulk_assign: me.bulk_assign || false,
              re_assign: me.re_assign || false,
            }),
            btn: me.dialog.get_primary_btn(),
            callback: function (r) {
              if (!r.exc) {
                if (me.callback) {
                  me.callback(r);
                }
                me.dialog && me.dialog.hide();
              } else {
                me.dialog.clear_message();
              }
            },
          });
        }
      },
    });
  }
  assign_to_me() {
    let me = this;
    // let assign_to = [];

    if (me.dialog.get_value("assign_to_me")) {
      frappe.db
        .get_list("Employee", {
          fields: ["user_id"],
        })
        .then(() => {
          let assign_to = me.dialog.get_value("assign_to");

          if (!assign_to.includes(frappe.session.user))
            return assign_to.push(frappe.session.user);

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");
          let whoami = frappe.session.user;
          console.log("Record USER : " + whoami);
          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(frappe.session.user);
            if (assign_to.includes(frappe.session.user)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }
  }
  // assign_team() {
  // 	let me = this;

  // 	if (me.dialog.get_value("assign_team")) {

  // 		frappe.db.get_list('Employee', {
  // 			filters: { 'branch': me.dialog.get_value("assign_team") },
  // 			fields: ['user_id']

  // 		}).then((records) => {
  // 			let assign_to = [];

  // 			records.forEach((c) => assign_to.push(c.user_id));

  // 			me.dialog.set_value("assign_to", assign_to);
  // 		});
  // 	}
  // 	else {
  // 		me.dialog.set_value("assign_to", []);
  // 	}
  // 	// values = {'branch':'Level Designer'}

  // 	// me.dialog.set_value("assign_to",frappe.db.sql("""select branch FROM 'tabEmployee'""", values=values, as_dict=0));
  // 	// subject = frappe.db.get_value('Employee', {'branch': 'Level Designer'}, ['subject'])

  // 	// alert(asd)
  // }

  assign_ld() {
    let me = this;

    if (me.dialog.get_value("assign_ld")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Level Designer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;

      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Level Designer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            console.log("Record USER : " + records[i].user_id);
            console.log("Assign_To USER : " + assign_to);
            console.log(index);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }

    if (me.dialog.get_value("assign_ld")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Level Designer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      // me.dialog.set_value("assign_to", []);
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Level Designer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          // for (let i = 0; i < records.length; i++) {
          // 	// console.log(records[i].user_id)
          // 	if (records.findIndex(records[i].user_id)) {
          // 		records[i].splice(i, 1);
          // 		console.log(records[i].user_id);
          // 		i--;
          // 	}
          // }
          // console.log(assign_to)
          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            console.log("Record USER : " + records[i].user_id);
            console.log("Assign_To USER : " + assign_to);
            console.log(index);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
            // 	i--;
            // }
          }
          // records.forEach((c) => {
          // 	console.log(c.user_id)
          // 	if (assign_to.includes(c.user_id))
          // 		// console.log(c.user_id)
          // 		if (assign_to.indexOf(c.user_id))
          // 			return assign_to.splice(c.user_id, 1);
          // });

          me.dialog.set_value("assign_to", assign_to);
        });
    }
  }

  assign_be() {
    let me = this;

    if (me.dialog.get_value("assign_be")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Backend Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Backend Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }

    if (me.dialog.get_value("assign_be")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Backend Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Backend Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }
  }

  assign_fe() {
    let me = this;

    if (me.dialog.get_value("assign_fe")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Frontend Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Frontend Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }

    if (me.dialog.get_value("assign_fe")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Frontend Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Frontend Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }
  }

  assign_unityprog() {
    let me = this;

    if (me.dialog.get_value("assign_unityprog")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Unity Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");
          console.log(records);
          records.forEach((c) => {
            console.log("Record USER : " + c.user_id);
            console.log("Assign_To USER : " + assign_to);
            if (!assign_to.includes(c.user_id)) {
              return assign_to.push(c.user_id);
            }
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Unity Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }

    if (me.dialog.get_value("assign_unityprog")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Unity Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");
          console.log(records);
          records.forEach((c) => {
            console.log("Record USER : " + c.user_id);
            console.log("Assign_To USER : " + assign_to);
            if (!assign_to.includes(c.user_id)) {
              return assign_to.push(c.user_id);
            }
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Unity Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }
  }
  assign_de() {
    let me = this;

    if (me.dialog.get_value("assign_de")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Document Engineer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Document Engineer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }

    if (me.dialog.get_value("assign_de")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Document Engineer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Document Engineer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }
  }
  assign_qa() {
    let me = this;
    if (me.dialog.get_value("assign_qa")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Quality Assurance", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Technical Architect Quality Assurance", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }

    if (me.dialog.get_value("assign_qa")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Quality Assurance", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Quality Assurance", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }
  }

  assign_lead() {
    let me = this;

    if (me.dialog.get_value("assign_lead")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Co Division Software Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "Co Division Software Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }

    if (me.dialog.get_value("assign_lead")) {
      frappe.db
        .get_list("Employee", {
          filters: { branch: "HOD Software Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          records.forEach((c) => {
            if (!assign_to.includes(c.user_id))
              return assign_to.push(c.user_id);
          });

          me.dialog.set_value("assign_to", assign_to);
        });
    } else {
      let me = this;
      frappe.db
        .get_list("Employee", {
          filters: { branch: "HOD Software Programmer", status: "Active" },
          fields: ["user_id"],
        })
        .then((records) => {
          let assign_to = me.dialog.get_value("assign_to");

          for (let i = 0; i < records.length; i++) {
            let index = assign_to.indexOf(records[i].user_id);
            if (assign_to.includes(records[i].user_id)) {
              assign_to.splice(index, 1);
            }
          }
          me.dialog.set_value("assign_to", assign_to);
        });
    }
  }

  set_description_from_doc() {
    let me = this;

    if (me.frm && me.frm.meta.title_field) {
      me.dialog.set_value("description", me.frm.doc[me.frm.meta.title_field]);
    }
  }

  toggleBoolean(val) {
    return val;
  }
  setToFalse(boolVar) {
    this.toggleBoolean(boolVar, false);
  }

  // get_user() {
  //   //next filter untuk leader, tp masih error
  //   frappe.db
  //     .get_list("Employee", {
  //       filters: { branch: "Leader Programmer" },
  //       fields: ["user_id"],
  //     })
  //     .then((records) => {
  //       // console.log(records)
  //       // console.log(frappe.session.user)

  //       for (let i = 0; i < records.length; i++) {
  //         // console.log(records[i].user_id)
  //         if (frappe.session.user.includes(records[i].user_id)) {
  //           // console.log(isBool)
  //           arrUser.push(records[i].user_id);
  //           isBool = true;
  //           // console.log("INI ARRAY RECORDS 1" + records[i].user_id)
  //           // console.log(isBool)
  //           // console.log((isBool))
  //           // return [
  //           // 	{
  //           // 		label: __("Assign to me"),
  //           // 		fieldtype: "Check",
  //           // 		fieldname: "assign_to_me",
  //           // 		default: 0,
  //           // 		onchange: () => me.assign_to_me(),
  //           // 	},
  //           // ];
  //         }
  //       }
  //       this.get_fields();
  //     });
  // }

  get_fields() {
    let me = this;

    // if (frappe.user.has_role("Software Developer") != 1) {
    let sdLeadRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("leader software");

    let sdRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("technical architect");

    var cdRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("hod content");

    // let filters = { name: ["like", "%" + frappe.session.user + "%"] };

    // if (cdRole || sdLeadRole || frappe.session.user === "Administrator") {
    //   filters = {};
    // }

    if (sdLeadRole) {
      return [
        {
          label: __("Assign to me"),
          fieldtype: "Check",
          fieldname: "assign_to_me",
          default: 0,
          onchange: () => me.assign_to_me(),
        },

        {
          label: __("Level Design"),
          fieldtype: "Check",
          fieldname: "assign_ld",
          default: 0,
          onchange: () => me.assign_ld(),
        },
        {
          label: __("Backend Programmer"),
          fieldtype: "Check",
          fieldname: "assign_be",
          default: 0,
          onchange: () => me.assign_be(),
        },
        {
          label: __("Frontend Programmer"),
          fieldtype: "Check",
          fieldname: "assign_fe",
          default: 0,
          onchange: () => me.assign_fe(),
        },
        {
          fieldtype: "Column Break",
        },
        {
          label: __("All Lead"),
          fieldtype: "Check",
          fieldname: "assign_lead",
          default: 0,
          onchange: () => me.assign_lead(),
        },
        {
          label: __("Unity Programmer"),
          fieldtype: "Check",
          fieldname: "assign_unityprog",
          default: 0,
          onchange: () => me.assign_unityprog(),
        },
        {
          label: __("Document Engineer"),
          fieldtype: "Check",
          fieldname: "assign_de",
          default: 0,
          onchange: () => me.assign_de(),
        },
        {
          label: __("Quality Assurance"),
          fieldtype: "Check",
          fieldname: "assign_qa",
          default: 0,
          onchange: () => me.assign_qa(),
        },

        {
          fieldtype: "Section Break",
        },
        {
          fieldtype: "MultiSelectPills",
          fieldname: "assign_to",
          label: __("Assign To"),
          reqd: true,
          get_data: function (txt) {
            return frappe.db.get_link_options("User", txt, {
              user_type: "System User",
              enabled: 1,
              // filters: filters,
            });
          },
        },

        {
          fieldtype: "Section Break",
        },
        {
          label: __("Comment"),
          fieldtype: "Small Text",
          fieldname: "description",
        },
      ];
    } if (sdRole) {
      return [
        {
          label: __("Assign to me"),
          fieldtype: "Check",
          fieldname: "assign_to_me",
          default: 0,
          onchange: () => me.assign_to_me(),
        },

        {
          label: __("Level Design"),
          fieldtype: "Check",
          fieldname: "assign_ld",
          default: 0,
          onchange: () => me.assign_ld(),
        },
        {
          label: __("Backend Programmer"),
          fieldtype: "Check",
          fieldname: "assign_be",
          default: 0,
          onchange: () => me.assign_be(),
        },
        {
          label: __("Frontend Programmer"),
          fieldtype: "Check",
          fieldname: "assign_fe",
          default: 0,
          onchange: () => me.assign_fe(),
        },
        {
          fieldtype: "Column Break",
        },
        {
          label: __("Unity Programmer"),
          fieldtype: "Check",
          fieldname: "assign_unityprog",
          default: 0,
          onchange: () => me.assign_unityprog(),
        },
        {
          label: __("Document Engineer"),
          fieldtype: "Check",
          fieldname: "assign_de",
          default: 0,
          onchange: () => me.assign_de(),
        },
        {
          label: __("Quality Assurance"),
          fieldtype: "Check",
          fieldname: "assign_qa",
          default: 0,
          onchange: () => me.assign_qa(),
        },

        {
          fieldtype: "Section Break",
        },
        {
          fieldtype: "MultiSelectPills",
          fieldname: "assign_to",
          label: __("Assign To"),
          reqd: true,
          get_data: function (txt) {
            return frappe.db.get_link_options("User", txt, {
              user_type: "System User",
              enabled: 1,
            });
          },
        },

        {
          fieldtype: "Section Break",
        },
        {
          label: __("Comment"),
          fieldtype: "Small Text",
          fieldname: "description",
        },
      ];
    }
    else if (cdRole) {
      return [
        {
          label: __("Assign to me"),
          fieldtype: "Check",
          fieldname: "assign_to_me",
          default: 0,
          onchange: () => me.assign_to_me(),
        },
        {
          fieldtype: "Section Break",
        },
        {
          fieldtype: "MultiSelectPills",
          fieldname: "assign_to",
          label: __("Assign To"),
          reqd: true,
          get_data: function (txt) {
            return frappe.db.get_link_options("User", txt, {
              user_type: "System User",
              enabled: 1,
            });
          },
        },
        {
          fieldtype: "Section Break",
        },
        {
          label: __("Comment"),
          fieldtype: "Small Text",
          fieldname: "description",
        },
      ];
    } else {
      return [
        {
          label: __("Assign to me"),
          fieldtype: "Check",
          fieldname: "assign_to_me",
          default: 0,
          onchange: () => me.assign_to_me(),
        },

        {
          fieldtype: "Section Break",
        },
        {
          fieldtype: "MultiSelectPills",
          fieldname: "assign_to",
          label: __("Assign To"),
          reqd: true,
          get_data: function (txt) {
            return frappe.db.get_link_options("User", txt, {
              user_type: "System User",
              enabled: 0,
              // filters: filters,
            });
          },
        },

        {
          fieldtype: "Section Break",
        },
        {
          label: __("Comment"),
          fieldtype: "Small Text",
          fieldname: "description",
        },
      ];
    }
  }
};

frappe.ui.form.AssignmentDialog = class {
  constructor(opts) {
    this.frm = opts.frm;
    this.assignments = opts.assignments;
    this.make();
  }

  make() {
    let juan = [];

    let sdLeadRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("leader software");

    let sdRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("technical architect");

    var cdRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("hod content");

    let filters = { name: ["like", "%" + frappe.session.user + "%"] };

    if (cdRole || sdLeadRole || sdRole || frappe.session.user === "Administrator") {
      filters = {};
    }

    juan.push({
      label: __("Assign a user"),
      fieldname: "user",
      fieldtype: "Link",
      options: "User",
      filters: filters,
      change: () => {
        let value = this.dialog.get_value("user");
        if (value && !this.assigning) {
          this.assigning = true;
          this.dialog.set_df_property("user", "read_only", 1);
          this.dialog.set_df_property(
            "user",
            "description",
            __("Assigning...")
          );
          this.add_assignment(value)
            .then(() => {
              this.dialog.set_value("user", null);
            })
            .finally(() => {
              this.dialog.set_df_property("user", "description", null);
              this.dialog.set_df_property("user", "read_only", 0);
              this.assigning = false;
            });
        }
      },
    });

    juan.push({
      fieldtype: "HTML",
      fieldname: "assignment_list",
    });
    this.dialog = new frappe.ui.Dialog({
      title: __("Assignments"),
      size: "small",
      no_focus: true,
      fields: juan,
    });

    this.assignment_list = $(this.dialog.get_field("assignment_list").wrapper);

    this.assignment_list.removeClass("frappe-control");

    this.assignments.forEach((assignment) => {
      this.update_assignment(assignment);
    });
    this.dialog.show();
  }
  render(assignments) {
    this.frm && this.frm.assign_to.render(assignments);
  }
  add_assignment(assignment) {
    return frappe
      .xcall("frappe.desk.form.assign_to.add", {
        doctype: this.frm.doctype,
        name: this.frm.docname,
        assign_to: [assignment],
      })
      .then((assignments) => {
        this.update_assignment(assignment);
        this.render(assignments);
      });
  }
  remove_assignment(assignment) {
    return frappe.xcall("frappe.desk.form.assign_to.remove", {
      doctype: this.frm.doctype,
      name: this.frm.docname,
      assign_to: assignment,
    });
  }
  update_assignment(assignment) {
    const in_the_list = this.assignment_list.find(`[data-user="${assignment}"]`)
      .length;
    if (!in_the_list) {
      this.assignment_list.append(this.get_assignment_row(assignment));
    }
  }
  get_assignment_row(assignment) {
    let sdLeadRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("leader software");

    var cdRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("hod content");

    let row = $(`
			<div class="dialog-assignment-row" data-user="${assignment}">
				<span>
					${frappe.avatar(assignment)}
					${frappe.user.full_name(assignment)}
				</span>
			</div>
		`);

    if (
      assignment === frappe.session.user ||
      this.frm.perm[0].write ||
      sdLeadRole ||
      cdRole
    ) {
      row.append(`
				<span class="remove-btn cursor-pointer">
					${frappe.utils.icon("close")}
				</span>
			`);
      row.find(".remove-btn").click(() => {
        this.remove_assignment(assignment).then((assignments) => {
          row.remove();
          this.render(assignments);
        });
      });
    }
    return row;
  }
};
