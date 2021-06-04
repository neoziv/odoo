# Part of neoziv. See LICENSE file for full copyright and licensing details.

import neoziv.tests


@neoziv.tests.tagged('post_install', '-at_install')
class TestUi(neoziv.tests.HttpCase):

    def test_01_project_tour(self):
        self.start_tour("/web", 'project_tour', login="admin")
