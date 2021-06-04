# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

import neoziv.tests
from neoziv import tools


@neoziv.tests.tagged('post_install', '-at_install')
class TestUi(neoziv.tests.HttpCase):
    def test_admin(self):
        self.env['blog.blog'].create({'name': 'Travel'})
        self.env['ir.attachment'].create({
            'public': True,
            'type': 'url',
            'url': '/web/image/123/transparent.png',
            'name': 'transparent.png',
            'mimetype': 'image/png',
        })
        self.start_tour("/", 'blog', login='admin')
