# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

from neoziv import api, models, fields
from neoziv.http import request
from neoziv.addons.http_routing.models.ir_http import url_for


class View(models.Model):
    _inherit = "ir.ui.view"

    customize_show = fields.Boolean("Show As Optional Inherit", default=False)

    @api.model
    def _prepare_qcontext(self):
        """ Returns the qcontext : rendering context with portal specific value (required
            to render portal layout template)
        """
        qcontext = super(View, self)._prepare_qcontext()
        if request and getattr(request, 'is_frontend', False):
            Lang = request.env['res.lang']
            portal_lang_code = request.env['ir.http']._get_frontend_langs()
            qcontext.update(dict(
                self._context.copy(),
                languages=[lang for lang in Lang.get_available() if lang[0] in portal_lang_code],
                url_for=url_for,
            ))
        return qcontext
