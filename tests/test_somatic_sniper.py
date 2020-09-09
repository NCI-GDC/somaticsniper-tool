#!/usr/bin/env python3

import unittest
from types import SimpleNamespace

import somaticsniper_tool.somatic_sniper as MOD


class ThisTestCase(unittest.TestCase):
    pass


class Test_SomaticSniper(ThisTestCase):

    CLASS_OBJ = MOD.SomaticSniper

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_setting_class_attributes_from_kwargs(self):

        input_args = {
            "somaticsniper_bin": "foobar",
            'map_q': 12,
            'base_q': 4,
            'pps': 6,
            'theta': 0.1,
            'nhap': 0.45,
            'pd': 7,
            'out_format': "baz",
            'flags': "[]",
            'reference_path': "/path/to/ref",
        }
        for k in input_args.keys():
            with self.subTest(k=k):
                self.assertEqual(getattr(self.CLASS_OBJ, k), None)

        self.CLASS_OBJ._initialize_args(**input_args)

        for k, v in input_args.items():
            with self.subTest(k=k):
                self.assertEqual(getattr(self.CLASS_OBJ, k), v)

    def test_setting_class_attributes_from_namespace(self):
        pass


# __END__
