# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

from neoziv import http
from neoziv.http import request


class AdyenPlatformsController(http.Controller):

    @http.route('/adyen_platforms/create_account', type='http', auth='user', website=True)
    def adyen_platforms_create_account(self, creation_token):
        request.session['adyen_creation_token'] = creation_token
        return request.redirect('/web?#action=adyen_platforms.adyen_account_action_create')
