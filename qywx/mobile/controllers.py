# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request 


class Mobile(http.Controller):

    def session_info(self):
        if not request.session.uid:
            try:
                request.session.assert_valid()
            except Exception:
                request.session.uid = None
        wxuser = request.session.has_key('wxuser') and request.session.wxuser or {}
        context = request.session.get_context() if request.session.uid else {}
        for k,v in wxuser.items(): context[k] = v
        
        return {
            "session_id": request.session_id,
            "uid": request.session.uid,
            "user_context": context,
            "db": request.session.db,
            "username": request.session.login,
            "company_id": request.env.user.company_id.id if request.session.uid else None,
        }

    @http.route('/mobile/session/get_session_info', type='json', auth="none")
    def get_session_info(self):
        request.uid = request.session.uid
        request.disable_db = False
        return self.session_info()