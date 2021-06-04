# -*- coding: utf-8 -*-

from neoziv import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_l10n_mx_edi = fields.Boolean('Mexican Electronic Invoicing')
