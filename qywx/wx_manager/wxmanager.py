# -*- coding: utf-8 -*-
import time
import xmlrpclib 
import psycopg2
from datetime import datetime
from openerp import http
from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager
from openerp.addons.wx_basic.wxapi import WChatContacts
from rpcutil import RPCUtil as RPC 
	
class DeptManager(object):
    
    def __init__(self,wxbasic):
        self.__wxbasic = wxbasic
        self._protected_dept = ['0','1']
        self._base_deptid = max(self._protected_dept) 

    def get_wx_deptdict(self,contacts):
        # 查询微信通讯录已创建的部门, 来判断是更新还是新建微信通讯录部门
        wx_deptdict = {}
        wx_depts = contacts.get_dept_list()
        if wx_depts['errcode'] == 0:
            for wxdept in wx_depts['department']:
                wx_deptdict[str(wxdept['id'])] = True 
                
        return  wx_deptdict

    def update_dept(self, reset=False):
    	u'''
    @param reset:  True表示删除所有部门(除部门ID为1和2), 然后根据wx_deparment数据创建微信通讯录部门	
    	'''
        registry = RegistryManager.get(http.request.cr.dbname)
        contacts = WChatContacts(self.__wxbasic) 
        today = datetime.today()
        #微信通讯录部门更新的部门ID
        update_deptids = []
        wx_deptdict = {}   # 已创建在微信通讯录的部门, KEY表的ID
        deptdict = {}       # key 表的DEPT_ID
        
        # @param id是wx_department表的ID
        def __check_parent_isdel(deptid):
            if deptid in self._protected_dept:
                return False 
            else:
                isdel = deptdict[deptid]['is_del']
                dept_pid = str(deptdict[deptid]['dept_pid'])
                if isdel:
                    return True 
                elif dept_pid not in self._protected_dept:
                    return __check_parent_isdel(dept_pid)
                else:
                    return False 
                
        with registry.cursor() as cr:
            wx_dept= registry.get('wx.department')
            self.__synch_department(reset) 
            #获取本志所有部门
            all_depts = wx_dept.browse(cr, SUPERUSER_ID,wx_dept.search(cr,SUPERUSER_ID,[]))
            #创建deptdict字典，key为部门真实id
            for dept in all_depts:
                deptdict[str(dept.dept_id)] = dept
                
            if reset: # 删除所有部门
            	self.delete_dept()
            else:
				wx_deptdict = self.get_wx_deptdict(contacts) 
			            		
            try:
			    for dept in sorted(all_depts, key=lambda x:x.level):
			        wx_dept_data = {
			            'id': dept.id, 
			            'name':  dept.dept_name_encrypt, 
			            'parentid' : (dept.level != 1 and deptdict.has_key(str(dept.dept_pid))) and str(deptdict[str(dept.dept_pid)].id) or 1
			        } 
			        # not dept.wx_synch_date 数据库没有同步日期
			        # dept.wx_synch_date < dept.synch_date 如果数据库同步时间大于微信通讯录同步时间
			        if reset or not dept.wx_synch_date or dept.synch_date > dept.wx_synch_date:
			            update_deptids.append(dept.id)
			            if wx_deptdict.has_key(str(dept['id'])):
			                if dept.is_del:
			                    self.delete_dept(deptid=dept.id) 
			                else:
			                    contacts.update_dept(wx_dept_data) 
			            else:
			            	#判断其上层部门是否删除
			                dept_isdel = __check_parent_isdel(str(dept.dept_id))
			                if not dept_isdel:
			                    contacts.create_dept(wx_dept_data)
			                    
			        if wx_deptdict.has_key(str(dept['id'])):
			            # 弹出已更新后的通讯录
			            wx_deptdict.pop(str(dept['id']))
            finally:
				if update_deptids:	
					cr.execute(u'''update wx_department set wx_synch_date = %s where id in %s''',(today,tuple(update_deptids)))											
					cr.commit()
					
	        	           
            # 剩下的就是数据库没有数据，但微信通讯录的有的，这些需要从微信通讯录删除
            for k,v in wx_deptdict.items():
                if k not in self._protected_dept and not reset:
	                self.delete_dept(deptid=k) 
	                
    def delete_dept(self, deptid=None):
        registry = RegistryManager.get(http.request.cr.dbname)
        with registry.cursor() as cr:
	        contacts = WChatContacts(self.__wxbasic)
	        wx_deptdict = {} 
	        dept_level = {}
	        delete_ids = [] 
	        members = [] 
	        wx_deptid = None
	        
	        if deptid:
		        cr.execute('''select id from wx_department where dept_id = %s''',(deptid))
		        wx_deptid = cr.fetchone()
	        
	        depts = contacts.get_dept_list()
	        if depts['errcode'] == 0:
	            for wxdept in depts['department']:
	                wx_deptdict[str(wxdept['id'])] = wxdept 
	                
	            for wxdept in depts['department']:
	                #计算部门的层级
	                self.__compute_dept_level(wx_deptdict,dept_level,str(wxdept['id']),str(wxdept['parentid']), deptid=wx_deptid)
	                       
	        try:
		        for k, v in sorted(dept_level.items(), key = lambda d : d[1], reverse=True):
					if k not in self._protected_dept:
						delete_ids.append(k)
						member = contacts.get_dept_members(k,fetch_child=1) #部门所有成员
						members = [x['userid'].lower() for x in member['userlist']]
						if members: contacts.delete_members(members) #删除部门下所有的成员
						contacts.delete_dept(k) #删除部门 
	        finally:
		        if delete_ids:
		            cr.execute('update wx_department set wx_synch_date = NULL where id in %s', (tuple(delete_ids),))
		            cr.commit()
		            
    def dept_amount(self):
        u'''
        查看部门总数
        '''
        contacts = WChatContacts(self.__wxbasic)
        depts = contacts.get_dept_list()
        if depts['errcode'] == 0:
            return len(depts['department'])
        else:
            return 'Something is wrong!'

    def __get_depts(self, synch_date):
        domain = []
#         if synch_date: domain.append(('write_date', '>', datetime.strptime(synch_date,'%Y-%m-%d %H:%M:%S.%f')))
        model="hr.department"  ##要运行哪个类中的函数？ 
        proxy = RPC.getProxy()
        ids = proxy.execute(RPC.DB,RPC.UID, RPC.PWD, model, 'search', domain, {}) 
        depts = proxy.execute(RPC.DB,RPC.UID, RPC.PWD, model, 'read', ids, ['id','parent_id','name','level','is_del']) 
        return  depts

    def __synch_department(self,reset=False):
        u'''
       同步本地与ERP企业系统的部门信息 
        '''        
        registry = RegistryManager.get(http.request.cr.dbname)
        wx_deptids = {}
        
        synch_date = None
        with registry.cursor() as cr:
            if reset:
                cr.execute(u''' delete from wx_department ''')
                cr.execute(u''' select setval('wx_department_id_seq', '''+self._base_deptid+''', true)''')
            else:
				# 本地部门数据
	            cr.execute(''' select id, dept_id from wx_department ''')
	            for dept in cr.fetchall():
	                wx_deptids[str(dept[1])] = str(dept[0])
				# 最后一次同步时间    
	            cr.execute(''' select max(synch_date) synch_date from wx_department ''')
	            synch_date = cr.fetchone()[0]
	            cond_synch_date = synch_date and ' and dtt.write_date > to_timestamp(\''+ synch_date +'\',\'YYYY-MM-DD HH24:MI:SS.MS\')' or '' 
                        
        erp_depts = self.__get_depts(synch_date)
        
        today = datetime.today()
        with registry.cursor() as cr:
            wx_dept= registry.get('wx.department')
            for dept in erp_depts:
                dept_vals = {
                        'dept_id': dept['id'],
                        'dept_pid': dept['parent_id'] and dept['parent_id'][0] or 1,
                        'dept_name': dept['name'],
                        'dept_name_encrypt': '部门【'+str(dept['id'])+'】' ,
                        'level': dept['level'],
                        'is_del': dept['is_del'],
                        'synch_date' : today,
                    }
                
            # update department
                if wx_deptids.has_key(str(dept['id'])):
                    wx_dept.write(cr, SUPERUSER_ID,int(wx_deptids[str(dept['id'])]),dept_vals)
            # insert department
                else:
                    wx_dept.create(cr, SUPERUSER_ID, dept_vals)
    
	#计算部门层级，删除部门时从最深层开始删除
    def __compute_dept_level(self, deptdict, level_dict, level_id, pid, level=1, parent_key='parentid', deptid=None):
        if deptid: 
            if str(deptid) == pid :
                level_dict[level_id] = level + 1
            elif level_id == str(deptid):
                level_dict[level_id] = level
            elif pid in self._protected_dept:
                return
        elif pid in self._protected_dept:
            level_dict[level_id] = level + 1
        elif level_dict.has_key(pid) and int(level_dict[pid]) > 1:
            level_dict[level_id] = level + int(level_dict[pid]) 
            
        if not level_dict.has_key(level_id):
	        self.__compute_dept_level(deptdict,level_dict,level_id,str(deptdict[pid][parent_key]), level+1, parent_key, deptid)
            

class MemberManager(object):
    
    def __init__(self,wxbasic):
        self.__wxbasic = wxbasic
        self.__protected_member = ['wx_admin']
        
    def update_memeber_by_workid(self,workids=None):
        if not workids: return
        
        registry = RegistryManager.get(http.request.cr.dbname)
        
        key = ''
        empdict = {}
        emps = self.__get_employee(None, None, workids)
        for emp in emps:
            key = str(emp['department_id'][0])
            if not empdict.has_key(key): empdict[key] = [] 
            empdict[key].append(emp['work_id'])
                
        for k, v in empdict.items():
            self.update_memeber(k, tuple(v))
            
            
        
    def update_memeber(self,deptid,workids=None, reset=False):
        u'''
       @param deptid: 企业部门ID 
       @param workids: 更新deptid部门下指定工号
       @param reset:	是否删除depid部门下的所有成员 
        '''
    	if not deptid :	
			raise NeedDeptIdError("{}: {}".format('NeedDeptIdError','NeedDeptIdError' ))
    	
        registry = RegistryManager.get(http.request.cr.dbname)
        contacts = WChatContacts(self.__wxbasic) 
        deptmgr = DeptManager(self.__wxbasic)
        today = datetime.today()
        empdict = {}    #wx.member字典
        wx_empdict = {} #微信通讯录成员字典
        deptdict = {} #key 部门真实ID, value微信通讯录部门ID
        
        with registry.cursor() as cr:
            wx_member = registry.get('wx.member')
            wx_dept = registry.get('wx.department')
            self.__synch_member(deptid, workids=workids, reset=reset)
            
            #更新通讯录部门
#             deptmgr.update_dept()
            # 查询微信通讯录已创建的部门, 来判断是更新还是新建微信通讯录部门
            wx_deptdict = deptmgr.get_wx_deptdict(contacts)
            #获取本志所有部门
            all_emps = wx_member.browse(cr, SUPERUSER_ID,wx_member.search(cr,SUPERUSER_ID,[('emp_deptid','=',deptid)]))
            #创建deptdict字典，key为部门真实id, 用来查询父部门
            for emp in all_emps:
                empdict[str(emp.emp_id)] = emp 
                
            #获取本志所有部门
            all_depts = wx_dept.browse(cr, SUPERUSER_ID,wx_dept.search(cr,SUPERUSER_ID,[]))
            #创建deptdict字典，key为部门真实id,value为微信通讯录部门ID 
            for dept in all_depts:
                deptdict[str(dept.dept_id)] = dept.id  #dept.id 对应的是微信通讯录部门ID
                
            # 获取微信通讯录全部成员 
            wx_emp = contacts.get_dept_members(deptdict[str(deptid)],fetch_child=1)
            userlist = []
            if wx_emp['errcode'] == 0 and wx_emp['userlist']:
            	for emp in wx_emp['userlist']:
                 	wx_empdict[str(emp['userid'])] =  True 
                 	userlist.append(emp['userid'].lower())
                     
                if reset:
					contacts.delete_members(userlist)
	                
	        userid = 'NOUSERID'
            for emp in all_emps:
                if not deptdict.has_key(str(emp.emp_deptid)) or not wx_deptdict.has_key(str(deptdict[str(emp.emp_deptid)])):
                   print '[WARNING][WX][UPDATE_MEMBER] The %s member\'s department is not exists!' % emp.id
                   continue 
                    
                emp_data = {
                    'userid': 'UID' + str(emp.id), 
                    'name': '成员[' + str(emp.id) + ']', 
                    'department':[deptdict[str(emp.emp_deptid)]], 
                    'mobile':emp.emp_mobile, 
                    'email': emp.emp_work_id.upper()+ '@billjc.com',
#                     'email': 'UID' + str(emp.id) + '@billjc.com', 
                } 
                # not dept.wx_synch_date 数据库没有同步日期
                # dept.wx_synch_date < dept.synch_date 如果数据库同步时间大于微信通讯录同步时间
                
                userid = 'UID' + str(emp['id'])
                if reset or not emp.wx_synch_date or emp.synch_date > emp.wx_synch_date:
                    if wx_empdict.has_key(userid):
                        if dept.is_del:
                            contacts.delete_member(str(emp.id)) 
                        else:
                            contacts.update_member(emp_data) 
                    else:
                        contacts.create_member(emp_data)
                        
	                cr.execute(u'''update wx_member set wx_synch_date = %s where id=%s''',(today,emp.id))                                            
	                cr.commit()
                
                if wx_empdict.has_key(userid):
                    # 弹出已更新后的通讯录
                    wx_empdict.pop(userid)
                
            # 剩下的就是数据库没有数据，但微信通讯录的有的，这些需要从微信通讯录删除
            for k,v in wx_empdict.items():
                if k not in self.__protected_member and not reset:
                    contacts.delete_member(str(k).lower()) 
                    
    def invite_memeber_by_workid(self,workids):
        if not workids: return
        
        registry = RegistryManager.get(http.request.cr.dbname)
        contacts = WChatContacts(self.__wxbasic) 
        wxids = []
        with registry.cursor() as cr:
            wx_member = registry.get('wx.member')
            ids = wx_member.search(cr,SUPERUSER_ID,[('emp_work_id','in',workids)])
            for id in ids:
                contacts.invite_member('uid' + str(id))
            
            
    def delete_memeber_by_workid(self,workids):
        if not workids: return
        
        registry = RegistryManager.get(http.request.cr.dbname)
        contacts = WChatContacts(self.__wxbasic) 
        wxids = []
        with registry.cursor() as cr:
            wx_member = registry.get('wx.member')
            ids = wx_member.search(cr,SUPERUSER_ID,[('emp_work_id','in',workids)])
            for id in ids:
                wxids.append('uid' + str(id))
                
            if wxids: contacts.delete_members(wxids)
            
            wx_member.unlink(cr,SUPERUSER_ID,ids)
    
    def memeber_amount(self,deptid): 
    	u'''
        查看部门总数
        '''
        registry = RegistryManager.get(http.request.cr.dbname)
        with registry.cursor() as cr:
            wx_dept = registry.get('wx.department')
            dept = wx_dept.browse(cr, SUPERUSER_ID,wx_dept.search(cr,SUPERUSER_ID,[('dept_id','=',deptid)]))
            if dept:
		        contacts = WChatContacts(self.__wxbasic)
		        members = contacts.get_dept_members(dept.id)
		        if members['errcode'] == 0:
		            return len(members['userlist'])
		        else:
		            return 'Something is wrong!'
		        pass
		    

    def __get_employee(self,synch_date, deptid, workids=None):
     
		proxy = RPC.getProxy() 
		domain = [('checkin_state','=','1'),('on_job_state.name','=','在职')] 
		if deptid: domain.append(('department_id.id','=',deptid))
		if workids: domain.append(('work_id','in',workids))
# 		if synch_date: domain.append(('write_date', '>', datetime.strptime(synch_date,'%Y-%m-%d %H:%M:%S.%f'))) 
		model="hr.employee"  ##要运行哪个类中的函数？ 
		fields = ['id','work_id','department_id','name_related','gender','work_email','mobile_phone','login','resource_id']
		ids = proxy.execute(RPC.DB,RPC.UID, RPC.PWD, model, 'search', domain, {}) 
		employees = proxy.execute(RPC.DB,RPC.UID, RPC.PWD, model, 'read', ids,fields ) 
		
		model="hr.employee"  ##要运行哪个类中的函数？ 
		fields = ['id','login']
		ids = proxy.execute(RPC.DB,RPC.UID, RPC.PWD, model, 'search', domain, {}) 
		users = proxy.execute(RPC.DB,RPC.UID, RPC.PWD, model, 'read', ids,fields ) 
		
		userdict = {}
		for user in users:
			userdict[user['login']] = user['id']
			
		for emp in employees:
			if userdict.has_key(emp['login']):
				emp['uid'] = userdict[emp['login']]
		
		return employees

    def __synch_member(self,deptid, workids=None, reset=False):
        u'''
       同步本地与ERP企业系统的员工信息 
        '''  
        registry = RegistryManager.get(http.request.cr.dbname)
        # 微信数据库成员
        wxdb_empids = {}
        synch_date = None
        
        with registry.cursor() as cr:
            if reset:
	            cr.execute(u''' delete from wx_member where emp_deptid = %r''' % (deptid,))
            else:
	        # 本地成员数据
	            cr.execute(u''' select id, emp_id from wx_member''')
	            for emp in cr.fetchall():
	                wxdb_empids[str(emp[1])] = str(emp[0])
	        # 最后一次同步时间    
	            cr.execute(u''' select max(synch_date) synch_date from wx_member''')
	            synch_date = cr.fetchone()[0]
	            cond_synch_date =  synch_date and  u' and emp.write_date > to_timestamp(\''+ synch_date +u'\',\'YYYY-MM-DD HH24:MI:SS.MS\')' or u'' 
                        
        erp_emps = self.__get_employee(synch_date,deptid, workids=workids)
        today = datetime.today()
        with registry.cursor() as cr:
            wx_member= registry.get('wx.member')
            for emp in erp_emps:
                emp_vals = {
                        'emp_id': emp['id'],
                        'emp_uid': emp.has_key('uid') and emp['uid'] or None,
                        'emp_work_id': emp['work_id'],
                        'emp_deptid': emp['department_id'][0],
                        'emp_name': emp['name_related'],
                        'emp_gender': emp['gender'] ,
                        'emp_email':  emp['work_email'],
                        'emp_mobile': emp['mobile_phone'],
                        'synch_date' : today,
                    }
                
            # update weixin member 
                if wxdb_empids.has_key(str(emp['id'])):
                    wx_member.write(cr, SUPERUSER_ID,int(wxdb_empids[str(emp['id'])]),emp_vals)
            # insert weixin member 
                else:
                    wx_member.create(cr, SUPERUSER_ID, emp_vals)
        