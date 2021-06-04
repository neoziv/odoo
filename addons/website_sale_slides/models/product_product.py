# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

from neoziv import fields, models


class Product(models.Model):
    _inherit = "product.product"

    channel_ids = fields.One2many('slide.channel', 'product_id', string='Courses')
