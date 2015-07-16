# -*- coding: utf-8 -*-

import xmlrpclib 
from datetime import date, datetime, timedelta
from openerp import api
from openerp.osv import fields, osv
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from openerp.addons.wx_basic.wxutil import req_get, req_post
from openerp.addons.wx_manager.rpcutil import RPCUtil as RPC
from calendar import calendar
# from bsddb.dbtables import _columns

def _get_empinfo(context):
    workid = context.has_key('WorkId') and context['WorkId'] or None
    empid = context.has_key('EmployeeId') and context['EmployeeId'] or None
    empuid = context.has_key('EmployeeUid') and context['EmployeeUid'] or None
    if not workid:
        raise except_orm(_('Error'), _("Employee Work ID is not exists !"))
    if not empid:
        raise except_orm(_('Error'), _("Employee ID is not exists !"))
    if not empuid:
        raise except_orm(_('Error'), _("Employee UID is not exists !"))
        
    return int(empid), workid, int(empuid)


class mobile_timesheet_sheet(osv.osv):
    _name = 'mobile_timesheet.sheet'
    
    _columns = {
        'date':fields.date(),
        'sheet_id':fields.integer(),
        'work':fields.float(),
        'reated_work':fields.float(),
        'emp_id':fields.char(),
        'status':fields.char(),   # 送审, 驳回(ng), 通过(ok), 未送审
        'project':fields.many2one('mobile_timesheet.project'),
    }
    
    def _timesheet_detail(self,proxy,fields, empuid, empid, from_date, to_date, wfstate=('wfstate', '!=', 'over')):
        result = [] 
        model = 'hr_timesheet_sheet.sheet'
        domain = [("date_from", "<=", to_date), ("date_to", ">=", from_date), ('employee_id.id', '=', empid), wfstate]
        fields = ["work_id", "date_from", "date_to", "total_timesheet", "wfstate","timesheet_ids"]
        
        ids = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'search', domain, {})
        record = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'read', ids, fields)
        
        wfstatus = {}
        for rec in record:
            status = rec["wfstate"]
            
            if 	  status == 'approv_1': status = 'draft'
            elif  status == 'proved': status = 'approved'
            else: status = 'review'
            
            fdate = datetime.strptime(rec["date_from"],'%Y-%m-%d')
            tdate = datetime.strptime(rec["date_to"],'%Y-%m-%d')
            delta = (tdate - fdate).days
            for lineid in rec['timesheet_ids']:
                wfstatus[str(lineid)] = status
                
        model = 'hr.analytic.timesheet'
        fields = ['date', 'unit_amount','sheet_id','account_id']
        domain = [("date", "<=", to_date), ("date", ">=", from_date), ('employee_id.id', '=', empid), ('sheet_id', 'in', tuple(ids))]
        ids = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'search', domain, {})
        record = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'read', ids, fields)
        for rec in record:
            result.append({'id':rec['id'],'date':rec['date'], 'work':int(rec['unit_amount']), 'status':wfstatus[str(rec['id'])],'sheet_id':int(rec['sheet_id'][0]),'project':rec['account_id']})
        
        return result

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False,lazy=True):
        result = [] 
        empid, workid, empuid = _get_empinfo(context)
        proxy = RPC.getProxy()
        
        from_date = domain[0][2]
        to_date = domain[1][2]
        tmsts = self._timesheet_detail(proxy,fields, empuid, empid, from_date, to_date)
        
        if "date:day" in groupby:
        	resultdict = {} 
#查询from_date到to_date每天的额定工时
				
        	for tm in tmsts: 
        		tmdate = tm['date']
        		tmstatus = tm['status'] 
        		tmwork= tm['work'] 
        		
        		if not resultdict.has_key(tmdate): 
        			resultdict[tmdate] = {'date:day':tmdate, 'status':tmstatus, 'work':tmwork} 
        		elif resultdict[tmdate] == 'approved' or tmstatus == 'draft': 
        			resultdict[tmdate] = {'date:day':tmdate, 'status':tmstatus, 'work':resultdict[tmdate]['work'] + tmwork} 
#如果需要返回额定工时
	        if 'reated_work' in fields:
		        warkdaydict = self._get_related_work(empid, datetime.strptime(from_date,'%Y-%m-%d'), datetime.strptime(to_date,'%Y-%m-%d')) 
		        for k,v in warkdaydict.items():
	        		if resultdict.has_key(k):
	        			resultdict[k]['reated_work'] = v 
	        			result.append(resultdict[k])
	        		else:
	        			result.append({'date:day':k, 'status':'', 'work':0, 'reated_work':v})
	        else:
	        	for k,v in resultdict.items():
	        		result.append(v)
	        		
        		
        elif "date:month" in groupby:
            resdict = {}
            for tm in tmsts:
                days = 1 
                work = tm['work']
                tmp_ym = datetime.strptime(tm["date"],'%Y-%m-%d').strftime('%Y-%m')
                tm.pop('date')
                if resdict.has_key(tmp_ym):
                    work += resdict[tmp_ym]['work']
                    days += resdict[tmp_ym]['days']
                    
                resdict[tmp_ym] = {'date:month':tmp_ym,'work':work, 'days':days}
            
            result = [v for k, v in resdict.items()]
            
        return result 
    

    def _get_related_work(self, empuid, empid, from_date, to_date): 
        warkdaydict = {}
    	proxy = RPC.getProxy()
        days = (to_date - from_date).days
        model = 'bjc.hr.payroll.workday'
        for d in range(0, days + 1):
            datetmp = (from_date + timedelta(d)).strftime('%Y-%m-%d')
            calendarworkday = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'get_employee_monthly_workday_work_hours', empid, datetmp, datetmp)
            warkdaydict[datetmp] = calendarworkday[1]
        
        return warkdaydict

    def search_read(self, cr, uid, domain=None, fields=None, offset=0, limit=None, order=None, context=None):
        proxy = RPC.getProxy()
        result = [] 
        empid, workid, empuid = _get_empinfo(context)
        if isinstance(domain[0][2],type('str')):
            from_date = domain[0][2]
            to_date = domain[0][2]
        elif isinstance(domain[0][2],type([])):
            from_date = domain[0][2][0]
            to_date = domain[0][2][len(domain[0][2]) - 1]
        tmsts = self._timesheet_detail(proxy,fields, empuid, empid, from_date, to_date)
        
#查询from_date到to_date每天的额定工时
        warkdaydict = self._get_related_work(empuid, empid, datetime.strptime(from_date,'%Y-%m-%d'), datetime.strptime(to_date,'%Y-%m-%d'))
        resworkday = {}
        for tm in tmsts:
            domain = [("employee_id", "=", empid), ("month_start", "=", from_date), ('month_end', '=', to_date)]
            tm['reated_work'] = warkdaydict[tm['date']]
            result.append(tm)
    
        return result

   

    def save_batch(self, cr,uid, vals, context = {}):
    	opertype = context['opertype']
        proxy = RPC.getProxy()
        empid, workid, empuid = _get_empinfo(context)
        
        stroneofweekday = '1999-09-09'
        if vals[0].has_key('values'): stroneofweekday = vals[0]['values'][0]['date']
        elif vals[0].has_key('unchanged'): stroneofweekday = vals[0]['unchanged'][0]['date']
        oneofweekday = datetime.strptime(stroneofweekday,'%Y-%m-%d')
        weekofday = oneofweekday.weekday()
        weekday_start = oneofweekday + timedelta( -weekofday ) 
        weekday_end = oneofweekday + timedelta(6 - weekofday ) 
        from_date = weekday_start.strftime('%Y-%m-%d')
        to_date = weekday_end.strftime('%Y-%m-%d')
        
        values = vals[0].has_key('values') and vals[0]['values'] or []
        timesheet_add = [] 
        timesheet_update= {}
        model="payroll.hr.analytic.timesheet"  ##要运行哪个类中的函数？
        fields = ["account_id", "general_account_id", "journal_id", "date", "name", "user_id", "product_id","product_uom_id","to_invoice","amount","unit_amount"]
        payrolldefault = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'default_get', fields) 
        
        model="hr_timesheet_sheet.sheet"  ##要运行哪个类中的函数？
        fields = ["message_follower_ids", "timesheet_ids", "current_project_name", "current_project_no", "wfstate", "attendances_ids", "state_attendance", "is_project_true", "message_ids", "employee_id", "user_id", "job_id", "approv_is_me", "date_from", "company_id", "period_ids", "jobtype_id", "state", "node_count", "department_id", "project_name", "total_difference", "current_node", "date_to", "date", "total_attendance", "current_contract_cate", "name", "total_timesheet", "transactor_is_me", "opinion", "personal_type", "work_id"]
        sheetdefault = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'default_get', fields) 
        
        
        #查询淌有送审的工时单, 将新加的工时加入到这张工时单
    	tmsts = self._timesheet_detail(proxy,fields, empuid, empid, from_date, to_date, ('wfstate','=','approv_1')) 
    	# 已存在没有送审工时字典, key为sheet_id
    	tmst_dict = {}
    	for tm in tmsts:
    		dictkey = str(tm['sheet_id'])
    		if not tmst_dict.has_key(dictkey): tmst_dict[dictkey] = {} 
    		tmst_dict[dictkey][tm['date']] = (0,False, {
                                "account_id": tm['project'][0],          #需要去查找 
	                            "amount": -(int(tm['work']) * 30), 
	                            "date": tm['date'],
	                            "general_account_id": payrolldefault['general_account_id'],
	                            "journal_id": payrolldefault['journal_id'],
	                            "name": "/",
	                            "product_id": payrolldefault['product_id'],
	                            "product_uom_id": payrolldefault['product_uom_id'],
	                            "to_invoice": False,
	                            "unit_amount": tm['work'],
	                            "user_id": False,  
                            })
       
        #新增或修改的工时记录
        for val in values:
            timesheetid = val['sheet_id'] and int(val['sheet_id']) or None
            work_tmp = val['work'] and int(val['work']) or 0
            datestr = val['date']
            timesheet_tmp = (0, False,{
                                        "account_id": int(val['project']),          #需要去查找 
			                            "amount": -(work_tmp * 30), 
			                            "date": datestr,
			                            "general_account_id": payrolldefault['general_account_id'],
			                            "journal_id": payrolldefault['journal_id'],
			                            "name": "/",
			                            "product_id": payrolldefault['product_id'],
			                            "product_uom_id": payrolldefault['product_uom_id'],
			                            "to_invoice": False,
			                            "unit_amount": work_tmp,
			                            "user_id": False,     
                                    })
            
            # timsheetid是没有送审的工时单
            if timesheetid and tmst_dict.has_key(str(timesheetid)): 
            	if not timesheet_update.has_key(str(timesheetid)): timesheet_update[str(timesheetid)] = [(5,False,False)]
            	timesheet_update[str(timesheetid)].append(timesheet_tmp)
            	if tmst_dict[str(timesheetid)].has_key(datestr): tmst_dict[str(timesheetid)].pop(datestr)
            else:
            	if not timesheet_add: timesheet_add.append((5,False,False))
            	timesheet_add.append(timesheet_tmp)
            	
        for tmid,v in tmst_dict.items():
        	if not timesheet_update.has_key(tmid):timesheet_update[tmid] = [(5,False,False)]
    		#将新加的工时行，添加到第一个工时单
    		for tm in timesheet_add[1:]:
    			timesheet_update[tmid].append(tm)
    		timesheet_add = [] 
    		
    		for tmdate,v2 in v.items():
				timesheet_update[tmid].append(v2)
					
        
        submit_vals = {
			"attendances_ids": [],
			"company_id": sheetdefault['company_id'],
		    "current_node": 0,
			"date": oneofweekday.strftime('%Y-%m-%d'),
			"date_from": from_date,
			"date_to": to_date,
			"employee_id": empid,
			"is_project_true": "Yes", 
			"message_follower_ids": False,
			"message_ids": False,
			"name": False,
			"node_count": 0,
			"opinion": False,
			"project_name": False,
			"timesheet_ids": [],
			"wfstate": "approv_1",
			"work_id": workid,
		}
        
        
        
        try:
	        model="hr_timesheet_sheet.sheet" 
	        #新建的工时单
	        if timesheet_add:
	        	if opertype == 1: submit_vals['wfstate'] = "approv_2"
	        	submit_vals['timesheet_ids'] = timesheet_add
		        proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'create', submit_vals) 
		        
		        
	        for id,vals in timesheet_update.items():
	        	if opertype == 1: submit_vals['wfstate'] = "approv_2"
	        	submit_vals['timesheet_ids'] = vals
                proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'write', [int(id)], submit_vals) 
		        
        except Exception, e: 
        	try: 
        		raise osv.except_osv(_('warning'),_(e.faultCode)) 
        	except: 
        		pass 
        	
class mobile_timesheet_calendar(osv.osv):    
    _name = 'mobile_timesheet.calendar'
    
    def search_read(self, cr,uid, vals, context = {}):
        pass

class mobile_timesheet_project(osv.osv):
    _name = 'mobile_timesheet.project'
    
    _columns = {
        'name':fields.char(),
    }
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100, name_get_uid=None):
		proxy = xmlrpclib.ServerProxy(RPC.URL) 
		empid, workid, empuid = _get_empinfo(context)
        
		res = [] 
		model="bjc.project.employee"  ##要运行哪个类中的函数？
		ids = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'search', [('work_id', '=', workid)], {})
		pros = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'read', ids, ['project_id']) 
        
		if not pros:
			model="account.analytic.account"  ##要运行哪个类中的函数？
			ids = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'search', [('name', '=', '工时申报')], {})
			pros = proxy.execute(RPC.DB, empuid, RPC.PWD, model, 'read', ids, ['name'])
        
		for pro in pros:
		    res.append((pro['id'],pro['name']))
            
		return res 
        
		    