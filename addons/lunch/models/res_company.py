# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

from neoziv import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    lunch_minimum_threshold = fields.Float()
