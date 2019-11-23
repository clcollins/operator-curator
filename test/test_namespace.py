import unittest
import json
import yaml

from operatorcurator import namespace

class TestNamespaces(unittest.TestCase):
    def test_init(self):
        """
        Tests initialization of a namespace object.
        """
        # TODO: need to mock requests
        #
        # This is how you would do it live

        # ns = namespace.Namespace('redhat-operators')

        # self.assertEqual(ns.name, 'redhat-operators')

        # Not the best test - could be improved when mocking
        # requests, because there would be a known quantity of data
        # self.assertGreater(len(ns.operators), 0)
        pass


    def test_list_operators(self):
        # TODO: need to mock requests
        #
        # This is how you would do it live

        # ns = namespace.Namespace('redhat-operators')
        # operators = ns.operators

        # Not the best test - could be improved when mocking
        # requests, because there would be a known quantity of data
        # self.assertGreater(len(operators), 0)
        pass