# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

from neoziv import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_process_edi_web_services(self):
        return self.move_id.action_process_edi_web_services()
