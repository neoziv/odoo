# -*- coding: utf-8 -*-	
# Part of neoziv. See LICENSE file for full copyright and licensing details.	

from neoziv import fields, models	


class ResConfigSettings(models.TransientModel):	
    _inherit = 'res.config.settings'	

    invoice_is_snailmail = fields.Boolean(string='Send by Post', related='company_id.invoice_is_snailmail', readonly=False)
