# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

{
    'name': "India Sales and Warehouse Management",

    'summary': """
        Define default sales journal on the warehouse""",

    'description': """
        Define default sales journal on the warehouse,
        help you to choose correct sales journal on the sales order when
        you change the warehouse.
        useful when you setup the multiple GSTIN units.
    """,

    'author': "neoziv",
    'website': "https://www.neoziv.com",
    'category': 'Accounting/Localizations/Sale',
    'version': '0.1',

    'depends': ['l10n_in_sale', 'l10n_in_stock'],

    'data': [
        'views/stock_warehouse_views.xml',
    ],
    'auto_install': True
}
