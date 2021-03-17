#!/usr/bin/env python3

import csv
import unittest
from types import SimpleNamespace
from unittest import mock

from somaticsniper_tool import annotate as MOD


class ThisTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.mocks = SimpleNamespace(
            csv=mock.MagicMock(spec_set=csv), open=mock.mock_open()
        )


class Test_Annotate(ThisTestCase):
    CLASS_OBJ = MOD.Annotate

    def setUp(self):
        super().setUp()

    def test_init_sets_attributes_as_expected(self):
        outfile = "/path/to/output.annotated.vcf"
        expected = {
            "output_file": outfile,
        }
        obj = self.CLASS_OBJ(outfile)
        for k, v in expected.items():
            with self.subTest(k=k):
                self.assertEqual(getattr(obj, k), v)

    def test_enter_opens_output_file_as_expected(self):
        outfile = "/path/to/output.annotated.vcf"
        with self.CLASS_OBJ(outfile, _di=self.mocks):
            pass

        self.mocks.open.assert_called_once_with(outfile, 'w')
        self.mocks.open.return_value.close.assert_called_once_with()


# __END__
