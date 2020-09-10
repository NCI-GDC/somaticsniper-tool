#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from unittest import mock

from somaticsniper_tool import high_confidence as MOD


class ThisTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.mocks = SimpleNamespace(utils=mock.MagicMock(spec_set=MOD.utils),)


class TestHighConfidene(ThisTestCase):
    CLASS_OBJ = MOD.HighConfidence

    def setUp(self):
        super().setUp()

        self.high_confidence = "/path/to/highconfidence.pl"
        self.input_file = "/path/to/vcf.SNPfilter"

    def test_init(self):
        expected = {
            "high_confidence": self.high_confidence,
            "input_file": self.input_file,
        }
        found = self.CLASS_OBJ(self.high_confidence, self.input_file)
        for k, v in expected.items():
            with self.subTest(k=k):
                self.assertEqual(getattr(found, k), v)

    def test_run_builds_command_as_expected(self):
        expected = self.CLASS_OBJ.COMMAND.format(
            high_confidence=self.high_confidence, input_file=self.input_file
        )
        high_confidence = self.CLASS_OBJ(self.high_confidence, self.input_file)
        high_confidence.run(_utils=self.mocks.utils)
        self.mocks.utils.run_subprocess_command.assert_called_once_with(expected)


# __END__
