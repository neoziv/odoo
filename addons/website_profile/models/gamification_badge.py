# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

from neoziv import models


class GamificationBadge(models.Model):
    _name = 'gamification.badge'
    _inherit = ['gamification.badge', 'website.published.mixin']
