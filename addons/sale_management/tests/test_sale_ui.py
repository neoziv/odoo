import neoziv.tests
# Part of neoziv. See LICENSE file for full copyright and licensing details.


@neoziv.tests.tagged('post_install', '-at_install')
class TestUi(neoziv.tests.HttpCase):

    def test_01_sale_tour(self):
        self.start_tour("/web", 'sale_tour', login="admin", step_delay=100)
