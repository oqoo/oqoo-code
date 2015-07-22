/*---------------------------------------------------------
 * modules' custom scripts
 *---------------------------------------------------------*/

$(function(){
	var instance = openerp;
	var mobile = instance.web.mobile;
	var QWeb = instance.web.qweb,
	    _t = instance.web._t;

	mobile._modules = (mobile._modules || []).concat(["mobile_timesheet"]);
	
	$("#page1").on('selectConfrimOk', "div:jqmData(role=calendar)", function(e, data){
		if(data.data.length>1){
			instance.web.mobile.changepagedata = data;
			$.mobile.changePage("#page2");
		}else{
			instance.web.mobile.changepagedata = {data: data.data[0]};
			$.mobile.changePage("#page3");
		}
		$(e.target).calendar('selectConfrimCancel');
	});
	
	$("#page2").on('data_loaded:oexevent', ".oex-list-wrapper", function(e, context, data){
		var domains = eval(context.options.domain);
		var dates = domains[0][2];
		var record_dates = _.pluck(data, "date");
		_.each(dates, function(element, index, list){
			if(!_.contains(record_dates, element)){
				data.push({date: element});
			}
		});
		//data = _.sortBy(data, "date");
		data.sort(function(a,b){
			if(a["date"]==b["date"])
				return 0;
			else if(a["date"]<b["date"])
				return -1;
			else
				return 1;
		});
	});
	
	$("#page2,#page3").on('before_save:oexevent', ":jqmData(oextype=listform)", function(e, context, data){
		// projects are not allowed to repeat in the same day.
		var r= _.chain(data)
				.groupBy(function(item){return item.date;})
				.map(function(val, key){
						return [key, _.chain(val)
									.countBy(function(item){return item.project;})
									.pairs()
									.reject(function(item){return item[1]==1;})
									.value()];
					})
				.reject(function(item){return item[1].length==0;})
				.map(function(item){return {message: (e.delegateTarget.id=="page2"?item[0]:"") + "存在重复的项目归属"}})
				.value();
		
		if(r.length){
			context.show_errors(r);
			return false;
		}
		
		// the total of working hours in a day must not be greater than the norm of working hour.
		r= _.chain(data)
			.groupBy(function(item){return item.date;})
			.map(function(val, key){
				return [key, 
				        _.reduce(val, 
								function(memo, item){
									return {work: memo.work+(item.work-0), 
										reated_work:(item.reated_work?item.reated_work:memo.reated_work)}; 
									}, 
								{work:0,reated_work:8})
						];
			})
			.filter(function(item){return item[1].work > item[1].reated_work;})
			.map(function(item){return {message: (e.delegateTarget.id=="page2"?item[0]:"") + "总填报工时(" + item[1].work +")超出额定工时("+item[1].reated_work+")"}})
			.value();
		
		if(r.length){
			context.show_errors(r);
			return false;
		}
		
	});
	
	$("#page2,#page3").on('after_save:oexevent', ":jqmData(oextype=listform)", function(e, context, data){
		$.mobile.loading('show', {
			html: "<span class='ui-icon'><img src='/mobile/static/src/img/success.png' width='55' height='55' /></span>"
		});	
		setTimeout("$.mobile.loading('hide');$.mobile.back();", 1000);
	});
	
	$("#page3").on('data_loaded:oexevent', ".oex-list-wrapper", function(e, context, data){
		var domains = eval(context.options.domain);
		var date = domains[0][2];

		if(_.isEmpty(data)){
			data.push({date: date});
		}else{
			context.getParent().fields["reated_work"]["default"] = data[0]["reated_work"];
		}
	});
	
	$("#page4").on('touchMonth', function(e, data){
		var month = data.month,
			fromdate = month+"-01",
			todate = instance.date_to_str(new Date(month.substring(0,4), month.substring(5), 0));
		instance.web.mobile.changepagedata = {fromdate: fromdate, todate: todate};
		$.mobile.changePage("#page5");
	});	

	$("#page5").on('data_loaded:oexevent', ".oex-list-wrapper", function(e, context, data){
		var domains = eval(context.options.domain),
			fromdate = domains[0][2],
			todate = domains[1][2],
		    record_dates = _.pluck(data, "date");
		
		var month = fromdate.substring(0,8);  //yyyy-MM-
			fromday = parseInt(fromdate.substring(8)),
			today = parseInt(todate.substring(8));
		
		for(var i = fromday; i<= today; i++){
			var date = month + (i<10?"0"+i:i);
			if(!_.contains(record_dates, date)){
				data.push({date: date, work: 0});
			}
		}
		
		//data = _.sortBy(data, "date");
		data.sort(function(a,b){
			if(a["date"]==b["date"])
				return 0;
			else if(a["date"]<b["date"])
				return -1;
			else
				return 1;
		});
	});
	
	$(":jqmData(role=popup)").popup();
});


