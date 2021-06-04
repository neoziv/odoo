import neoziv.tests
from neoziv.tools import mute_logger


@neoziv.tests.common.tagged('post_install', '-at_install')
class TestWebsiteSession(neoziv.tests.HttpCase):

    def test_01_run_test(self):
        self.start_tour('/', 'test_json_auth')
