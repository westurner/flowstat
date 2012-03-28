import unittest
from pyramid import testing

from .... import _register_routes
from .... import _register_common_templates

from ...models import NumbersContextFactory
from ...views import NumberGraphRESTfulView



#class NumberGraphContextModelTests(unittest.TestCase):
    #def setUp(self):
        ##self.session = _initialize_sql_test()
        #self.config = testing.setUp()
        #_register_routes(self.config)
        #_register_common_templates(self.config)

    #def tearDown(self):
        #import transaction
        #transaction.abort()
        #testing.tearDown()

    #def test_get_number(self):
        #req = testing.DummyRequest()
        #ncf = NumbersContextFactory(req)


#class NumberGraphRESTfulViewTests(unittest.TestCase):
    ##def render_to_response(self, member):

    #def setUp(self):
        #req = testing.DummyRequest()
        #self.ngf = NumberGraphRESTfulView(NumbersContextFactory(req))

    #def test_determine_renderer(self):
        #renderer = self.ngf.determine_renderer()
        #self.failIfNone(renderer)

    #def test_render_to_response(self):
        #value = None
        #fields = None
        #self.ngf.render_to_response(value, fields=fields)

    #def test_render_to_404(self):
        #value = None
        #redirect = self.ngf.render_to_404(value)
        #self.failIfNone(value)
        #self.failIfNone(redirect)

    #def test_render_json(self):
        #value = dict(one='two', three=4.0)
        #_json = self.ngf.render_json(value)
        #self.failIfNone(_json)

    #def test_render_html(self, value):
        #value = dict(one='two', three=4.0)
        #_json = self.ngf.render_html(value)
        #self.failIfNone(_json)

    #def testrender_graphml(self, value):
        #value = dict(one='two', three=4.0)
        #_json = self.ngf.render_html(value)
        #self.failIfNone(_json)
