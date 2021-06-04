# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

import neoziv.tests
from neoziv.tools import mute_logger


@neoziv.tests.common.tagged('post_install', '-at_install')
class TestCustomSnippet(neoziv.tests.HttpCase):

    @mute_logger('neoziv.addons.http_routing.models.ir_http', 'neoziv.http')
    def test_01_run_tour(self):
        self.start_tour("/", 'test_custom_snippet', login="admin")
