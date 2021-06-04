# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

import neoziv
import neoziv.tests


@neoziv.tests.common.tagged('post_install', '-at_install', 'website_snippets')
class TestSnippets(neoziv.tests.HttpCase):

    def test_01_empty_parents_autoremove(self):
        self.start_tour("/?enable_editor=1", "snippet_empty_parent_autoremove", login='admin')
