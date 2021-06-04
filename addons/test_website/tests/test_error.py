import neoziv.tests
from neoziv.tools import mute_logger


@neoziv.tests.common.tagged('post_install', '-at_install')
class TestWebsiteError(neoziv.tests.HttpCase):

    @mute_logger('neoziv.addons.http_routing.models.ir_http', 'neoziv.http')
    def test_01_run_test(self):
        self.start_tour("/test_error_view", 'test_error_website')
