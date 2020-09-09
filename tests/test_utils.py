#!/usr/bin/env python3

import unittest

from somaticsniper_tool import utils as MOD


class ThisTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()


class Test__get_region_from_name(ThisTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_method_returns_expected(self):
        path = "/foo/bar/chr1-1-12345.mpileup"
        expected = "chr1:1-12345"
        found = MOD.get_region_from_name(path)
        self.assertEqual(found, expected)


# __END__
