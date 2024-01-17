frappe.provide("erpnext.timesheet");

const momentDurationFormatSetup = frappe.require(
  "/assets/erpnext/js/projects/moment-duration-format.js"
);

function checkSubTaskVisibility() {
  var userRole = frappe.user_roles
    .join(",")
    .toLowerCase()
    .includes("content");

  return !userRole;
}

function checkDependsOnCondition(doc) {
  // var hasContentRole = frappe.user.has_role('Content Developer Staff') || frappe.user.has_role('HOD Content Division');

  var userRole = frappe.user_roles
    .join(",")
    .toLowerCase()
    .includes("content");

  // alert(userRole)
  if (!userRole) {
    return checkSubTaskLength(doc.task).length > 0;
  }
  else {
    return false
  }
}

function checkSubTaskLength(doc) {

  var subTasks = [];

  frappe.call({
    method: "frappe.client.get_list",
    args: {
      doctype: "Task",
      filters: { subject: doc },
      fields: ["sub_task.sub_task"]
    },
    async: false,
    callback: function (response) {
      if (response && response.message) {
        subTasks = response.message.map(entry => entry.sub_task ? entry.sub_task[0].sub_task : null);
        subTasksFilter = subTasks.filter(subTask => {
          if (subTask !== null) {
            return true;
          }
          return false;
        });
      }
    },
  });
  return subTasksFilter;
}


function convertTime(seconds) {
  var seconds = parseInt(seconds, 10);
  var hours = Math.floor(seconds / 3600);
  var minutes = Math.floor((seconds - hours * 3600) / 60);
  var seconds = seconds - hours * 3600 - minutes * 60;
  if (!!hours) {
    if (!!minutes) {
      return `${hours}h ${minutes}m ${seconds}s`;
    } else {
      return `${hours}h ${seconds}s`;
    }
  }
  if (!!minutes) {
    return `${minutes}m ${seconds}s`;
  }
  return `${seconds}s`;
}

erpnext.timesheet.auto_complete_timers = function () {
  frappe.run_serially([
    () =>
      frappe.call({
        method: "erpnext.js.projects.auto_complete_timers",
        callback: function (r) {
          if (r.message) {
            console.log("Timers auto-completed successfully:", r.message);
          } else {
            console.error("Error auto-completing timers:", r.exc);
          }
        },
      }),
  ]);
};

erpnext.timesheet.timer = function (frm, row, timestamp = 0) {
  let user_roles = frappe.user_roles;
  let dialog = new frappe.ui.Dialog({
    title: __("Timer"),
    fields: [
      {
        fieldtype: "Link",
        label: __("Project"),
        fieldname: "project",
        reqd: 1,
        //options: "Project",
        // options: user_roles.includes("Administrator")
        options: user_roles.join(",").toLowerCase().includes("content")
          ? "CD Project"
          : "Project",
        filters: { _assign: ["like", "%" + frappe.session.user + "%"] },
      },
      {
        fieldtype: "Link",
        label: __("Activity Type"),
        fieldname: "activity_type",
        reqd: 1,
        options: user_roles.join(",").toLowerCase().includes("content")
          ? "CD Activity Type"
          : "Activity Type",
      },
      {
        fieldtype: "Link",
        label: __("Task"),
        fieldname: "task",
        reqd: 1,
        // options: "Task",
        // options: user_roles.includes("Administrator") ? "CD Task" : "Task",
        options: user_roles.join(",").toLowerCase().includes("content")
          ? "CD Task"
          : "Task",
      },
      {
        fieldtype: "Link",
        label: __("SD Sub Task"),
        fieldname: "sub_task",
        // reqd: "eval: (function() { return 0})",
        // options: "Task",
        // options: user_roles.includes("Administrator") ? "CD Task" : "Task",
        options: user_roles.join(",").toLowerCase().includes("content")
          ? "CD Task"
          : "SD Sub Task",
        // depends_on: "eval: ((function() { console.log('Sub Task Length:', doc); })() || true) ",
        depends_on: "eval: (function() { return  checkDependsOnCondition(doc) && (!frappe.user.has_role('Content Developer Staff') || !frappe.user.has_role('HOD Content Division')); })()",
        // hidden: "eval: (function() { return  checkSubTaskVisibility() ); })()",

      },
      {
        fieldtype: "Int",
        label: __("Expected Minutes"),
        reqd: 1,
        fieldname: "expected_hours",
      },
      { fieldtype: "Section Break" },
      { fieldtype: "HTML", fieldname: "timer_html" },
    ],
  });

  dialog.fields_dict.task.get_query = function (frm, cdt, cdn) {
    // var child = locals[cdt][cdn];
    var project = cur_dialog.fields_dict.project.value;

    // var userRole = frappe.user_roles.includes("Administrator");
    var userRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("content");

    if (userRole) {
      return {
        filters: {
          project: project,
          status: ["!=", "Cancelled"],
          _assign: ["like", "%" + frappe.session.user + "%"],
        },
      };
    } else {
      return {
        filters: {
          project: project,
          status: ["!=", "Cancelled"],
          ongoing_sprint: ["!=", ""],
          _assign: ["like", "%" + frappe.session.user + "%"],
        },
      };
    }
  };

  dialog.fields_dict.sub_task.get_query = function (frm, cdt, cdn) {
    var selected_task = cur_dialog.fields_dict.task.value;


    // var selected_sub_task = cur_dialog.fields_dict.sub_task.value.length;
    // console.log(selected_sub_task)
    var userRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("content");

    if (!userRole) {
      return {
        filters: {
          task: selected_task,
          status: ["!=", "Cancelled"],
          _assign: ["like", "%" + frappe.session.user + "%"],
        },
      };
    }
  };

  if (row) {
    dialog.set_values({
      activity_type: row.activity_type,
      project: row.project,
      task: row.task,
      sub_task: row.sub_task,
      expected_hours: row.expected_hours,
    });
  }
  dialog.get_field("timer_html").$wrapper.append(get_timer_html());
  function get_timer_html() {
    return `
			<div class="stopwatch text-center" style="font-size:35px;">
				<span class="hours">00</span>
				<span class="colon">:</span>
				<span class="minutes">00</span>
				<span class="colon">:</span>
				<span class="seconds">00</span>
			</div>
			<br>
			<div class="playpause text-center">
				<button class= "btn btn-primary btn-start"> ${__("Start")} </button>
				<button class= "btn btn-primary btn-complete"> ${__("Complete")} </button>
			</div>
		`;
  }
  erpnext.timesheet.control_timer(frm, dialog, row, timestamp);
  dialog.show();
};

erpnext.timesheet.control_timer = function (frm, dialog, row, timestamp = 0) {
  var $btn_start = dialog.$wrapper.find(".playpause .btn-start");
  var $btn_complete = dialog.$wrapper.find(".playpause .btn-complete");
  var interval = null;
  var currentIncrement = timestamp;
  var initialized = row ? true : false;
  var clicked = false;
  var flag = true; // Alert only once
  // If row with not completed status, initialize timer with the time elapsed on click of 'Start Timer'.
  if (row) {
    initialized = true;
    $btn_start.hide();
    $btn_complete.show();
    initializeTimer();
  }

  if (!initialized) {
    $btn_complete.hide();
  }

  $btn_start.click(function (e) {
    if (!initialized) {
      // New activity if no activities found
      var args = dialog.get_values();
      if (!args) return;

      var userRole = frappe.user_roles
        .join(",")
        .toLowerCase()
        .includes("content");

      if (!userRole) {
        if (checkSubTaskLength(args.task).length > 0 && args.sub_task == undefined) {
          frappe.msgprint(__("Sub Task cannot be null. Please select a sub task."));
          throw __("Sub Task cannot be null.");
        }
      }

      if (
        frm.doc.time_logs.length <= 1 &&
        !frm.doc.time_logs[0].activity_type &&
        !frm.doc.time_logs[0].from_time
      ) {
        frm.doc.time_logs = [];
      }


      var childType = frappe.user_roles
        .join(",")
        .toLowerCase()
        .includes("content")
        ? "CD Timesheet Detail"
        : "Timesheet Detail";

      row = frappe.model.add_child(frm.doc, childType, "time_logs");
      row.activity_type = args.activity_type;
      row.from_time = frappe.datetime.get_datetime_as_string();
      row.project = args.project;
      row.task = args.task;
      row.sub_task = args.sub_task;
      row.expected_hours = args.expected_hours;
      row.expected_hours_count = args.expected_hours;
      row.expected_hours_count = moment
        .utc(((args.expected_hours * 1000) / 60) * 3600)
        .format("HH:mm:ss");

      // const duration = moment.duration(args.expected_hours, 'minutes')
      // const format = Math.floor(duration.asHours()) + ':' + duration.minutes() + ':' + duration.seconds()
      // alert(row.expected_hours_count)
      row.completed = 0;
      let d = moment(row.from_time);
      if (row.expected_hours) {
        d.add(row.expected_hours, "hours");
        row.to_time = d.format(frappe.defaultDatetimeFormat);
      }
      frm.refresh_field("time_logs");
      frm.save();
    }

    if (clicked) {
      e.preventDefault();
      return false;
    }

    if (!initialized) {
      initialized = true;
      $btn_start.hide();
      $btn_complete.show();
      initializeTimer();
    }
  });

  // Stop the timer and update the time logged by the timer on click of 'Complete' button
  $btn_complete.click(function () {
    var grid_row = cur_frm.fields_dict["time_logs"].grid.get_row(row.idx - 1);
    var args = dialog.get_values();

    var userRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("content");

    if (!userRole) {
      if (checkSubTaskLength(args.task).length > 0 && args.sub_task === undefined) {
        frappe.msgprint({
          title: __("Sub Task is Null"),
          message: __("Sub Task cannot be null. Please select a sub task."),
        });
        throw __("Sub Task cannot be null.");
      }
    }

    grid_row.doc.completed = 1;
    grid_row.doc.activity_type = args.activity_type;
    grid_row.doc.project = args.project;
    grid_row.doc.task = args.task;
    grid_row.doc.sub_task = args.sub_task;
    console.log(grid_row.doc)
    console.log(grid_row.doc.sub_task)
    grid_row.doc.expected_hours = args.expected_hours;
    grid_row.doc.expected_hours_count = moment
      .utc(((args.expected_hours * 1000) / 60) * 3600)
      .format("HH:mm:ss");
    grid_row.doc.hours = currentIncrement / 3600;
    grid_row.doc.hrs = grid_row.doc.hours;
    grid_row.doc.to_time = frappe.datetime.now_datetime();
    let actualTimeMoment = moment.utc(currentIncrement * 1000);
    // Get the numeric value of the Moment object in milliseconds
    let actualTimeFloat = actualTimeMoment.valueOf();

    // Convert milliseconds to seconds (if needed)
    grid_row.doc.actual_time_float = actualTimeFloat;
    // grid_row.doc.hours_count = moment
    //   .utc(currentIncrement * 1000)
    //   .format("HH:mm:ss");

    // alert(currentIncrement / 3600);
    // let durationInSeconds = currentIncrement / 3600;

    // console.log(currentIncrement);

    alert("SECOND : " + currentIncrement);
    alert("HOURS : " + currentIncrement / 3600);
    // alert(moment({}).seconds(currentIncrement).format("D [days], HH:mm:ss"));

    if (currentIncrement >= 86400) {
      grid_row.doc.hours_count = moment
        .duration(currentIncrement, "seconds")
        .format("D [days], HH:mm:ss");

      alert(
        moment.duration(currentIncrement, "second").format("D [days], HH:mm:ss")
      );
    } else {
      grid_row.doc.hours_count = moment
        .utc(currentIncrement * 1000)
        .format("HH:mm:ss");

      alert(moment.utc(currentIncrement * 1000).format("HH:mm:ss"));
    }

    // if (currentIncrement / 3600 < 24) {
    //   grid_row.doc.hours_count = moment
    //     .duration(currentIncrement, "seconds")
    //     .format("HH:mm:ss");
    //   // grid_row.doc.hours_count = moment(currentIncrement).format("HH:mm:ss");
    //   alert(grid_row.doc.hours_count);
    // }

    grid_row.refresh();
    frm.dirty();
    frm.save();
    reset();
    dialog.hide();
  });

  function initializeTimer() {
    interval = setInterval(function () {
      var current = setCurrentIncrement();
      updateStopwatch(current);
    }, 1000);
  }

  function updateStopwatch(increment) {
    var hours = Math.floor(increment / 3600);
    var minutes = Math.floor((increment - hours * 3600) / 60);
    var seconds = increment - hours * 3600 - minutes * 60;

    // If modal is closed by clicking anywhere outside, reset the timer
    if (!$(".modal-dialog").is(":visible")) {
      reset();
    }
    if (hours > 99999) reset();
    if (cur_dialog && cur_dialog.get_value("expected_hours") > 0) {
      if (
        flag &&
        currentIncrement >= cur_dialog.get_value("expected_hours") * 3600
      ) {
        frappe.utils.play_sound("alert");
        frappe.msgprint(__("Timer exceeded the given hours."));
        flag = false;
      }
    }
    $(".hours").text(hours < 10 ? "0" + hours.toString() : hours.toString());
    $(".minutes").text(
      minutes < 10 ? "0" + minutes.toString() : minutes.toString()
    );
    $(".seconds").text(
      seconds < 10 ? "0" + seconds.toString() : seconds.toString()
    );
  }

  function setCurrentIncrement() {
    currentIncrement += 1;
    return currentIncrement;
  }

  function reset() {
    currentIncrement = 0;
    initialized = false;
    clearInterval(interval);
    $(".hours").text("00");
    $(".minutes").text("00");
    $(".seconds").text("00");
    $btn_complete.hide();
    $btn_start.show();
  }
};
