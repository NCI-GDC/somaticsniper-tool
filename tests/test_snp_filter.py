#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from unittest import mock

from somaticsniper_tool import snp_filter as MOD


class ThisTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.mocks = SimpleNamespace(utils=mock.MagicMock(spec_set=MOD.utils),)


class TestSnpFilter(ThisTestCase):
    CLASS_OBJ = MOD.SnpFilter

    def setUp(self):
        super().setUp()

        self.snpfilter = "/path/to/snpfilter.pl"
        self.snp_file = "/path/to/somaticsniper.vcf"
        self.indel_file = "/path/to/region.mpileup"

    def test_init(self):
        expected = {
            "snpfilter": self.snpfilter,
            "vcf_file": self.snp_file,
            "indel_mpileup_file": self.indel_file,
        }
        found = self.CLASS_OBJ(self.snpfilter, self.snp_file, self.indel_file)
        for k, v in expected.items():
            with self.subTest(k=k):
                self.assertEqual(getattr(found, k), v)

    def test_run_builds_command_as_expected(self):
        expected = self.CLASS_OBJ.COMMAND.format(
            snpfilter=self.snpfilter, vcf_file=self.snp_file, indel_file=self.indel_file
        )
        snpfilter = self.CLASS_OBJ(self.snpfilter, self.snp_file, self.indel_file)
        snpfilter.run(_utils=self.mocks.utils)
        self.mocks.utils.run_subprocess_command.assert_called_once_with(expected)


# __END__
