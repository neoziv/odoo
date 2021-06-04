# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

{
    'name': 'neoziv Payments by Adyen Payment Acquirer',
    'category': 'Accounting/Payment Acquirers',
    'sequence': 330,
    'summary': 'Payment Acquirer: neoziv Payments by Adyen',
    'version': '1.0',
    'description': """neoziv Payments by Adyen""",
    'depends': ['payment', 'adyen_platforms'],
    'data': [
        'views/payment_views.xml',
        'views/payment_neoziv_by_adyen_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'application': True,
}
