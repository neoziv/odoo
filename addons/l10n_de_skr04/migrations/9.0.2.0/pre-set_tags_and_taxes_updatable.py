# -*- coding: utf-8 -*-

import neoziv

def migrate(cr, version):
    registry = neoziv.registry(cr.dbname)
    from neoziv.addons.account.models.chart_template import migrate_set_tags_and_taxes_updatable
    migrate_set_tags_and_taxes_updatable(cr, registry, 'l10n_de_skr04')
