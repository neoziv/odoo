# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

import neoziv.tests
from neoziv import tools


@neoziv.tests.tagged('post_install', '-at_install')
class TestUi(neoziv.tests.HttpCase):
    def test_admin(self):
        self.start_tour("/", 'event', login='admin', step_delay=100)
