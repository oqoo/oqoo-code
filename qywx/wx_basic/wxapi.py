#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import cgi
import json
import time
import urllib
import requests
from xml.dom import minidom
from StringIO import StringIO

from .wxmsg import MESSAGE_TYPES, UnknownMessage
from .exception import ParseError, NeedParseError, NeedParamError, OfficialAPIError
from .wxreply import TextReply, ImageReply, VoiceReply, VideoReply, FileReply, Article, ArticleReply
from .lib import disable_urllib3_warning
from .wxutil import req_get, req_post , transcoding, dicttojson
from WXBizMsgCrypt import WXBizMsgCrypt,XMLParse,SHA1,Prpcrypt,PKCS7Encoder

class WXApiParam:
	TOKEN = 'YI1PdMGV5rcYgsGWFWHfRTgRAql8w84'  # 公从平台设定的token
	AESKEY = 'LT7YTqWkePVScoUJkg62aGFhPKmVMsMU7WJw5zhSmge'  # 公从平台设定的EncodingAESKey
	CORPID = 'wxbe8617c40953d356'  # 企业号设置，贴作息里的CorpID

class WChatBasic(object):
    '''
    :微信参数相关
    :消息验证加密解密
    '''
    def __init__(self,secret=None,agentid=None, checkssl=False):
        '''
        :param secret: 微信管理组的凭证密钥
        :param agentid: 企业应用 ID 
        :param checkssl: 是否检查 SSL, 默认为 False, 可避免 urllib3 的 InsecurePlatformWarning 警告
        '''
        if not checkssl:
            disable_urllib3_warning()  # 可解决 InsecurePlatformWarning 警告
        self.__secret = secret
        self.__agentid = agentid 

        self.__access_token = None
        self.__access_token_expires_at = None
        self.__is_parse = False # 是否解析了消息
        self.__message = None   # 解析消息的实例
        
        # 解密加密，验证微信信息
        self.__wxcrypt = WXBizMsgCrypt(WXApiParam.TOKEN, WXApiParam.AESKEY, WXApiParam.CORPID)
        self._access_token
    @property
    def _access_token(self,override=True):
        if not WXApiParam.CORPID  or not self.__secret:
            raise NeedParamError('Please provide app_id and app_secret parameters in the construction of class.')

        if self.__access_token:
            now = time.time()
            if self.__access_token_expires_at - now > 60:
                return self.__access_token
        else:    
            response_json = req_get(
                        url="https://qyapi.weixin.qq.com/cgi-bin/gettoken",
                        params={
                            "corpid": WXApiParam.CORPID,
                            "corpsecret": self.__secret,
                        }
                    )
        
        if override:
            self.__access_token = response_json['access_token']
            self.__access_token_expires_at = int(time.time()) + response_json['expires_in']
        
        return self.__access_token
    
    def verifyURL(self, signature, timestamp, nonce, echostr):
        return self.__wxcrypt.VerifyURL(signature, timestamp, nonce, echostr)
    
    def encryptMsg(self, sReplyMsg, sNonce, timestamp = None):
        ret , sEncryptReplyMsg = self.__wxcrypt.EncryptMsg(sReplyMsg, sNonce, timestamp)
        return ret
    
    def decryptMsg(self, sPostData, sMsgSignature, sTimeStamp, sNonce):
        '''
           验证，解密信息
        '''
        result = {}
        ret, xml_content = self.__wxcrypt.DecryptMsg(sPostData, sMsgSignature, sTimeStamp, sNonce )
        
        if ret == 0:
            doc = minidom.parseString(xml_content)
            
            params = [ele for ele in doc.childNodes[0].childNodes
                      if isinstance(ele, minidom.Element)]
    
            for param in params:
                if param.childNodes:
                    text = param.childNodes[0]
                    result[param.tagName] = text.data
                    
            result['raw'] = xml_content
            result['type'] = result.pop('MsgType').lower()
            
            message_type = MESSAGE_TYPES.get(result['type'], UnknownMessage)
            self.__message = message_type(result)
            
        else:
            self.__is_parse = False
            
        return ret
    
    def get_message(self):
        '''
        获取解析好的 WechatMessage 对象
        :return: 解析好的 WechatMessage 对象
        '''
        return self.__message
    
    def get_agentid(self):
        return self.__agentid
    
class WChatMsg(object):
    '''
    :微信各种类型消息的回复
    '''
    def __init__(self,wcbasic):
        self.__wcbasic = wcbasic
        
    def sendTextMessage(self, content,escape=False):
        print '[WX][SEND_TEXT_MESSAGE]......'
        
        message = self.__wcbasic.get_message()
        reply_data = TextReply(message= message, content=content).render()
        self.__reply_message(reply_data)
    
    def sendImageMessage(self, media_id):
        print '[WX][SEND_IMAGE_MESSAGE]......'
        
        message = self.__wcbasic.get_message()
        reply_data = ImageReply(message=message, media_id=media_id).render()
        self.__reply_message(reply_data)
        
    def sendVoiceMessage(self, media_id):
        print '[WX][SEND_VOICE_MESSAGE]......'
        
        message = self.__wcbasic.get_message()
        reply_data = VoiceReply(message=message,media_id=media_id).render()
        self.__reply_message(reply_data)
    
    def sendVideoMessage(self, media_id, title=None, description=None):
        print '[WX][SEND_VIDEO_MESSAGE]......'
        
        message = self.__wcbasic.get_message()
        reply_data = VideoReply(message=message,media_id=media_id,title=title, description=description).render()
        self.__reply_message(reply_data)
    
    def sendFileMessage(self, media_id):
        print '[WX][SEND_FILE_MESSAGE]......'
        
        message = self.__wcbasic.get_message()
        reply_data = FileReply(message=message,media_id=media_id).render()
        self.__reply_message(reply_data)
        
    def sendNewsMessage(self, articles, mpnews_flag = False):
        print '[WX][SEND_NEWS_MESSAGE]......'
        
        message = self.__wcbasic.get_message()
        reply_data = ArticleReply(message=message, articles=articles, mpnews_flag=mpnews_flag).render()
        self.__reply_message(reply_data)
        
    def __reply_message(self,reply_data):
        access_token = self.__wcbasic._access_token
        return req_post(
            url='https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + access_token,
            data = reply_data 
        )
        
class WChatMenu(object):
    '''
    :微信各种类型消息的回复
    '''
    def __init__(self,wcbasic):
        self.__wcbasic = wcbasic
   
    def create_menu(self, menu_data):
        '''
        http://qydev.weixin.qq.com/wiki/index.php?title=创建应用菜单
        创建自定义菜单 ::
           {
    "button": [
        {
            "name": "扫码", 
            "sub_button": [
                {
                    "type": "scancode_waitmsg", 
                    "name": "扫码带提示", 
                    "key": "rselfmenu_0_0", 
                    "sub_button": [ ]
                }, 
                {
                    "type": "scancode_push", 
                    "name": "扫码推事件", 
                    "key": "rselfmenu_0_1", 
                    "sub_button": [ ]
                }
            ]
        }, 
        {
            "name": "发图", 
            "sub_button": [
                {
                    "type": "pic_sysphoto", 
                    "name": "系统拍照发图", 
                    "key": "rselfmenu_1_0", 
                   "sub_button": [ ]
                 }, 
                {
                    "type": "pic_photo_or_album", 
                    "name": "拍照或者相册发图", 
                    "key": "rselfmenu_1_1", 
                    "sub_button": [ ]
                }, 
                {
                    "type": "pic_weixin", 
                    "name": "微信相册发图", 
                    "key": "rselfmenu_1_2", 
                    "sub_button": [ ]
                }
            ]
        }, 
        {
            "name": "发送位置", 
            "type": "location_select", 
            "key": "rselfmenu_2_0"
        }
    ]
}
        :param menu_data: Python 字典
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][CREATE_MENU] %r' % dicttojson(menu_data)
        
        agentid = self.__wcbasic.get_agentid()
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/menu/create?access_token=ACCESS_TOKEN&agentid=AGENTID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('AGENTID', str(agentid))
        
        return req_post(url = url, data=dicttojson(menu_data))

    def delete_menu(self):
        '''
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][DELETE_MENU]......'

        agentid = self.__wcbasic.get_agentid()
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/menu/delete?access_token=ACCESS_TOKEN&agentid=AGENTID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('AGENTID', str(agentid))
        
        return req_get(url=url)

    def get_menu(self):
        '''
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][GET_MENU]......'
        
        agentid = self.__wcbasic.get_agentid()
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/menu/get?access_token=ACCESS_TOKEN&agentid=AGENTID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('AGENTID', str(agentid))
        
        return req_get(url=url)
   
class WChatMedia(object):
    '''
    :微信多媒体上传下载
    '''
    def __init__(self,wcbasic):
        self.__wcbasic = wcbasic
    
    def upload_media(self, media_type, media_file, extension=''):
        '''
            注意事项
上传的多媒体文件有格式和大小限制，如下：
图片（image）: 128K，支持JPG格式
语音（voice）：256K，播放长度不超过60s，支持AMR\MP3格式
视频（video）：1MB，支持MP4格式
缩略图（thumb）：64KB，支持JPG格式
媒体文件在后台保存时间为3天，即3天后media_id失效。

使用网页调试工具调试该接口
        :param media_type: 媒体文件类型，分别有图片（image）、语音（voice）、视频（video）和缩略图（thumb）
        :param media_file: 要上传的文件，一个 File object 或 StringIO object
        :param extension: 如果 media_file 传入的为 StringIO object，那么必须传入 extension 显示指明该媒体文件扩展名，如 ``mp3``, ``amr``；如果 media_file 传入的为 File object，那么该参数请留空
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        
        types = ['jpg', 'jpeg', 'amr', 'mp3', 'mp4','png']
        if not isinstance(media_file, file) and not isinstance(media_file, StringIO):
            raise ValueError('Parameter media_file must be file object or StringIO.StringIO object.')
        if isinstance(media_file, StringIO) and extension.lower() not in types:
            raise ValueError('Please provide \'extension\' parameters when the type of \'media_file\' is \'StringIO.StringIO\'.')
        if isinstance(media_file, file):
            extension = media_file.name.split('.')[-1]
            if extension.lower() not in types:
                raise ValueError('Invalid file type.')

        ext = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'amr': 'audio/amr',
            'mp3': 'audio/mpeg',
            'mp4': 'video/mp4',
        }
        if isinstance(media_file, StringIO):
            filename = 'temp.' + extension
        else:
            filename = os.path.basename(media_file.name)
            
        print '[WX][UPLOAD_MEDIA] media_file=%s' % filename 

        access_token = self.__wcbasic._access_token
        return req_post(
            url='https://qyapi.weixin.qq.com/cgi-bin/media/upload',
            params={
                "access_token": access_token,
                "type": media_type,
            },
            files={
                "media": (filename, media_file.read() + '\r\n'),
            }
        )

    def download_media(self, media_id, savepath):
        print '[WX][DOWNLOAD_MEDIA] media_id=%s' % media_id 
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/media/get?access_token=ACCESS_TOKEN&media_id=MEDIA_ID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('MEDIA_ID', media_id)
        return requests.get(url, stream=True)
    
class WChatContacts(object):
    '''
:通讯录管理
    :部门管理
    :成员管理
    :标签管理
    '''
    def __init__(self,wcbasic):
        self.__wcbasic = wcbasic
	    
    def create_dept(self, dept_data):
        '''
        请求包结构体为:

{
   "name": "广州研发中心",
   "parentid": "1",
   "order": "1",
   "id": "1"
}
        :param name: 部门名称。长度限制为1~64个字节
        :param parentid: 父亲部门id。根部门id为1
        :param order: 在父部门中的次序值。order值小的排序靠前。 不是必须
        :param id: 部门id，整型。指定时必须大于1，不指定时则自动生成  不是必须
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][CREATE_DEPT] %s', dicttojson(dept_data)
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/department/create?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_post(url = url,data=dicttojson(dept_data))
    
    
    def update_dept(self, dept_data):
        '''
        :param name: 部门名称。长度限制为1~64个字节
        :param parentid: 父亲部门id。根部门id为1
        :param order: 在父部门中的次序值。order值小的排序靠前。
        :param id: 部门id，整型。指定时必须大于1，不指定时则自动生成
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][UPDATE_DEPT] %s' % dicttojson(dept_data)
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/department/update?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_post(url = url,data=dicttojson(dept_data))

    def delete_dept(self, deptid):
        '''
        :param id: 部门id。获取指定部门id下的子部门
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][DELETE_DEPT] deptid=%s' % deptid
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/department/delete?access_token=ACCESS_TOKEN&id=DEPTID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('DEPTID', str(deptid))
        
        return req_get(url = url)
    
    def get_dept_list(self, deptid=None):
        '''
        :param id: 部门id。获取指定部门id下的子部门
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][GET_DEPT_LIST] deptid=%s' % deptid
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token=ACCESS_TOKEN&id=DEPTID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('DEPTID', str(deptid))
        
        return req_get(url = url)


    def create_member(self, member_data):
        '''
        :param data: 新建成员信息 
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][CREATE_MEMBER] %s' % dicttojson(member_data)
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/create?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_post(url=url, data=dicttojson(member_data))

    def update_member(self, member_data):
        '''
        :param data: 新建成员信息 
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][UPDATE_MEMBER] %s' % dicttojson(member_data)
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/update?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_post(url=url, data=dicttojson(member_data))
    
    def delete_member(self, userid):
        '''
        :param userid: 成员UserID。对应管理端的帐号 
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][DELETE_MEMBER] userid=%s' % str(userid)
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/delete?access_token=ACCESS_TOKEN&userid=USERID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('USERID', str(userid))
        
        return req_get(url=url)
    
    def delete_members(self, userids):
        '''
        :param useridlist: 成员UserID列表。对应管理端的帐号
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][DELETE_MEMBERS] userids=%s' % dicttojson(userids)
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/batchdelete?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_post(url=url, data=dicttojson({'useridlist':userids}))

    def get_member(self, userid):
        '''
        :param userid: 成员UserID。对应管理端的帐号
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][GET_MEMBER] userid=%s' % userid 
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token=ACCESS_TOKEN&userid=USERID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('USERID', userid)
        
        return req_get(url=url)
    
    def get_dept_members(self,dept_id,fetch_child=0,status=0):
        '''
        :param dept_id: 获取的部门id
        :param fetch_child: 1/0：是否递归获取子部门下面的成员
        :param status: 0获取全部成员，1获取已关注成员列表，2获取禁用成员列表，4获取未关注成员列表。status可叠加
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][GET_DEPT_MEMBERS] deptid=%s' % dept_id 
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?access_token=ACCESS_TOKEN&department_id=DEPARTMENT_ID&fetch_child=FETCH_CHILD&status=STATUS'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('DEPARTMENT_ID', str(dept_id))
        url = url.replace('FETCH_CHILD', str(fetch_child))
        url = url.replace('STATUS', str(status))
        
        return req_get(url=url)
    
    def get_dept_members_detail(self, dept_id,fetch_child=0,status=0):
        '''
        :param dept_id: 获取的部门id
        :param fetch_child: 1/0：是否递归获取子部门下面的成员
        :param status: 0获取全部成员，1获取已关注成员列表，2获取禁用成员列表，4获取未关注成员列表。status可叠加
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][GET_DEPT_MEMBERS_DETAIL] deptid=%s' % dept_id 
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token=ACCESS_TOKEN&department_id=DEPARTMENT_ID&fetch_child=FETCH_CHILD&status=STATUS'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('DEPARTMENT_ID', dept_id)
        url = url.replace('FETCH_CHILD', fetch_child)
        url = url.replace('STATUS', status)
        
        return req_get(url=url)
       
    def invite_member(self, userid):
    	'''
        :param userid: 微信成员ID 
        '''
        print '[WX][INVITE_MEMBER] userid=%s' % userid 
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/invite/send?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_post(url=url,data=dicttojson({'userid':userid}))
    
    def create_tag(self, tag_data):
        '''
请求包结构体为:
{
   "tagname": "UI"
}
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][CREATE_TAG] %s' % dicttojson(tag_data)
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/create?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_post(url = url,data=dicttojson(tag_data))
    
    def update_tag(self, tag_data):
        '''
请求包结构体为:
{
"tagid": "1",
"tagname": "UI design"
}
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][UPDATE_TAG] %s' % dicttojson(tag_data)
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/update?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_post(url = url,data=dicttojson(tag_data))

    def delete_tag(self, tagid):
        '''
        :param tagid: 标签ID
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][DELETE_TAG] tageid=%s' % tagid
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/delete?access_token=ACCESS_TOKEN&tagid=TAGID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('TAGID', tagid)
        
        return req_get(url = url)

    def get_tag_members(self, tagid):
        '''
        :param tagid: 标签ID
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][GET_TAG_MEMBERS] tageid=%s' % tagid
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/get?access_token=ACCESS_TOKEN&tagid=TAGID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('TAGID', tagid)
        
        return req_get(url = url)
    
    def add_tag_members(self, tag_member_data):
        '''
        请求包示例如下:

{
   "tagid": "1",
   "userlist":[ "user1","user2"],
   "partylist": [4]
}
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][ADD_TAG_MEMBERS] %s' % dicttojson(tag_member_data)
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/addtagusers?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_post(url = url, data = dicttojson(tag_member_data))

    def delete_tag_members(self, tag_member_data):
        '''
        请求包示例如下:

{
   "tagid": "1",
   "userlist":[ "user1","user2"],
   "partylist": [4]
}
userlist        企业成员ID列表，注意：userlist、partylist不能同时为空
partylist       企业部门ID列表，注意：userlist、partylist不能同时为空

        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][DELETE_TAG_MEMBERS] %s' % dicttojson(tag_member_data)
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/deltagusers?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_post(url = url, data = dicttojson(tag_member_data))
    
    def get_tags(self):
        '''
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        '''
        print '[WX][GET_TAGS]...........'
        
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/list?access_token=ACCESS_TOKEN'
        url = url.replace('ACCESS_TOKEN', access_token)
        
        return req_get(url = url)

class WChatOauth2(object):
    '''
    :OAuth2验证接口
    '''
    def __init__(self,wcbasic):
        self.__wcbasic = wcbasic

    def get_code(self,redirect_uri,state=None,wechat_redirect=None):
        '''
        :param redirect_uri: 授权后重定向的回调链接地址，请使用urlencode对链接进行处理
        :param state: 重定向后会带上state参数，企业可以填写a-zA-Z0-9的参数值，长度不可超过128个字节
        :param #wechat_redirect: 微信终端使用此参数判断是否需要带上身份信息
        '''
        print '[WX][GET_CODE]....'
        
        url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=CORPID&REDIRECT_URI&response_type=code&scope=snsapi_base&state=STATE#wechat_redirect'
        url = url.replace('CORPID', WXApiParam.CORPID)
        url = url.replace('REDIRECT_URI', urllib.urlencode({'redirect_uri':redirect_uri}))
        if state: url = url.replace('STATE', state)
        if wechat_redirect: url = url.replace('wechat_redirect', wechat_redirect)
        
        return url
    
    def get_code_member(self,code):
        '''
        根据code获取成员信息
        :param code:通过成员授权获取到的code，每次成员授权带上的code将不一样，code只能使用一次，5分钟未被使用自动过期
        '''
        print '[WX][GET_CODE_MEMBER]....'
        
        agentid = self.__wcbasic.get_agentid()
        access_token = self.__wcbasic._access_token
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo?access_token=ACCESS_TOKEN&code=CODE&agentid=AGENTID'
        url = url.replace('ACCESS_TOKEN', access_token)
        url = url.replace('AGENTID', str(agentid))
        url = url.replace('CODE', code)
        
        return req_get(url) 







    