# -*- coding: utf-8 -*-
import werkzeug.utils
import urllib2
from openerp import http
from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager
from openerp.addons.wx_basic.wxapi import WXApiParam , WChatBasic, WChatOauth2

GET_CODE_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=CORPID&REDIRECT_URI&response_type=code&scope=SCOPE&state=STATE#wechat_redirect'
CODE_TO_USERINFO = 'https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo?access_token=ACCESS_TOKEN&code=CODE&agentid=AGENTID'
AGENTID = 2
SECRET = 'otSJTLUAOnZacpktKjIxjQ_zvs-GZHLZ9SvWX17BXiGEHWWlnRu75ZGA6rOMHOOJ'

WX_USER = 'wxuser'
USER_PWD = '123456'

class MobileTimesheet(http.Controller):
   
    @http.route('/mobile/mobile_timesheet/', auth='public')
    def index(self, **kw):
		session = http.request.session
        #是否确认微信用户信息
		if session.has_key('wxuser') or kw.has_key('allowpc'):
			return http.request.render('mobile_timesheet.client_bootstrap', qcontext={})
		else:
			return werkzeug.utils.redirect('/wchat/timesheet')     
		        
    
    @http.route('/wchat/timesheet', auth='none')
    def timesheet(self, **kw):
		session = http.request.session
		wxstate =  '' 
		page = 1
 	    # 用户登录 
		self.__check_login()
        #微信重定向，然后根据code获取微信用户信息
		if not session.has_key('wxuser') or not session['wxuser'].has_key('EmployeeUid') or not session['wxuser'].has_key('init_1'): 
			wxbasic = WChatBasic(secret=SECRET, agentid=AGENTID)
			wx_oauth2 = WChatOauth2(wxbasic)
			if kw.has_key('code') and kw.has_key('state'): 
				userinfo = wx_oauth2.get_code_member(kw['code'])
				userinfo = self.__set_empinfo(userinfo)
				session['wxuser'] = userinfo 
				userinfo['init_1'] = 'for initialize  session' 
				self.__set_cookie_and_session(userinfo) 
			else:                
				redirect_url='http://weixin.bill-jc.com/wchat/timesheet?' 
				for k,v in kw.items(): 
					redirect_url +=  str(k) + '=' + str(v) + '&' 
				                    
				if not wxstate : wxstate = None 
				get_codeurl = wx_oauth2.get_code(redirect_url,state=None,wechat_redirect=None) 
				response = werkzeug.utils.redirect(get_codeurl) 
				return response
        
        
		if kw.has_key('pg'): page = kw['pg']
		return werkzeug.utils.redirect('/mobile/mobile_timesheet/#page' + str(page))	 
    
    def __set_empinfo(self, userinfo):
        emp = {}
        workid = 'B-8509'
        empid = 26172
        empuid = 26172
        
        if userinfo['UserId'].startswith('UID'):
            registry = RegistryManager.get(http.request.cr.dbname)
            wx_member = registry.get('wx.member')
            emp = wx_member.browse(http.request.cr, SUPERUSER_ID, int(userinfo['UserId'].replace('UID','')))       
            workid = emp.emp_work_id 
            empid = emp.emp_id
            empuid = emp.emp_uid
        
        userinfo['WorkId'] = workid 
        userinfo['EmployeeId'] = empid
        userinfo['EmployeeUid'] = empuid 
                
        return userinfo
	           
    def __set_cookie_and_session(self, userinfo):
        session = http.request.session
        self.opener = urllib2.OpenerDirector()
        self.opener.add_handler(urllib2.HTTPCookieProcessor())
        self.opener.addheaders.append(('Cookie', 'userinfo=%s' % userinfo))
    
    def __check_login(self):
        session = http.request.session
        session.authenticate(http.request.cr.dbname, WX_USER, USER_PWD)
        
    
    @http.route('/wchat/write/<model("mobile_timesheet.sheet"):timesheet>/', auth='public')
    def timesheet_write(self):
        pass
    