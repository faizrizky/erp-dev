frappe.pages['project_gantt'].on_page_load = function(wrapper) {
	var page = new CustomReportPages(wrapper);
}



// PAGES CONTENT
CustomReportPages = Class.extend({
	init : function (wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Project Dashboard',
			single_column: true
		});
		window.pages = this.page;
	
		this.make(() => {
			this.intialFilters();
		});
	},

	intialFilters : function() {
		
		_this = this;

		frappe.call({
			method : "erpnext.devproj.page.project_gantt.project_gantt.get_project",
			callback : function(r) { 
				console.log('test',r);
				let field = _this.page.add_field({
					label: 'Status',
					fieldtype: 'MultiSelectPills',
					fieldname: 'status',
					"options": r.message,
					change() {
						console.log(field.get_value());
					}
				})
				$(field.wrapper).removeClass("col-md-2");
				$(field.wrapper).addClass("col-md-4");

				// initial gannt chart 

				_this.add_section_gantt(r.message, _this);
			}
		});
	},

	make : function(cb) {
		let me = $(this);
		let body = /*html*/`<h1>lorem ipsum</h1>`;

		$(frappe.render_template(frappe.test_app_page.body,this)).appendTo(this.page.main);
		
		frappe.require([
			"assets/frappe/node_modules/frappe-gantt/dist/frappe-gantt.css",
			"assets/frappe/node_modules/frappe-gantt/dist/frappe-gantt.min.js",
		],() => {
			cb();
		});

	},

	/**
	 * Add Individual Gantt That Calling in add_section_gantt
	 * @param {*} title 
	 */
	add_gantt_chart : async (title) => {

		let id = toKebabCase(title);

		frappe.call({
			method : "erpnext.devproj.page.project_gantt.project_gantt.get_task",
			callback : function(r) { 

				console.log(r.message);
				var gantt = new Gantt("#" + id, r.message);

				$("#loading-" + id).remove();

				$("#" + id).removeClass('d-none');
			}
		})

	},

	add_section_gantt : (projects, _this) => {
		var ganttContainerLog = $('#container-gantt-log');

		// clean state
		ganttContainerLog.innerHTML = "";

		projects.forEach(element => {
			ganttContainerLog.append(frappe.test_app_page.ganttTemplate(element, toKebabCase(element)));
			_this.add_gantt_chart(element);
		});
	},

})

frappe.test_app_page = {
	body : /*html*/`<div>
		<div id="container-gantt-log">
		
	</div>`,
	ganttTemplate : function(title,id) {
		return /*html */`
		<div>
			<h3 class="mt-3"> ${title} </h3>
			<div class="d-flex align-items-center" style="height:200px" id="loading-${id}">
				<div class="spinner-grow" style="width: 3rem; height: 3rem;" role="status">
					<span class="sr-only">Loading...</span>
				</div> <h4 class="my-auto ml-2"> Loading...</h4>
			</div>
		</div>
		
		<div class="holder-gantt d-block">
			<svg id="${id}" class="d-none"></svg>
		</div>
	`
	}
}

const toKebabCase = str =>
  str &&
  str
    .match(/[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+/g)
    .map(x => x.toLowerCase())
    .join('-');