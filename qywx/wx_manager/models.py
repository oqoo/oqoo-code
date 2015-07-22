# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from bsddb.dbtables import _columns

class wx_msg_count(osv.osv_memory):
    _name = 'wx.msg'  #表名
    _description = 'Wei xin message'

    _columns = {
        'msg_timestamp': fields.char('Message Timestamp', required=True),
    }
    
    
class wx_department(osv.osv):
    _name = 'wx.department'
    _description = 'Weixin department'
    
    _columns = {
        'dept_id' : fields.integer('Department ID'),
        'dept_pid' : fields.integer('Department ID'),
        'dept_name': fields.char('Department Name',size=64),
        'dept_name_encrypt': fields.char('Department Name Encrypt', size=64),
        'level' : fields.integer('Level'),
        'is_del' : fields.boolean('Is Delete'),
        'synch_date': fields.datetime('Synch Date'),
        'wx_synch_date': fields.datetime('WX Synch Date'),
    }
    
class wx_member(osv.osv):
    _name = 'wx.member'
    _description = 'Wexin member'
    
    _columns = {
        'emp_id' : fields.integer('Employee ID'),
        'emp_uid' : fields.integer('User ID'),
        'emp_deptid' : fields.integer('Department ID'),
        'emp_work_id' : fields.char('Employee Work ID',size=12),
        'emp_name': fields.char('Employee Name',size=64),
        'emp_gender' : fields.boolean('Employee gender'),
        'emp_email': fields.char('Employee email',size=128),
        'emp_mobile': fields.char('Employee mobile',size=128),
        'synch_date': fields.datetime('Synch Date'),
        'wx_synch_date': fields.datetime('WX Synch Date'),
    }
