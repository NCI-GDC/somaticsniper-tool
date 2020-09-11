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
        self.input_args = {
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

    def tearDown(self):
        super().tearDown()
        for k in self.input_args.keys():
            setattr(self.CLASS_OBJ, k, None)

    def test_setting_class_attributes_from_kwargs(self):

        for k in self.input_args.keys():
            with self.subTest(k=k):
                self.assertEqual(getattr(self.CLASS_OBJ, k), None)

        self.CLASS_OBJ._initialize_args(**self.input_args)

        for k, v in self.input_args.items():
            with self.subTest(k=k):
                self.assertEqual(getattr(self.CLASS_OBJ, k), v)

    def test_setting_class_attributes_from_namespace(self):

        input_namespace = SimpleNamespace(**self.input_args)
        for k in self.input_args.keys():
            with self.subTest(k=k):
                self.assertEqual(getattr(self.CLASS_OBJ, k), None)

        self.CLASS_OBJ._initialize_args(args=input_namespace)

        for k, v in self.input_args.items():
            with self.subTest(k=k):
                self.assertEqual(getattr(self.CLASS_OBJ, k), v)

    def test_setting_class_attributes_from_namespace_and_kwarg(self):

        input_namespace = SimpleNamespace(**self.input_args)
        for k in self.input_args.keys():
            with self.subTest(k=k):
                self.assertEqual(getattr(self.CLASS_OBJ, k), None)
        kwarg_input = {'theta': 2.7}

        self.CLASS_OBJ._initialize_args(args=input_namespace, **kwarg_input)

        for k, v in self.input_args.items():
            with self.subTest(k=k):
                if k == 'theta':
                    self.assertEqual(getattr(self.CLASS_OBJ, k), kwarg_input[k])
                else:
                    self.assertEqual(getattr(self.CLASS_OBJ, k), v)


# __END__
