# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

import json
import logging
import pprint

from neoziv import http
from neoziv.http import request

_logger = logging.getLogger(__name__)


class neozivByAdyenController(http.Controller):
    _notification_url = '/payment/neoziv_adyen/notification'

    @http.route('/payment/neoziv_adyen/notification', type='json', auth='public', csrf=False)
    def neoziv_adyen_notification(self):
        data = json.loads(request.httprequest.data)
        _logger.info('Beginning neoziv by Adyen form_feedback with data %s', pprint.pformat(data)) 
        if data.get('authResult') not in ['CANCELLED']:
            request.env['payment.transaction'].sudo().form_feedback(data, 'neoziv_adyen')
