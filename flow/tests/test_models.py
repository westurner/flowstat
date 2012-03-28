# -*- coding: utf-8 -*-


import unittest
from pyramid import testing

#from .. import _register_routes
#from .. import _register_common_templates

from ..numbers.models import NumbersContextFactory
from ..models.context import PlainContext
#from ..numbers.views import NumberGraphRESTfulView

#IContextFactory
class PlainContextTests(unittest.TestCase):
    def setUp(self):
        req = testing.DummyRequest()
        self.ncf = NumbersContextFactory(req)

    def test_ncf(self):
        self.assertTrue(self.ncf)
        self.failIfEqual(self.ncf, None)
        self.assertEqual(self.ncf.__class__, PlainContext)

    def test_get_collection(self):
        results = self.ncf.get_collection()
        self.failIfEqual(results, None)

    def test_get_member(self):
        self.ncf.get_member("17")
        self.ncf.get_member("32")
        #fails:
        # self.ncf.get_member(17)
        # self.ncf.get_member(-1)

    # NOP
    def test_create_member(self):
        func = lambda : self.ncf.create_member({})
        self.failUnlessRaises(NotImplementedError, func)
        # should fail
    def test_update_member(self):
        func = lambda : self.ncf.update_member(-1, {})
        self.failUnlessRaises(NotImplementedError, func)
        # should fail
    def test_delete_member(self):
        func = lambda : self.ncf.delete_member(-1)
        self.failUnlessRaises(NotImplementedError, func)
        # should fail

    def test_get_member_id_as_string(self):
        self.assertEqual(
            "10",
            self.ncf.get_member_id_as_string({'n': "10"}))

    def test_to_json(self):
        import json # TODO
        value = dict(one='two', two='three')
        jsonstr = self.ncf.to_json(value)
        self.assertTrue(json.loads(jsonstr))

    #def test_get_json_obj(self):
    #    self.ncf.get_json_obj(value, fields, wrap)

    def test_wrap_json_obj(self):
        obj = ['one','two','three']
        outp = dict(results=obj, result_count=len(obj))
        self.assertEqual(self.ncf.wrap_json_obj(obj), outp)

    def test_member_to_dict(self):
        member = ['one','two','three']
        self.assertEqual(
                member,
                self.ncf.member_to_dict(member)
        )
        # TODO
        # self.ncf.member_to_dict(member, fields=['one'])

    def test_default_fields(self):
        expected = ['one']
        fields = self.ncf.default_fields
        self.assertEqual(expected, fields)

