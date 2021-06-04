# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

from neoziv import fields, models


class Lead(models.Model):
    _inherit = 'crm.lead'

    reveal_id = fields.Char(string='Reveal ID', help="Technical ID of reveal request done by IAP.")
