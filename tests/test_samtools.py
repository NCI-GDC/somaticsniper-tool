#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from unittest import mock

from somaticsniper_tool import samtools as MOD


class ThisTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.mocks = SimpleNamespace(
            tempfile=mock.MagicMock(spec_set=MOD.tempfile),
            utils=mock.MagicMock(spec_set=MOD.utils),
        )


class Test_SamtoolsView(ThisTestCase):
    CLASS_OBJ = MOD.SamtoolsView

    def setUp(self):
        super().setUp()
        self.timeout = 3600
        self.samtools = "samtools"
        self.bam_file = "/path/to/file.bam"
        self.region = "chr1:1-20"

        self.temp_file_name = "foobar"
        self.temp_file_mock = mock.Mock()
        self.temp_file_mock.name = self.temp_file_name
        self.mocks.tempfile.NamedTemporaryFile.return_value = self.temp_file_mock

    def test_tempfile_opened_on_init(self):
        found = self.CLASS_OBJ(
            self.timeout,
            self.samtools,
            self.bam_file,
            self.region,
            _utils=self.mocks.utils,
            _di=self.mocks,
        )

        self.assertEqual(found.temp_view_name, self.temp_file_name)
        self.assertEqual(found.temp_view_fh, self.temp_file_mock)

    def test_tempfile_name_returned_on_enter(self):

        with self.CLASS_OBJ(
            self.timeout,
            self.samtools,
            self.bam_file,
            self.region,
            _utils=self.mocks.utils,
            _di=self.mocks,
        ) as found:
            self.assertEqual(found, self.temp_file_name)

        self.temp_file_mock.close.assert_called_once_with()

    def test_samtools_command_called_on_enter(self):
        expected_cmd_str = self.CLASS_OBJ.COMMAND_STR.format(
            samtools=self.samtools, bam_path=self.bam_file, region=self.region
        )

        with self.CLASS_OBJ(
            self.timeout,
            self.samtools,
            self.bam_file,
            self.region,
            _utils=self.mocks.utils,
            _di=self.mocks,
        ):
            self.mocks.utils.run_subprocess_command.assert_called_once_with(
                expected_cmd_str, self.timeout, stdout=self.temp_file_mock
            )


# __END__
