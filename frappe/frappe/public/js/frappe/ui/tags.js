// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.ui.Tags = class {
  constructor({
    parent,
    placeholder,
    tagsList,
    onTagAdd,
    onTagRemove,
    onTagClick,
    onChange,
  }) {
    this.tagsList = tagsList || [];
    this.onTagAdd = onTagAdd;
    this.onTagRemove = onTagRemove;
    this.onTagClick = onTagClick;
    this.onChange = onChange;

    this.setup(parent, placeholder);
  }

  setup(parent, placeholder) {
    this.$ul = parent;
    this.$input = $(`<input class="tags-input form-control"></input>`);

    this.$inputWrapper = this.get_list_element(this.$input);
    this.$placeholder = this.get_list_element(
      $(`<span class="tags-placeholder text-muted">${placeholder}</span>`)
    );
    this.$inputWrapper.appendTo(this.$ul);
    this.$placeholder.appendTo(this.$ul);

    this.deactivate();
    this.bind();
    this.boot();
  }

  bind() {
    var cdRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("content");

    let sdRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("technical architect");

    let sdLeadRole = frappe.user_roles
      .join(",")
      .toLowerCase()
      .includes("leader software");

    const me = this;
    const select_tag = function () {
      const tagValue = frappe.utils.xss_sanitise(me.$input.val());
      me.addTag(tagValue);
      me.$input.val("");
    };

    this.$input.keypress((e) => {
      if (e.which == 13 || e.keyCode == 13) select_tag();
    });
    this.$input.focusout(select_tag);

    this.$input.on("blur", () => {
      this.deactivate();
    });

    if (sdLeadRole || sdRole || frappe.session.user === "Administrator") {
      this.$placeholder.on("click", () => {
        this.activate();
        this.$input.focus(); // focus only when clicked
      });
    } else this.$placeholder.html("No tags added");

    if (cdRole) {
      this.$placeholder.html("Tags is not available in your division");
    }
  }

  boot() {
    this.addTags(this.tagsList);
  }

  activate() {
    this.$placeholder.hide();
    this.$inputWrapper.show();
  }

  deactivate() {
    this.$inputWrapper.hide();
    this.$placeholder.show();
  }

  addTag(label) {
    if (label && label !== "" && !this.tagsList.includes(label)) {
      let $tag = this.get_tag(label);
      let row = this.get_list_element($tag, "form-tag-row");
      row.insertBefore(this.$inputWrapper);
      this.tagsList.push(label);
      this.onTagAdd && this.onTagAdd(label);
    }
  }

  removeTag(label) {
    label = frappe.utils.xss_sanitise(label);
    if (this.tagsList.includes(label)) {
      this.tagsList.splice(this.tagsList.indexOf(label), 1);
      this.onTagRemove && this.onTagRemove(label);
    }
  }

  addTags(labels) {
    labels.map(this.addTag.bind(this));
  }

  clearTags() {
    this.$ul.find(".form-tag-row").remove();
    this.tagsList = [];
  }

  get_list_element($element, class_name = "") {
    let $li = $(`<li class="${class_name}"></li>`);
    $element.appendTo($li);
    return $li;
  }

  get_tag(label) {
    let $tag = frappe.get_data_pill(label, label, (target, pill_wrapper) => {
      this.removeTag(target);
      pill_wrapper.closest(".form-tag-row").remove();
    });

    if (
      !(
        frappe.user.has_role("Software Developer") != 1 ||
        frappe.session.user === "Administrator"
      )
    )
      $tag.find(".remove-btn").remove();

    if (this.onTagClick) {
      $tag.on("click", ".pill-label", () => {
        this.onTagClick(label);
      });
    }

    return $tag;
  }
};
