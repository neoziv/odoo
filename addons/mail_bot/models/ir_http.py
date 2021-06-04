# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

from neoziv import models


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super(Http, self).session_info()
        if self.env.user.has_group('base.group_user'):
            res['neozivbot_initialized'] = self.env.user.neozivbot_state not in [False, 'not_initialized']
        return res
