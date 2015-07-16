# -*- coding: utf-8 -*-
from .wxutil import xmltojson, xmltodict, dicttojson
from .wxmsg import WechatMessage

class WechatReply(object):
    def __init__(self, message=None, **kwargs):
        if 'touser' not in kwargs and isinstance(message, WechatMessage):
            kwargs['target'] = message.source
        if 'agentid' not in kwargs and isinstance(message, WechatMessage):
            kwargs['agentid'] = message.agentid
        if 'toparty' not in kwargs:
            kwargs['toparty'] = None 
        if 'totag' not in kwargs:
            kwargs['totag'] = None 
        if 'safe' not in kwargs:
            kwargs['safe'] = 0 

        self._args = dict()
        for k, v in kwargs.items():
            self._args[k] = v

    def render(self):
        raise NotImplementedError()

class TextReply(WechatReply):
    """
    回复文字消息
    """
    TEMPLATE = u"""
    <xml>
    <touser><![CDATA[{target}]]></touser>
    <toparty><![CDATA[{toparty}]]></toparty>
    <totag><![CDATA[{totag}]]></totag>
    <msgtype><![CDATA[text]]></msgtype>
    <agentid><![CDATA[{agentid}]]></agentid>
    <text>
    <content><![CDATA[{content}]]></content>
    </text>
    <safe><![CDATA[{safe}]]></safe>
    </xml>
    """
    def __init__(self, message, content):
        """
        :param message: WechatMessage 对象
        :param content: 文字回复内容
        """
        super(TextReply, self).__init__(message=message, content=content)

    def render(self):
        sXml = TextReply.TEMPLATE.format(**self._args)
        return xmltojson(sXml)
        
class ImageReply(WechatReply):
    """
    回复图片消息
    """
    TEMPLATE = u"""
    <xml>
    <touser><![CDATA[{target}]]></touser>
    <toparty><![CDATA[{toparty}]]></toparty>
    <totag><![CDATA[{totag}]]></totag>
    <msgtype><![CDATA[image]]></msgtype>
    <agentid><![CDATA[{agentid}]]></agentid>
    <image>
    <media_id><![CDATA[{media_id}]]></media_id>
    </image>
    <safe><![CDATA[{safe}]]></safe>
    </xml>
    """

    def __init__(self, message, media_id):
        """
        :param message: WechatMessage 对象
        :param media_id: 图片的 MediaID
        """
        super(ImageReply, self).__init__(message=message, media_id=media_id)

    def render(self):
        sXml = ImageReply.TEMPLATE.format(**self._args)
        return xmltojson(sXml)


class VoiceReply(WechatReply):
    """
    回复语音消息
    """
    TEMPLATE = u"""
    <xml>
    <touser><![CDATA[{target}]]></touser>
    <toparty><![CDATA[{toparty}]]></toparty>
    <totag><![CDATA[{totag}]]></totag>
    <msgtype><![CDATA[voice]]></msgtype>
    <agentid><![CDATA[{agentid}]]></agentid>
    <voice>
    <media_id><![CDATA[{media_id}]]></media_id>
    </voice>
    <safe><![CDATA[{safe}]]></safe>
    </xml>
    """

    def __init__(self, message, media_id):
        """
        :param message: WechatMessage 对象
        :param media_id: 语音的 MediaID
        """
        super(VoiceReply, self).__init__(message=message, media_id=media_id)

    def render(self):
        sXml = VoiceReply.TEMPLATE.format(**self._args)
        return xmltojson(sXml)


class VideoReply(WechatReply):
    """
    回复视频消息
    """
    TEMPLATE = u"""
    <xml>
    <touser><![CDATA[{target}]]></touser>
    <toparty><![CDATA[{toparty}]]></toparty>
    <totag><![CDATA[{totag}]]></totag>
    <msgtype><![CDATA[video]]></msgtype>
    <agentid><![CDATA[{agentid}]]></agentid>
    <video>
    <media_id><![CDATA[{media_id}]]></media_id>
    <title><![CDATA[{title}]]></title>
    <description><![CDATA[{description}]]></description>
    </video>
    <safe><![CDATA[{safe}]]></safe>
    </xml>
    """

    def __init__(self, message, media_id, title=None, description=None):
        """
        :param message: WechatMessage对象
        :param media_id: 视频的 MediaID
        :param title: 视频消息的标题
        :param description: 视频消息的描述
        """
        title = title or ''
        description = description or ''
        super(VideoReply, self).__init__(message=message, media_id=media_id, title=title, description=description)

    def render(self):
        sXml = VideoReply.TEMPLATE.format(**self._args)
        return xmltojson(sXml)
    

class FileReply(WechatReply):
    """
    回复视频消息
    """
    TEMPLATE = u"""
    <xml>
    <touser><![CDATA[{target}]]></touser>
    <toparty><![CDATA[{toparty}]]></toparty>
    <totag><![CDATA[{totag}]]></totag>
    <msgtype><![CDATA[file]]></msgtype>
    <agentid><![CDATA[{agentid}]]></agentid>
    <file>
    <media_id><![CDATA[{media_id}]]></media_id>
    </file>
    <safe><![CDATA[{safe}]]></safe>
    </xml>
    """

    def __init__(self, message, media_id):
        """
        :param message: WechatMessage 对象
        :param media_id: 语音的 MediaID
        """
        super(FileReply, self).__init__(message=message, media_id=media_id)

    def render(self):
        sXml = FileReply.TEMPLATE.format(**self._args)
        return xmltojson(sXml)


class Article(object):
    def __init__(self, title=None, description=None, picurl=None, url=None):
        self.title = title or ''
        self.description = description or ''
        self.picurl = picurl or ''
        self.url = url or ''


class ArticleReply(WechatReply):
    TEMPLATE = u"""
    <xml>
    <touser><![CDATA[{target}]]></touser>
    <toparty><![CDATA[{toparty}]]></toparty>
    <totag><![CDATA[{totag}]]></totag>
    <msgtype><![CDATA[news]]></msgtype>
    <agentid><![CDATA[{agentid}]]></agentid>
    <news><articles></articles></news>
    </xml>
    """
    ITEM_TEMPLATE = u"""
    <xml>
    <title><![CDATA[{title}]]></title>
    <description><![CDATA[{description}]]></description>
    <url><![CDATA[{url}]]></url>
    <picurl><![CDATA[{picurl}]]></picurl>
    </xml>
    """
    MP_TEMPLATE = u"""
    <xml>
    <touser><![CDATA[{target}]]></touser>
    <toparty><![CDATA[{toparty}]]></toparty>
    <totag><![CDATA[{totag}]]></totag>
    <msgtype><![CDATA[news]]></msgtype>
    <agentid><![CDATA[{agentid}]]></agentid>
    <mpnews><articles></articles></mpnews>
    </xml>
    """
    MP_ITEM_TEMPLATE = u"""
    <xml>
    <title><![CDATA[{title}]]></title>
    <thumb_media_id><![CDATA[{thumb_media_id}]]></thumb_media_id>
    <author><![CDATA[{author}]]></author>
    <content_source_url><![CDATA[{content_source_url}]]></content_source_url>
    <content><![CDATA[{content}]]></content>
    <digest><![CDATA[{digest}]]></digest>
    <show_cover_pic><![CDATA[{show_cover_pic}]]></show_cover_pic>
    </xml>
    """

    def __init__(self, message, articles, mpnews_flag = False):
        super(ArticleReply, self).__init__(message, articles=articles)
        self._articles = articles
        self._mpnews_flag = mpnews_flag
        if len(self._articles) >= 10:
            raise AttributeError("Can't add more than 10 articles in an ArticleReply")

    def render(self):
        articles = []
        resutldict = {}
        if self._mpnews_flag:
            resutldict = xmltodict(ArticleReply.MP_TEMPLATE.format(**self._args))
        else:
	        resutldict = xmltodict(ArticleReply.TEMPLATE.format(**self._args))
            
        
        for article in self._articles:
            if self._mpnews_flag: # MPNEWS
                item = ArticleReply.MP_ITEM_TEMPLATE.format(
                    title=article['title'],
                    thumb_media_id=article['thumb_media_id'],
                    author=article['author'],
                    content_source_url=article['content_source_url'],
                    content=article['content'],
                    digest=article['digest'],
                    show_cover_pic=article['show_cover_pic'],
                )
            else:
                item = ArticleReply.ITEM_TEMPLATE.format(
                    title=article['title'],
                    description=article['description'],
                    picurl=article['picurl'],
                    url=article['url'],
                )
            articles.append(xmltodict(item)['xml'])
            
        if self._mpnews_flag:
	        resutldict['xml']['mpnews']['articles'] = articles          
        else:
	        resutldict['xml']['news']['articles'] = articles          
        
        return dicttojson(resutldict['xml'])

