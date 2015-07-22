# -*- coding: utf-8 -*-
import time
from datetime import datetime

from openerp import http
from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager
from openerp.modules.module import get_module_resource
from openerp.addons.wx_basic.wxapi import * 

from wxmanager import *
from exception import *


AGENTID = 2
SECRET = 'otSJTLUAOnZacpktKjIxjQ_zvs-GZHLZ9SvWX17BXiGEHWWlnRu75ZGA6rOMHOOJ'

class WXManager(http.Controller):
    
    def __get_param(self, dict, key):
        if dict.has_key(key):
            return dict[key]
        else:
            return None
        
    # 接收用户信息，处理后调用微信API回复用户消息
    @http.route('/wchat/', auth='public')
    def wx_callback(self, **kw):
        # 实例化 wechat
		wxbasic = WChatBasic(secret=SECRET, agentid=AGENTID)
		sMsgSignature = self.__get_param(kw, 'msg_signature')
		sTimeStamp = self.__get_param(kw, 'timestamp')
		sNonce = self.__get_param(kw, 'nonce')
		sEchoStr = self.__get_param(kw, 'echostr')
		sReplyMsg = None
        
		repeat = self.__check_msg_repeat(sTimeStamp)
		        
		if not repeat:
			if sEchoStr:
			    # 开启应用的回调模式, 验证URL
			    # @return：成功0，失败返回对应的错误码    
			    ret, sReply = wxbasic.verifyURL(sMsgSignature, sTimeStamp, sNonce, sEchoStr)
			    return sReply
			        
			# 微信回调企业调口，POST数据是对消息的处理
			elif http.request.httprequest.method == 'POST':
				instream = http.request.httprequest.input_stream
				sPostData = instream.read(instream.bufsize)
				            
				# 解密接收的消息
				ret = wxbasic.decryptMsg(sPostData, sMsgSignature, sTimeStamp, sNonce)
				message = wxbasic.get_message()
				            
				# 业务处理
				if ret == 0:
					self._process_biz(wxbasic)
		                
		return ''
    
    def _process_biz(self, wxbasic):
        file = None
        message = wxbasic.get_message()
		# 实例化 wechat
        wxmsg = WChatMsg(wxbasic)
        wcmedia = WChatMedia(wxbasic)
        
        help = {'content':'''
发送【】里数字测消息接口:
【10】text消息
【11】image消息
【12】voice消息
【13】video消息
【14】file消息
【15】news消息
【16】创建菜单

【20】 初始部门 
【21】 更新部门
【22】 删除交付中心研发部
【23】 查询部门数
 
【30】 初始交付中心部门成员
【31】 更新交付中心部门成员
【32】 交付中心部门成员总数
【1@工号:工号:...】 增加成员
【2@工号:工号:...】  删除成员
【3@工号:工号:...】 邀请成员

'''}
        subscribe = [{"title":"欢迎使用微信工时填报"
                      , "description":"欢迎使用微信工时填报, 公司规定员工必须在每周二之前完成上一周的工时填报．"
                      , "url":u'http://weixin.bill-jc.com/wchat/timesheet'
                      , "picurl":u'http://weixin.bill-jc.com/wx_manager/static/img/enter_agent.png'
                    }]
        #成员进入应用的事件
        if message.type == 'subscribe':
            wxmsg.sendNewsMessage(subscribe) 
        
        elif message.type == 'text':
            content = message.content
            
            if content == '00001011':
	           wxmsg.sendTextMessage(help['content'])
            elif content == '10':
	           wxmsg.sendTextMessage('这是一条文本消息!')
            elif message.content == '11':
				imgpath = get_module_resource('wx_manager', 'static/img', 'test.png')
				try:
					file = open(imgpath, 'rb')
					media_id = wcmedia.upload_media('image', file)['media_id']
					wxmsg.sendImageMessage(media_id)
				except IOError:
					raise ValueError('file not exist') 
            elif content == '12':
				voicepath = get_module_resource('wx_manager', 'static/voice', 'purr.mp3')
				try:
					file = open(voicepath, 'rb')
					media_id = wcmedia.upload_media('voice', file)['media_id']
					wxmsg.sendVoiceMessage(media_id)
				except IOError:
					raise ValueError('file not exist') 
            elif content == '13':
				videopath = get_module_resource('wx_manager', 'static/video', '123.mp4')
				try:
					file = open(videopath, 'rb')
					media_id = wcmedia.upload_media('video', file)['media_id']
					wxmsg.sendVideoMessage(media_id, '视频标题', '视频描述')
				except IOError:
					raise ValueError('file not exist') 
            elif content == '14':
				filepath = get_module_resource('wx_manager', 'static/voice', 'purr.mp3')
				try:
					file = open(filepath, 'rb')
					media_id = wcmedia.upload_media('file', file)['media_id']
					wxmsg.sendFileMessage(media_id)
				except IOError:
					raise ValueError('file not exist') 
            elif content == '15':
				url = u'http://weixin.bill-jc.com/wx_manager/static/img/test.png'
				itmes = [{"title":"图文消息标题1", "description":"DESCRIPTION1", "url":url, "picurl":url},
                 {"title":"图文消息标题2", "description":"DESCRIPTION2", "url":url, "picurl":url},
                 {"title":"图文消息标题3", "description":"DESCRIPTION3", "url":url, "picurl":url}]
                     
				wxmsg.sendNewsMessage(itmes) 
            elif content == '16':
 				self.__create_menu(wxbasic)
                 
            elif content == '20':
			    wxdept = DeptManager(wxbasic)
			    wxdept.update_dept(reset=True) 
            elif content == '21':
			    wxdept = DeptManager(wxbasic)
			    wxdept.update_dept() 
            elif content == '22':
			    wxdept = DeptManager(wxbasic)
			    wxdept.delete_dept(133) # 133是交付中心部门ID
            elif content == '23':
			    wxdept = DeptManager(wxbasic)
			    amount = wxdept.dept_amount()
			    wxmsg.sendTextMessage('部门总数:' + str(amount))
               
            elif content == '30': 
                wxmember = MemberManager(wxbasic) 
                wxmember.update_memeber(deptid=589,reset=True) #589是交付中心部门ID
            elif content == '31': 
                wxmember = MemberManager(wxbasic) 
                wxmember.update_memeber(deptid=589) # 589是交付中心部门ID
            elif content == '32':
 			    wxmember = MemberManager(wxbasic)
  			    amount = wxmember.memeber_amount(589)  # 589是交付中心部门ID
 			    wxmsg.sendTextMessage('交付中心部门成员总数:' + str(amount))
            elif content.startswith('1@') or content.startswith('2@') or content.startswith('3@'): 
                workids = []
                wxmember = MemberManager(wxbasic) 
                
                if content.startswith('1@'):
                    ids= content.replace('1@','').split(':')
                elif content.startswith('2@'):
                    ids= content.replace('2@','').split(':')
                elif content.startswith('3@'):
                    ids= content.replace('3@','').split(':')
                    
                for id in ids:
                    workids.append('B-' + id.strip())
                
                if workids[0] != '': 
                    if content.startswith('1@'):
	                    wxmember.update_memeber_by_workid(workids=tuple(workids))
                    elif content.startswith('2@'):
	                    wxmember.delete_memeber_by_workid(workids=tuple(workids))
                    elif content.startswith('3@'):
	                    wxmember.invite_memeber_by_workid(workids=tuple(workids))
                
            else:
	            wxmsg.sendNewsMessage(subscribe) 
        
        if file:
            file.close()
        
    def __check_msg_repeat(self, sTimeStamp):
		repeat = True 
		registry = RegistryManager.get(http.request.cr.dbname)
        
		with registry.cursor() as cr:
			wxmsgcount = registry.get('wx.msg')
			msgcount = wxmsgcount.search(cr, SUPERUSER_ID, [('msg_timestamp', '=', sTimeStamp)])
            
			if not msgcount:
				repeat = False 
				wxmsgcount.create(cr, SUPERUSER_ID, {'msg_timestamp':sTimeStamp})
            
		return repeat            
    
    def __create_menu(self, wxbasic):
        menu_data = {
    "button": [
        {
            "name": "我的工时",
            "type": "view",
            "url": "http://weixin.bill-jc.com/wchat/timesheet?pg=4"
        }, 
        {
            "name": "工时填报",
            "type": "view",
            "url": "http://weixin.bill-jc.com/wchat/timesheet"
        }
    ]
}
        wxmenu = WChatMenu(wxbasic) 
        wxmenu.delete_menu()
        wxmenu.create_menu(menu_data)
    
   
