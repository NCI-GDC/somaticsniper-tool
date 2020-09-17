#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from unittest import mock

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
            'flags': ["foo", "bar"],
            'reference_path': "/path/to/ref",
        }
        self.mocks = SimpleNamespace(UTILS=mock.MagicMock(spec_set=MOD.utils))

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

    def test_init_sets_attributes(self):
        output = "output"
        expected = "{}.vcf".format(output)
        obj = self.CLASS_OBJ(output)
        self.assertEqual(expected, obj.output_file)

    def test_run_builds_command_as_expected(self):
        self.CLASS_OBJ._initialize_args(**self.input_args)
        output = "output"
        obj = self.CLASS_OBJ(output)
        args = self.input_args.copy()
        args['extra_args'] = ",".join(args.pop('flags'))
        normal_bam = "normal.bam"
        tumor_bam = "tumor.bam"
        expected_cmd = self.CLASS_OBJ.COMMAND.format(
            normal_bam=normal_bam,
            tumor_bam=tumor_bam,
            output_file="{}.vcf".format(output),
            **args,
        )
        subprocess_return = MOD.utils.PopenReturn(stdout='foo', stderr='bar')
        self.mocks.UTILS.run_subprocess_command.return_value = subprocess_return
        output_file = obj.run(normal_bam, tumor_bam, _utils=self.mocks.UTILS)
        self.mocks.UTILS.run_subprocess_command.assert_called_once_with(
            expected_cmd, stdout=MOD.subprocess.PIPE, stderr=MOD.subprocess.PIPE
        )


# __END__
