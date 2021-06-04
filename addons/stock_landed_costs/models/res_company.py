# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

from neoziv import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    lc_journal_id = fields.Many2one('account.journal')

