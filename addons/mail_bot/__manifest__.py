# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

{
    'name': 'neozivBot',
    'version': '1.2',
    'category': 'Productivity/Discuss',
    'summary': 'Add neozivBot in discussions',
    'description': "",
    'website': 'https://www.neoziv.com/page/discuss',
    'depends': ['mail'],
    'auto_install': True,
    'installable': True,
    'application': False,
    'data': [
        'views/assets.xml',
        'views/res_users_views.xml',
        'data/mailbot_data.xml',
    ],
    'demo': [
        'data/mailbot_demo.xml',
    ],
    'qweb': [
        'static/src/bugfix/bugfix.xml',
    ],
}
