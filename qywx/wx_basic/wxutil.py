#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import random 
import mimetypes
import mimetools
import json 
import requests
from . import xmltodict as xd 
from .exception import ParseError, NeedParseError, NeedParamError, OfficialAPIError

# xml, dict, json 间的转换
def xmltodict(xmlstr):
    return xd.parse(xmlstr)

def xmltojson(xmlstr):
    return _json_loads(xmlstr)

def dicttojson(dict):
    returnobj = {}
    unicodeJson = json.loads(json.dumps(dict,ensure_ascii=False))
    return json.dumps(unicodeJson, ensure_ascii=False).encode('utf-8') 

def _json_loads(data):
    returnobj = {}
    unicodeJson = json.loads(json.dumps(xd.parse(data),  ensure_ascii=False))
    
    return json.dumps(unicodeJson['xml'], ensure_ascii=False).encode('utf-8')

# Dict 内容编码
def transcoding(data, code='utf-8'):
    result = None
    
    if not data:
        return data
   
    elif isinstance(data, str):
        result = data.decode(code)
        
    elif  isinstance(data, dict):
       result =  _transcoding_dict(data)
       
    elif  isinstance(data, list):
       result =  _transcoding_list(data)
    else:
        result = data
        
    return result

def _transcoding_list(data):
    if not isinstance(data, list):
        raise ValueError('Parameter data must be list object.')

    result = []
    for item in data:
        if isinstance(item, dict):
            result.append(_transcoding_dict(item))
        elif isinstance(item, list):
            result.append(_transcoding_list(item))
        else:
            result.append(item)
    return result

def _transcoding_dict(data):

    if not isinstance(data, dict):
        raise ValueError('Parameter data must be dict object.')

    result = {}
    for k, v in data.items():
        k = self._transcoding(k)
        if isinstance(v, dict):
            v = _transcoding_dict(v)
        elif isinstance(v, list):
            v = _transcoding_list(v)
        else:
            v = transcoding(v)
        result.update({k: v})
    return result


# HTTPP 请求
def req_get(url, **kwargs):
    return _request(
        method="get",
        url=url,
        **kwargs
    )

def req_post(url, **kwargs):
    return _request(
        url = url,
        method = "post",
        **kwargs
    )
        
def _request(method, url, **kwargs):
    r = requests.request(
        url = url,
        method = method,
        **kwargs
    )
        
    r.raise_for_status()
    response_json = r.json()
    _check_official_error(response_json)
    return response_json

def _check_official_error(json_data):
    if "errcode" in json_data and json_data["errcode"] != 0:
        print "[ERROR][WXAPI]---> {}: {}".format(json_data["errcode"], json_data["errmsg"])
        raise OfficialAPIError("{}: {}".format(json_data["errcode"], json_data["errmsg"]))
    
