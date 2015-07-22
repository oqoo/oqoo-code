/*---------------------------------------------------------
 * OpenERP mobile widget library
 *---------------------------------------------------------*/

(function() {

var instance = openerp;
instance.web.mobile = {};
var QWeb = instance.web.qweb,
    _t = instance.web._t
    _mobile = instance.web.mobile;

_mobile._modules = (_mobile._modules || []).concat(["mobile"]);

instance.web.Session.include({
	session_init: function () {
        var self = this;
        return self.session_reload().then(function(result) {
            var modules = _mobile._modules.join(',');
            return self.load_qweb(modules);
        });
    },
    
    session_reload: function () {
        var self = this;
        return self.rpc("/mobile/session/get_session_info", {}).then(function(result) {
            delete result.session_id;
            _.extend(self, result);
        });
    }
    
});

// extension to DataSet
_mobile.DataSetSearch =  instance.web.DataSetSearch.extend({
	init: function(parent, model, context, domain){
		var ctx = _mobile.parseJSON( context || {} ),
			dom = _mobile.parseJSON( domain || {} );
        this._super(parent, model, ctx, dom);
	},
	save_batch: function (data, options) {
        options = options || {};
        var self = this;
        return this._model.call('save_batch', [data], {
            context: this.get_context(options.context)
        }).done(function () {
            self.trigger('dataset_changed', data, options);
        });
    },
    read_any: function(fields, options){
    	var self = this;
    	options = options || {};
    	
    	var groupby = self.context.group_by,
    		groupflag = groupby && groupby.length > 0,
    		deferred;
    	if(groupflag){
    		deferred = self.call('read_group', {
                fields  : fields,
                groupby : groupby,
                domain  : self._model.domain(options.domain),
                context : self._model.context(options.context),
                offset  : options.offset,
    			limit   : options.limit,
    			orderby : options.orderby || options.order || options.sort,
                lazy    : false
            });
    	}else{
    		deferred = self.read_slice(fields, options);
    	}
    	
    	return deferred.then(function (records) {

    		if(groupflag){
    			_.chain(groupby)
    			.filter(function(e){return e.indexOf(":")>0})
    			.reduce(function(memo, e){memo[e] = e.split(":")[0]; return memo;},{})
    			.each(function(v, k, l){
    					_.each(records, function(r, idx){
    						r[v] = r[k];
    					});
    				});
    		}
            return records;
        });
    }
});

_mobile.DictStore = instance.web.Class.extend({
    /**
     * Dict Store
     *
     * @constructs DictStore
     * @extends instance.web.Class
     * 
     * @param {Object} [options]
     */
    init: function (options) {
    	var self = this;
        options = options || {};
        self.records = [];
        self.dataset = new _mobile.DataSetSearch(this, options.model, options.context, options.domain);
        self.loaded = $.Deferred();
        self.lazy = options.lazy;
        
        if(!self.lazy){
        	self.load_records();
        }
    },
    /**
     * load records from database
     *
     * @returns {Array}[Records]
     */
    load_records: function(){
    	var self = this;
    	return self.dataset.name_search().done(function(records) {
    		self.records = records;
    		self.loaded.resolve(records);
    	});
    },
    /**
     * Get a record by its index in the dict store
     *
     * @param {Number} index
     * @returns {Record|null}
     */
    at: function (index) {
        var self = this;
    	return self.loaded.then(function(){
    		if( self.records.length > 0 && index < self.records.length && index>=0 ){
                return self.records[index];
            }
    		return null;
    	});
    },
    /**
     * Get a record by its database id
     *
     * @param {Number} id
     * @returns {Record|undefined}
     */
    get: function (id) {
    	var self = this;
    	return self.loaded.then(function(){
    		return _(self.records).find(function (record) {
                return record["id"] == id;
            });
    	});
    },
    /**
     * Get all records
     *
     * @returns {Array} [records]
     */
    data: function () {
    	return this.loaded;
    },
    /**
     * @param {Array} [records]
     * @returns this
     */
    reset: function (options) {
    	var self = this;
        options = options || {};
        self.records = [];
        self.loaded = $.Deferred();
        
        if(options.lazy !== undefined){
        	self.lazy = options.lazy;
        }
        
        if(!self.lazy){
        	self.load_records();
        }
    },
});

_mobile.Context = instance.web.Class.extend(instance.web.EventDispatcherMixin, {
    /**
     * context management.
     * @constructs instance.web.mobile.Context
     */
    init: function(parent) {
        instance.web.EventDispatcherMixin.init.call(this, parent);
        this.__innerMap = {};
    },
    set: function(arg1, arg2, arg3) {
        var map;
        var options;
        if (typeof arg1 === "string") {
            map = {};
            map[arg1] = arg2;
            options = arg3 || {};
        } else {
            map = arg1;
            options = arg2 || {};
        }
        var self = this;
        var changed = false;
        _.each(map, function(val, key) {
            var tmp = self.__innerMap[key];
            if (_.isEqual(tmp, val))
                return;
            changed = true;
            self.__innerMap[key] = val;
            if (! options.silent)
                self.trigger("change:" + key, self, {
                    oldValue: tmp,
                    newValue: val
                });
        });
        if (changed)
            self.trigger("change", self);
    },
    get: function(key) {
    	return this.__innerMap[key]? this.__innerMap[key]:null;
    },
    setAll: function(arg1, arg2, arg3) {
        var map;
        var options;
        if (typeof arg1 === "string") {
            map = {};
            map[arg1] = arg2;
            options = arg3 || {};
        } else {
            map = arg1;
            options = arg2 || {};
        }
        var self = this;
        
        if(!_.isEqual(this.__innerMap, map)){
        	this.__innerMap = $.extend({}, map);
        	if (! options.silent)
            	self.trigger("change", self);
        }
    },
    getAll: function(){
    	return this.__innerMap;
    }
});

_mobile.CrashManager = instance.web.Class.extend({
    init: function() {
        
    },
/*
{
  "jsonrpc": "2.0",
  "error"  : {
	"code"    : code,
    "message" : "End user error message.",
    "data"    : {
	  "name": "name",
      "debug": "traceback",
      "message": "message",
      "arguments": "arguments",
      "exception_type": "exception_type"
	}
  }
}
*/
    rpc_error: function(error) {
        var handler = _mobile.crash_manager_registry.get_object(error.data.name, true);
        if (handler) {
            new (handler)(this, error).display();
            return;
        }
        if (error.data.name === "openerp.http.SessionExpiredException" || error.data.name === "werkzeug.exceptions.Forbidden") {
            this.show_warning({
            	type: "Session Expired", 
            	data: { message: _t("Your session expired. Please refresh the current web page.") }});
            return;
        }
        if (error.data.exception_type === "except_osv" || error.data.exception_type === "warning" || error.data.exception_type === "access_error") {
            this.show_warning(error);
        } else {
            this.show_error(error);
        }
    },
    show_warning: function(error) {
        if (error.data.exception_type === "except_osv") {
            error = _.extend({}, error, {data: _.extend({}, error.data, {message: error.data.arguments[0] + "\n\n" + error.data.arguments[1]})});
        }
        $("#popupError h1").html(error.type?error.type:"Server Warning");
        $("#popupError .oex-errmsg").html(error.data.message || error.message);
        $("#popupError").popup("open");
    },
    show_error: function(error) {
        $("#popupError h1").html(error.type?error.type:"Server Error");
        $("#popupError .oex-errmsg").html(error.data.message || error.message);
        $("#popupError").popup("open");
    },
    show_message: function(exception) {
        this.show_error({
            type: _t("Client Error"),
            message: exception
        });
    },
});
_mobile.ExceptionHandler = {
	init: function(parent, error) {},
	display: function() {},
};
_mobile.crash_manager_registry = new instance.web.Registry();

_mobile.Widget = instance.web.Widget.extend({

    setElement: function (element) {
    	this._super(element);
    	this.$el.data("oe-instance", this);
        return this;
    },
    //refresh the view(layout,style)
    refresh: function(){},
    //reload data
    reload: function(){
    	return $.when();
    },
    trigger: function(e){
    	this._super(arguments);
    	this.$().trigger(e+":oexevent", Array.prototype.slice.call(arguments, 1));
    },
    triggerWithResult: function(e){
    	if(!(e instanceof $.Event)){
    		e = new jQuery.Event(e);
    	}
    	this.$().trigger(e, Array.prototype.slice.call(arguments, 1));
    	return e;
    }
});

/**
 * page container.
 */
_mobile.Pagecontainer = _mobile.Widget.extend({
    init: function(parent, options) {
        this._super(parent);
        this.$doc = $.mobile.document;
        this.$wnd = $.mobile.window;
        if (options) {
            _.extend(this.options, options);
        }
        this._current_state = null;
    },
    start: function() {
        var self = this;
        return instance.session.session_bind(this.origin).then(function() {
        
            self.bind_events();
            self.show_common();
            if (self.session.session_is_valid()) {
                self.show_application();
            }
            /*
            if (self.client_options.action) {
                self.action_manager.do_action(self.client_options.action);
                delete(self.client_options.action);
            }
            */
        });
    },
    bind_events: function() {
        var self = this;
        
        self.$doc.on("pagebeforecreate", function(event){
        	//alert("pagebeforecreate!");
        });
        
        self.$doc.on("pagecreate", function(event){
        	//alert("pagecreate!");
        });
        
		self.$doc.on("pageinit", function(event){
			//$(event.target).find(":jqmData(role=content)").prepend("<ul data-role='listview'> <li>Acura</li><li>Ferrari</li></ul>");
			//alert(event.target.id);
		});
		
		self.$wnd.on("pagecontainercreate", function(event){
			// reset the $.mobile.firstpage before changing to if needed. If not, the first page will be shown.
			var firstpage = self.getFirstpage();
			if(firstpage){
				$.mobile.firstPage = $("#" + firstpage);
			}
		});
		
		//self.$doc.on("pagecontainerbeforechange", function(event, ui){
		self.$doc.on("pagecontainerbeforetransition", function(event, ui){
			//alert(ui.toPage);
			
			var $page;
			if(typeof(ui.toPage) == 'string'){
				$page = $('#' + ui.toPage.replace( /^[^#]*#?(.*)$/, '$1' ));
			}else{
				$page = ui.toPage;
			}
			
			var page = $page.data("oe-instance");
			if(!page){
				page = new _mobile.Page(this, $.extend(true, {}, $page.data()));
				if(_mobile.changepagedata){
					page.pagecontext.setAll(_mobile.changepagedata);
					_mobile.changepagedata = null;
				}
				page.setElement($page);
				page.start();
			}else{
				if( ui.options.direction == "back" || ui.options.direction == "forward" 
					|| _mobile.isEqual(_mobile.changepagedata, page.pagecontext.getAll())){
					page.renderWithin();
				}else{
					if(_mobile.changepagedata){
						page.pagecontext.setAll(_mobile.changepagedata);
						_mobile.changepagedata = null;
					}
					page.reload();
				}
			}
		});
		
		// build context
		self.$doc.on("vclick", ".oex-changepage", function(event){
			
	        var context = $(event.target).data("context");
            context = _mobile.parseJSON(context) || {};
            
	        //var fields_values = this.field_manager.build_eval_context();
	        //v_context = new instance.web.CompoundContext(v_context).set_eval_context(fields_values);
			
			if(typeof(context) != "object"){
				context = {context: context};
			}
			
	        _mobile.changepagedata = context;
		});
		
		/*
        instance.web.bus.on('click', this, function(ev) {
            $('.tooltip').remove();
            if (!$(ev.target).is('input[type=file]')) {
                self.$el.find('.oe_dropdown_menu.oe_opened, .oe_dropdown_toggle.oe_opened').removeClass('oe_opened');
            }
        });
        */
    },
    show_common: function() {
        var self = this;

        self.crashmanager =  new _mobile.CrashManager();
        instance.session.on('error', self.crashmanager, self.crashmanager.rpc_error);

        window.onerror = function (message, file, line) {
            self.crashmanager.show_error({
                type: _t("Client Error"),
                message: message,
                data: {debug: file + ':' + line}
            });
        };
    },
    show_application: function() {
        var self = this;

        // Menu is rendered server-side thus we don't want the widget to create any dom
        //self.menu = new instance.web.Menu(self);
        //self.menu.setElement(this.$el.parents().find('.oe_application_menu_placeholder'));
        //self.menu.start();
        //self.menu.on('menu_click', this, this.on_menu_action);

        // self.bind_hashchange();
		/*
        if (self.client_options.action_post_login) {
            self.action_manager.do_action(self.client_options.action_post_login);
            delete(self.client_options.action_post_login);
        }
		*/
		
		// determinate the first page
		this.firstPage = this.getFirstpage();
		
		// initialize page manually
		$.mobile.initializePage();
		
    },

    getFirstpage: function() {
		if(!this.firstPage){
			var firstPage = "page1";
			this.firstPage = firstPage;
		}
		return this.firstPage;
    },

    destroy_content: function() {
        _.each(_.clone(this.getChildren()), function(el) {
            el.destroy();
        });
        this.$el.children().remove();
    },
    do_reload: function() {
        var self = this;
        return this.session.session_reload().then(function () {
            instance.session.load_modules(true).then(
                self.menu.proxy('do_reload')); });
    },
    do_notify: function() {

    },
    do_warn: function() {

    },
    on_logout: function() {

    },
    bind_hashchange: function() {
        var self = this;
        $(window).bind('hashchange', this.on_hashchange);

        var state = $.bbq.getState(true);
        if (_.isEmpty(state) || state.action == "login") {
            self.menu.is_bound.done(function() {
                new instance.web.Model("res.users").call("read", [self.session.uid, ["action_id"]]).done(function(data) {
                    if(data.action_id) {
                        self.action_manager.do_action(data.action_id[0]);
                        self.menu.open_action(data.action_id[0]);
                    } else {
                        var first_menu_id = self.menu.$el.find("a:first").data("menu");
                        if(first_menu_id) {
                            self.menu.menu_click(first_menu_id);
                        }
                    }
                });
            });
        } else {
            $(window).trigger('hashchange');
        }
    },
    on_hashchange: function(event) {
        var self = this;
        var stringstate = event.getState(false);
        if (!_.isEqual(this._current_state, stringstate)) {
            var state = event.getState(true);
            if(!state.action && state.menu_id) {
                self.menu.is_bound.done(function() {
                    self.menu.menu_click(state.menu_id);
                });
            } else {
                state._push_me = false;  // no need to push state back...
                this.action_manager.do_load_state(state, !!this._current_state);
            }
        }
        this._current_state = stringstate;
    },
    do_push_state: function(state) {
        this.set_title(state.title);
        delete state.title;
        var url = '#' + $.param(state);
        this._current_state = $.deparam($.param(state), false);     // stringify all values
        $.bbq.pushState(url);
        this.trigger('state_pushed', state);
    },
});
_mobile.pagecontainer = new _mobile.Pagecontainer();

_mobile.Page = _mobile.Widget.extend({
    //template:  "",
    init: function(parent, options) {
        this._super(parent);
        
        options = options || {};
    	this._template = options.template;
    	this.context = options.context;
    	this.pagecontext = new _mobile.Context();
        //this.flags = flags || {};
        this.view_completely_inited = $.Deferred();
    },
    /**
     * @returns {jQuery.Deferred} initial view loading promise
     */
    start: function() {
        this._super();
        
        var self = this;
        
        // refresh when context changed
        // self.pagecontext.on("change", self, self.refresh);
		
		// initialize widgets
		self.render();
		
		return self.renderWithin().then(function(){
			//p.data("init", true);
			self.$el.enhanceWithin();
		});
    },
	render: function() {
		var self = this;
        if (self._template) {
            var html = QWeb.render(self._template, {'widget':self, 'utils': _mobile.utils}).trim();
            self.$el.empty().html(html);
        }
        //title
        var titlegen = self.$el.jqmData("title-gen");
        if(titlegen){
        	self.$el.jqmData( "title", eval(titlegen) );
        }
    },
    /**
     * @param opertype Operation type when widget exists. false means refresh and true means reload.
     */
    renderWithin: function(opertype){
    	
    	var self = this;
    	//look up eXtended ELementS
    	var xels = self.$el.find(":jqmData(oextype)");
    	
    	var deferreds = [];
    	$.each( xels, function( i, n ) {
    		
    		var widget = $(this).data("oe-instance");
    		if(widget){
    			deferreds.push(widget.reload().then(function(){widget.refresh();}));
    		}else{
	    		var widgetClass = _mobile.widgets.get_object($(this).jqmData("oextype"));
	    		
				// If initSelector not false find elements
				if ( widgetClass ) {
					 widget = new widgetClass(self, $(this).data());
					 widget.setElement($(this));
					 deferreds.push(widget.start());
				}
			}
		});
		
		return $.when.apply($, deferreds);
    },
    /**
     * 
     */
    reload: function(){
    	var self = this;
    	self.render();
		return self.renderWithin().then(function(){
			//p.data("init", true);
			self.$el.enhanceWithin();
		});
    },
});

_mobile.List = _mobile.Widget.extend({
	template: "list",
	//init: function(parent, dataset, view_id, options) {
	init: function(parent, options) {
        var self = this;
        this._super(parent);
        options = options || {};
        
        self.options = options;
        //var dataset = new instance.web.DataSetSearch(this, action.res_model, context, action.domain);
        //this.dataset = dataset;
        self.model = options.model;
        self.dataset = new _mobile.DataSetSearch(this, self.model, options.context, options.domain);
        self.fields = _mobile.parse(options.fields);
        //self.records = new openerp.web.list.Collection();
        self.records = [];
        self.row_template = options.rowtemplate;
        
        //self.view_id = view_id;
        //self.previous_colspan = null;
        self.columns = [];
        self.page = 0;
        self.no_leaf = false;
        self.grouped = false;
    },
    /**
     * @returns {jQuery.Deferred} initial view loading promise
     */
    start: function() {
    	var self = this;
        self.render();
        return self.load_data();
    },
    render: function(options){
    	var self = this;
        var list = $(QWeb.render(self.template, self).trim());
        self.$el.html(list);
        self.$contentEl = list.filter(".oex-list");
    },
    reload: function(options){
    	return this.load_data(options || {}, true);
    },
    refresh: function(){
    	this.$contentEl.listview("refresh");
    	this.$contentEl.enhanceWithin();
    },
    load_data: function(options, reset){
    	var self = this;
    	
    	//var options = { offset: page * limit, limit: limit, context: {bin_size: true} };
    	var fields = _.keys(self.fields);
    	options = options || {};
    	return self.dataset.read_any(fields, options).then(function (records) {
    		/*
    		if (reset && self.records.length) {
                self.records.reset(null, {silent: true});
                self.$contentEl.empty();
            }
            self.records.add(records, {silent: true});
            */
    		if (reset && self.records.length) {
                self.records = [];
                self.$contentEl.empty();
            }
    		
    		self.trigger("data_loaded", self, records);
    		self.records = _.union(self.records, records);
            
            var html = QWeb.render(self.row_template, {records: records});
            self.$contentEl.append(html);
        });
    },
    /*
    select_row: function (index, view) {
        view = view || index === null || index === undefined ? 'form' : 'form';
        this.dataset.index = index;
        _.delay(_.bind(function () {
            this.do_switch_view(view);
        }, this));
    },
    row_clicked: function (e, view) {
        $(this).trigger(
            'row_link',
            [this.dataset.ids[this.dataset.index],
             this.dataset, view]);
    },
    row_id: function (row) {
        return $(row).data('id');
    },
    */
    default_record: function(){
    	var self = this, result = {};
    	_.each(self.fields, function(value, key, list) {
    		result[key] = value["default"];
    	});
    	return result;
    }
});


_mobile.ListEditable = _mobile.List.extend({
	template: "list",
	//init: function(parent, dataset, view_id, options) {
	init: function(parent, options) {
        var self = this;
        options = options || {};
        
        this._super(parent, options);
        self.records_todelete = [];
    },
    
    add_row: function(record){
    	var self = this;
    	record = record || self.default_record();    	
    	var $html = $(QWeb.render(self.row_template, {records: [record]}));
        self.$contentEl.append($html);
        self.records.push(record);
        return $html;
    },
    
    delete_row: function(index){
    	var self = this;
    	var row = self.$().find(".oex-list-row").eq(index);
    	if(row.data('id')){
    		self.records_todelete.push(self.records[index]);
    	}
    	self.records.splice(index, 1);
    	row.remove();
    }
});

_mobile.Form = _mobile.Widget.extend({
	
	init: function(parent, options) {
        var self = this;
        this._super(parent);
        this.options = options || {};

        self.model = this.options.model;
        self.dataset = new _mobile.DataSetSearch(this, self.model, this.options.context, this.options.domain);
        self.datarecord = {id: (this.options.context ? this.options.context.id : null)};
        
        this.fields = {};
        this.has_been_loaded = $.Deferred();
        this.is_initialized = $.Deferred();
        
        //this.has_been_loaded.done(function() {
        //    self.init_pager();
        //});
        
        /*
        instance.web.bus.on('clear_uncommitted_changes', this, function(e) {
            if (!this.can_be_discarded()) {
                e.preventDefault();
            }
        });
        */
    },
    
    /**
     * @returns {jQuery.Deferred} initial view loading promise
     */
    start: function() {
    	var self = this;
    	
    	// render self
        self.render();
        
        // build validator
        self.validator = self.$el.validate({
        	errorPlacement: function( error, element ) {
				error.insertAfter( element.parent() );
			}
		});
    	
    	// load fields config
    	var fields = self.$el.find(":jqmData(fieldtype)");
    	var deferreds = [];
        $.each(fields, function(idx, field){
        	var fieldClass = _mobile.formwidgets.get_object($(field).data("fieldtype"));
        	if(!fieldClass){
        		fieldClass = _mobile.FormField;
        	}
        	var fieldWidget = new fieldClass(self, $(field).data());
        	fieldWidget.setElement(field);
        	self.fields[$(field).attr("name")] = fieldWidget;
        	deferreds.push(fieldWidget.start());
        });
        
    	return $.when.apply($, deferreds).then(function(){
    		// load record
            return self.load_data(self.datarecord.id);
    	});

    },
    
    render: function(){
        var self = this;

		self.on("data_loaded", self, self.render_data);
        self.$el.on('click', '.oex_button_save', this.on_save);
        self.$el.on('click', '.oex_button_cancel', this.on_cancel);
    },

	reload: function(){
		_.each(self.fields, function(field, key, fields){
			field.set('value'); //clear the saved value.
		});
		return self.load_data(self.datarecord.id);
	},
    
    render_data: function(r){
    	$.each(this.fields, function(idx, field){
    		field.set_value(r[field.name]);
    	});
    },
    
    get_values: function() {
        
    },
    
    is_valid: function() {
    	var valid = true;
    	$.each(this.fields, function(idx, field){
    		if(!field.is_valid()){
    			valid = false;
    			return false;
    		}
    	});
        return valid;
    },
	
	load_defaults: function () {
		var self = this;
        var fields = _.keys(self.fields);
        return self.dataset.default_get(fields).then(function(r) {
            self.trigger('data_loaded', r);
        });
    },
    
    load_data: function(id, options) {
        var self = this;
        
        if(id==undefined || id==null || id=="" || id instanceof Array && id.length == 0){        	
        	return self.load_defaults();
        }
        
        options = options || {};
        var ids = id instanceof Array ? id : [id];
        var fields = _.keys(self.fields)
        
        return self.dataset.read_ids(ids, fields, options).then(function (records) {
            if (_.isEmpty(records)) { return $.Deferred().reject().promise(); }
            self.trigger('data_loaded', records[0]);
        });
    },
    
    on_save: function(e) {
        var self = this;
        $(e.target).attr("disabled", true);
        return this.save().done(function(result) {
            self.trigger("save", result);
        }).always(function(){
            $(e.target).attr("disabled", false);
        });
    },
    
    on_cancel: function(event) {
        var self = this;
        if (this.can_be_discarded()) {
        	this.trigger('history_back');
        }
        this.trigger('on_button_cancel');
        return false;
    },
    
    save: function() {
        var self = this;
        try {
            var isFormValid = true,
                invalid_fields = [],
                first_invalid_field = null,
                values = {},
                readonly_values = {};
            for (var f in self.fields) {
                f = self.fields[f];
                if (!f.is_valid()) {
                    form_invalid = false;
                    if (!first_invalid_field) {
                        first_invalid_field = f;
                    }
                    invalid_fields.push(f);
                //} else if (f.name !== 'id' && (!self.datarecord.id || f._dirty_flag)) {
                } else if (f.name !== 'id') {
                    // Special case 'id' field, do not save this field
                    // on 'create' : save all non readonly fields
                    // on 'edit' : save non readonly modified fields
                    if (!f.get("readonly")) {
                        values[f.name] = f.get_value();
                    } else {
                        readonly_values[f.name] = f.get_value();
                    }
                }
            }
            if (!isFormValid) {
                self.set({'display_invalid_fields': true});
                first_invalid_field.focus();
                //self.on_invalid();
                return $.Deferred().reject();
            } else {
                self.set({'display_invalid_fields': false});
                var save_deferral;
                if (!self.datarecord.id) {
                    // Creation save
                    save_deferral = self.dataset.create(values, {readonly_fields: readonly_values}).then(function(r) {
                        return self.record_created(r);
                    }, null);
                } else if (_.isEmpty(values)) {
                    // Not dirty, noop save
                    save_deferral = $.Deferred().resolve({}).promise();
                } else {
                    // Write save
                    save_deferral = self.dataset.write(self.datarecord.id, values, {readonly_fields: readonly_values}).then(function(r) {
                        return self.record_saved(r);
                    }, null);
                }
                return save_deferral;
            }
        } catch (e) {
            console.error(e);
            return $.Deferred().reject();
        }
    },
    
    record_saved: function(r) {
        this.trigger('record_saved', r);
        if (!r) {
            // should not happen in the server, but may happen for internal purpose
            return $.Deferred().reject();
        }
        return r;
    },

    record_created: function(r) {
        var self = this;
        self.trigger('record_created', r);
        if (!r) {
            // should not happen in the server, but may happen for internal purpose
            return $.Deferred().reject();
        } else {
            self.datarecord.id = r;
        }
    },

});

		
_mobile.FormField = _mobile.Widget.extend({
	init: function(form, options) {
        var self = this;
        this._super(form);
        this.form = form;
        this.options = options || {};
    },
    
    render: function() {
    },
    
    start: function() {
    
        this.name = this.$el.attr("name");
        //this.set('value', false);
        
        return $.when();
        
		/*
        this.on("change:value", this, function() {
            if (field.is_syntax_valid()) {
                this.trigger('field_changed:' + name);
            }
            if (field._inhibit_on_change_flag) {
                return;
            }
            field._dirty_flag = true;
            if (field.is_syntax_valid()) {
                this.on_onchange(field);
                this.on_form_changed(true);
                this.do_notify_change();
            }
            this._check_css_flags();
            if (! this.no_rerender)
                this.render_value();
        });
        
        var tmp = this._super();
        this.render_value();
        */
    },
	set_value: function(value) {
		this.$el.val(value);
		if(this.get("value") === undefined){
        	this.set('value', value); //old value
        }
    },
    get_value: function() {
        return this.$el.val();
    },
    is_valid: function() {
        //return this.$el.valid();
    	var self = this,
    		validator = self.form.validator,
    		element = validator.validationTargetFor( validator.clean( self.$el ) );
    	return element !== undefined ? validator.check(self.$el) : true;
    },
    is_dirty: function(){
    	return !(this.get('value') == this.get_value() || _.isEqual(this.get('value'), this.get_value()));
    },
    on_value_changed: function(){
    	
    },
    focus: function() {
    	this.$el.focus();
    },
});


_mobile.FieldSelect = _mobile.FormField.extend({

	init: function(form, options) {
        var self = this;
        self._super(form);
        options = options || {};
        
        self.options = options;
        self.placeholder = options.placeholder;
        
        //self.selectoptions = [];
        //self.dataset = new _mobile.DataSetSearch(this, options.model, options.context, options.domain);
        self.dict = _mobile.dict(options.model, options);
        
        /*
        this.field_manager.on("view_content_has_changed", this, function() {
            var domain = new openerp.web.CompoundDomain(this.build_domain()).eval();
            if (! _.isEqual(domain, this.get("domain"))) {
                this.set("domain", domain);
            }
        });
        */
    },
    
    start: function(){
    	var self = this;
    	self._super();
    	/*
    	return self.query_options().then(function(values){
    		self.render_options(values);
    	});
    	*/
    	return self.render();
    },
    /*
    query_options: function() {
        var self = this;
        //name_search(name, domain, operator, limit)
        return self.dataset.name_search().done(function(values) {
            self.selectoptions = values;
        });
    },

    render_options: function(values) {
        var self = this;
        
        if(self.placeholder){
        	values = [[false, this.placeholder]].concat(values);
        }
        self.$().html(QWeb.render("select.options", {values: values}));
    },
    */
    render: function(){
    	var self = this;
    	return self.dict.data().then(function(records){
    		var selectoptions = self.placeholder ? [[false, this.placeholder]].concat(records) : [].concat(records);
            self.$().html(QWeb.render("select.options", {options: selectoptions}));
    	});
    },
    
    set_value: function(value){
		var v = value;
    	if(typeof value == "object"){
    		if(value.id){
    			v = value.id
    		}else if(value.length){
    			v = value[0];
    		}    			
    	}
    	this._super(v);
    },

    focus: function() {
        var input = this.$('select:first')[0];
        return input ? input.focus() : false;
    },
    
});


_mobile.ListForm = _mobile.Widget.extend({
	
	init: function(parent, options) {
        var self = this;
        options = options || {};
        
        self._super(parent);
        
        self.options = options;
        self.model = options.model;
        self.dataset = new _mobile.DataSetSearch(this, self.model, options.context, options.domain);
        
        options.fields = _mobile.parse(options.fields);
        self.fields = options.fields;
        
        self.list = new _mobile.ListEditable(self, options);
        self.row_template = options.rowtemplate;
        
        self.widgets = [];
        
        self.has_been_loaded = $.Deferred();
        self.is_initialized = $.Deferred();
        
    },
    
    /**
     * @returns {jQuery.Deferred} initial view loading promise
     */
    start: function() {
    	var self = this;
    	
    	// render
        self.render();
        self.list.setElement(self.$el.find(".oex-list-wrapper"));	        	
        
        // build validator
        self.validator = self.$el.validate({
        	onfocusout: false,
        	onfocusin: false,
        	onkeyup: false
        	/*
        	errorPlacement: function( error, element ) {
				error.insertAfter( element.parent() );
			}
			*/
		});
	    
        // list
	    return self.list.start().then(function(){
	    	
	    	// load fields config
	        return self._build_widgets();
	    });
    },

	_build_widgets: function(){
		var self = this;
		var deferreds = [];
		var rows = self.list.$el.find(".oex-list-row");
		$.each(rows, function(idx, row){
			deferreds = deferreds.concat(self._build_row_widgets(idx, $(row)));
		});
		
		return $.when.apply($, deferreds);
	},
	_build_row_widgets: function(rowidx, row){
		var self = this;
		var fields = row.find(":jqmData(fieldtype)");
    	if(!fields.length){
    		return false;
    	}

    	self.widgets[rowidx] = {};
    	var deferreds = [];
    	
        $.each(fields, function(idx, field){
        	var fieldClass = _mobile.formwidgets.get_object($(field).data("fieldtype"));
        	if(!fieldClass){
        		fieldClass = _mobile.FormField;
        	}
        	var fieldWidget = new fieldClass(self, $(field).data());
        	fieldWidget.setElement(field);
        	self.widgets[rowidx][$(field).attr("name")] = fieldWidget;
        	deferreds.push(fieldWidget.start().then(function(){
        		fieldWidget.set_value(self.list.records[rowidx][fieldWidget.name]);
        	}));
        });

		return deferreds;
	},

	reload: function(){
		var self = this;
		return self.list.reload().then(function(){
	    	// load fields config
	        return self._build_widgets();
	    });
	},
	
	refresh: function(){
		this.list.refresh();
	},
    
    render: function(){
        var self = this;

		self.getParent().$el.off('vclick', '.oex_button_save').on('vclick', '.oex_button_save', this.on_save);
        self.getParent().$el.off('vclick', '.oex_button_new').on('vclick', '.oex_button_new', this.on_new);
        self.getParent().$el.off('vclick', '.oex_button_delete').on('vclick', '.oex_button_delete', this.on_delete);
        self.getParent().$el.off('vclick', '.oex_button_cancel').on('vclick', '.oex_button_cancel', this.on_cancel);
        
        self.$el.submit(function(e){
        	self.getParent().$el.find(".oex_button_save").eq(0).trigger('vclick');
        	return false;
        });
    },
    
    is_valid: function() {
    	var valid = true;
    	$.each(this.widgets, function(idx1, row){
    		$.each(row, function(idx2, field){
	    		if(!field.is_valid()){
	    			valid = false;
	    			return false;
	    		}
	    	});
	    	return valid;
    	});
        return valid;
    },
    
    check_valid: function() {
    	var invalid_fields = [];
    	$.each(this.widgets, function(idx1, row){
    		if(row){
	    		$.each(row, function(idx2, field){
		    		if(!field.is_valid()){
		    			invalid_fields.push({index:idx1, name:idx2, field:field});
		    		}
		    	});
    		}
    	});
        return invalid_fields;
    },
    
    get_values: function() {
    	var self = this,
    		unchanged = [], changed = [], all = [];
    	$.each(self.widgets, function(idx1, row){
    		var record = {}, dirty = false;
    		if(row){
	    		$.each(row, function(idx2, field){
	    			record[field.name] = field.get_value();
	    			if(!dirty && field.is_dirty()){
	    				dirty = true;
	    			}
		    	});
	    		if(record.id && !dirty){
	    			unchanged.push(record);
	    		}else{
	    			changed.push(record);
	    		}
	    		all[idx1] = record;
    		}else{
    			all[idx1] = self.list.records[idx1];
    		}
    	});
        return [changed, unchanged, all];
    },
    
    save: function(options) {
        var self = this;
        try {
        	
        	self.validator.resetForm();
        	self.validator.errors().empty();
            var invalid_fields = self.check_valid();
            if (invalid_fields.length) {
                self.set({'display_invalid_fields': true});
                //self.on_invalid();
                //self.validator.showErrors();
                self.show_errors(self.validator.errorList, invalid_fields);
                invalid_fields[0].field.focus();
                return $.Deferred().reject();
            }
            
            var values = self.get_values();
			if( self.triggerWithResult("before_save:oexevent", self, values[2]).result === false ){
				return $.Deferred().reject();
			}
			
            var delids = _.pluck(self.records_todelete, "id");
            
            self.set({'display_invalid_fields': false});
            // Batch save
            if(options.context.force === true || !_.isEmpty(values[0]) || !_.isEmpty(delids)){
            	var data = {};
            	if(!_.isEmpty(values[0]))	data.values = values[0];
            	if(!_.isEmpty(delids))		data.delids = delids;
            	if(options.context.force === true)	data.unchanged = values[1];
            	
	            return self.dataset.save_batch([data], options || {});
            }
            return $.Deferred().reject();

        } catch (e) {
            console.error(e);
            return $.Deferred().reject();
        }
    },
    
    show_errors: function(error_list, fields){
    	var self = this;
    	$("#popupInputPrompt ul").empty();
		for ( i = 0; error_list[ i ]; i++ ) {
			error = error_list[ i ];
			if ( self.validator.settings.highlight && error.element) {
				self.validator.settings.highlight.call( self.validator, error.element, self.validator.settings.errorClass, self.validator.settings.validClass );
			}
			//{index:idx1, name:idx2, field:field}
			if(fields && fields.length){
				$("#popupInputPrompt ul").append("<li>第"+(fields[i].index+1) + "行:" + error.message+"</li>"); //( error.element,  );
			}else{
				$("#popupInputPrompt ul").append("<li>" + error.message+"</li>"); 
			}
		}
		$("#popupInputPrompt").popup("open");
    },
    
    on_new: function(e) {
        var self = this;
        
        $(e.target).attr("disabled", true);
        
        var row = self.list.add_row();
        
        var fields = row.find(":jqmData(fieldtype)");
    	if(!fields.length){
    		return false;
    	}
    	
    	var rowidx = self.list.records.length-1;    	
    	var deferreds = self._build_row_widgets(rowidx, row);
        
        $.when.apply($, deferreds).always(function(){
            $(e.target).attr("disabled", false);
            self.list.refresh();
        });
        
    },
    on_delete: function(e) {
        var self = this;
        var row = $(e.target).closest(".oex-list-row");
        var rowindex = row.index();
        self.widgets.splice(rowindex, 1);
        self.list.delete_row(rowindex);
    },
    on_save: function(e) {
        
    	//return $.when();
        var self = this,
        	context = $(e.target).jqmData("context") || {};
        
        context = _mobile.parseJSON(context);
        	
        $(e.target).attr("disabled", true);
        $.mobile.loading("show");
        return this.save({context: context}).always(function(result) {
            $.mobile.loading("hide");
            $(e.target).attr("disabled", false);
        }).done(function(result){
            self.trigger("after_save", result);
        });
    },
    on_cancel: function(event) {
        var self = this;
        if (this.can_be_discarded()) {
        	this.trigger('history_back');
        }
        this.trigger('on_button_cancel');
        return false;
    },
    
});

_mobile.Calendar = _mobile.Widget.extend({
	//template: "calendar",

	init: function(parent, options) {
        var self = this;
        this._super(parent);
        options = options || {};
        
        self.options = options;
        self.model = options.model;
        self.dataset = new _mobile.DataSetSearch(this, self.model, options.context, options.domain);
        self.fields = _mobile.parse(options.fields);
        self.date_field = options.datefield;
        self.records = [];
        self.cell_template = options.celltemplate;
		self.month = instance.date_to_str(new Date()).substring(0,7);
        self.grouped = false;
    },
    /**
     * @returns {jQuery.Deferred} initial view loading promise
     */
    start: function() {
    	var self = this;
        self.render();
        self.$().on("refresh", ":jqmData(role=calendar)", function(ev, options){
        	self.reload(options);
        });
        return self.load_data().then(function(){
            self.render_data();
        });
    },
    render: function(options){
    	var self = this;
        self.$contentEl = self.$().find(":jqmData(role=calendar)");
        self.$contentEl.calendar();
    },
    render_data: function(){
    	var self = this;
    	$.each(self.records, function(idx, record){
    		var d = record[self.date_field];
    		//var $cell = self.$contentEl.calendar("find", d);
    		var $cell = self.$contentEl.find("td[date="+d+"]");
	    	var html = QWeb.render(self.cell_template, {record: record});
	        $cell.find(".content").html(html);
    	});
    },
    reload: function(options){
    	var self = this;
		if(options && options.initDay){
			self.month = instance.date_to_str(options.initDay).substring(0,7);
		}
        return self.load_data().then(function(){
            	self.render_data();
            });
    },
    
	//options.domain
	//options.context
    load_data: function(options){
    	
    	var self = this;

    	var options = {};
    	var fields = _.keys(self.fields),
    		fromdate = self.month + '-01',
			todate = instance.date_to_str(new Date(self.month.substring(0,4), self.month.substring(5), 0));

    	options.domain = "[('" + self.date_field + "','>=','" + fromdate + "')"
    		+ ",('" + self.date_field + "','<=','" + todate + "')]";
    	
    	return self.dataset.read_any(fields, options).done(function (records) {
    		/*
    		if (self.records.length) {
                self.records.reset(null, {silent: true});
                //self.$contentEl.empty();
            }
            self.records.add(records, {silent: true});
            */
            self.records = records;
        });
    }
});

_mobile.MonthView = _mobile.Widget.extend({

	init: function(parent, options) {
        var self = this;
        this._super(parent);
        options = options || {};
        
        self.options = options;
        self.model = options.model;
        self.dataset = new _mobile.DataSetSearch(this, self.model, options.context, options.domain);
        self.fields = _mobile.parse(options.fields);
        self.date_field = options.datefield;

        self.records = [];
        self.cell_template = options.celltemplate;

    },
    /**
     * @returns {jQuery.Deferred} initial view loading promise
     */
    start: function() {
    	var self = this;
        self.render();
        self.$().on("changeYear", function(ev, options){
        	self.reload();
        });
        return self.load_data().then(function(){
            self.render_data();
        });
    },
    render: function(options){
        this.$el.monthview();
    },
    reload: function(options){
    	var self = this;
        return self.load_data().then(function(){
            	self.render_data();
            });
    },
    render_data: function(){
    	var self = this;
    	$.each(self.records, function(idx, record){
    		var d = record[self.date_field];
    		var $cell = self.$el.find("td[month="+parseInt(d.substring(5))+"]");
	    	var html = QWeb.render(self.cell_template, {record: record});
	        $cell.find(".content").html(html);
	        //$cell.find(".disable").removeClass("disable");
    	});
    },
    load_data: function(options){
    	
    	var self = this;

    	var options = options || {};
    	var fields = _.keys(self.fields),
    		currYear = self.$el.monthview("option").currYear,
    		fromdate = currYear + '-01-01',
    		todate   = currYear + '-12-31';

    	options.domain = "[('" + self.date_field + "','>=','" + fromdate + "')"
    		+ ",('" + self.date_field + "','<=','" + todate + "')]";
    	
    	return self.dataset.read_any(fields, options).done(function (records) {
            self.records = records;
        });
    }
});

/**
 * Registry for all the widgets
 */
_mobile.widgets = new instance.web.Registry({
	'list' : 'instance.web.mobile.List',
	'form' : 'instance.web.mobile.Form',
	'listform' : 'instance.web.mobile.ListForm',
	'calendar' : 'instance.web.mobile.Calendar',
	'monthview' : 'instance.web.mobile.MonthView'
});

_mobile.formwidgets = new instance.web.Registry({
     'text'          : 'instance.web.mobile.FieldText'
    ,'select'        : 'instance.web.mobile.FieldSelect'
    ,'checkboxradio' : 'instance.web.mobile.FieldRadio'
    ,'one2many'      : 'instance.web.mobile.FieldOne2Many'
    ,'one2many_list' : 'instance.web.mobile.FieldOne2Many'
    ,'progressbar'   : 'instance.web.mobile.FieldProgressBar'
});

_mobile.dicts = {};
_mobile.dict = function(name, options){
	var dict = _mobile.dicts[name];
	if(!dict){
		dict = new _mobile.DictStore(options);
		_mobile.dicts[name] = dict;
	}
	return dict;
};

// common methods
_mobile.parse = function(values){
	
	var obj = _mobile.parseJSON(values), result = {};
	
	if(_.isString(obj)){
		_.each(obj.split(","), function(item){ 
			try{
				$.extend(result, $.parseJSON(item));
			}catch(ex){
				result[item] = {};
			}
		});
		return result;
	}
	return obj;
};

_mobile.parseJSON = function(value){
	
	if(!value){
		return null;
	}
	
	if( _.isFunction(value) ){
		var result;
		if(arguments.length==2){
			result = value.apply(arguments[1]);
		}else if(arguments.length>2){
			result = value.apply(arguments[1], Array.prototype.slice.call(arguments, 2));
		}else{
			result = (value)();
		}
		return _mobile.parseJSON(result);
	}
	
	if( _.isString(value) ){
		try{
			return $.parseJSON(value);
		}catch(e){
			//try{
			//	return eval("(" + value + ")");
			//}catch(e1){}
		}
	}
	return value;
};

_mobile.isEqual = function(value1, value2){
	return value1 == value2 || _.isEqual(value1,value2);
};

_mobile.utils = {
	date_to_str: instance.date_to_str
};

})();

$.extend( $.validator.prototype, {
	customDataMessage: function( element, method ) {
		return $( element ).data( "msg" + method.charAt( 0 ).toUpperCase() +
			method.substring( 1 ).toLowerCase() ) 
			|| $( element ).data( "msg-" + method.toLowerCase() )
			|| $( element ).data( "msg" );
	}
});
