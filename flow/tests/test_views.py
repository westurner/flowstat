import unittest

from pyramid import testing

from ..models.sql import _initialize_sql_test
from .. import _register_routes, _register_common_templates


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.session = _initialize_sql_test()
        self.config = testing.setUp()

    def tearDown(self):
        import transaction
        transaction.abort()
        testing.tearDown()


    def test_about_view(self):
        from ..views.about import about_view
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest()
        about_view(request)

