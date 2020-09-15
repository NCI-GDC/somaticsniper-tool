#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from unittest import mock

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


class Test_run_subprocess_command(ThisTestCase):
    def setUp(self):
        super().setUp()
        self.mocks = SimpleNamespace(subprocess=mock.MagicMock(spec_set=MOD.subprocess))

    def tearDown(self):
        super().tearDown()

    def _setup_popen(self, cmd, stdout=None, stderr=None, do_raise=False):
        stdout = stdout or b""
        stderr = stderr or b""

        mock_popen = mock.MagicMock(spec_set=MOD.subprocess.Popen)
        self.mocks.subprocess.Popen.return_value = mock_popen
        if do_raise:
            mock_popen.communicate.side_effect = [
                MOD.subprocess.TimeoutExpired(cmd, 3600),
                (stdout, stderr),
            ]
        else:
            mock_popen.communicate.return_value = (stdout, stderr)
        return mock_popen

    def test_popen_command_not_split_on_shell_is_True(self):
        cmd_str = "ls /foo/bar"
        expected_cmd = cmd_str
        mock_popen = self._setup_popen(cmd_str)
        MOD.run_subprocess_command(cmd_str, shell=True, _di=self.mocks)
        self.mocks.subprocess.Popen.assert_called_once_with(expected_cmd, shell=True)

    def test_popen_command_split_on_shell_is_False_or_not_given(self):
        cmd_str = "ls /foo/bar"
        expected_cmd = MOD.shlex.split(cmd_str)
        mock_popen = self._setup_popen(cmd_str)
        MOD.run_subprocess_command(cmd_str, _di=self.mocks)
        self.mocks.subprocess.Popen.assert_called_once_with(expected_cmd)

    def test_popen_killed_on_timeout_expired(self):
        expected_communicate_calls = (
            mock.call(timeout=3600),
            mock.call(),
        )
        cmd_str = "ls /foo/bar"
        mock_popen = self._setup_popen(cmd_str, do_raise=True)
        MOD.run_subprocess_command(cmd_str, _di=self.mocks)
        mock_popen.communicate.assert_has_calls(expected_communicate_calls)
        mock_popen.kill.assert_called_once_with()

    def test_popen_returns_decoded_stdout_stderr(self):
        cmd_str = "ls /foo/bar"
        stdout = b"stdout"
        stderr = b"stderr"
        mock_popen = self._setup_popen(cmd_str, stdout=stdout, stderr=stderr)
        found = MOD.run_subprocess_command(cmd_str, _di=self.mocks)

        self.assertEqual(found.stdout, stdout.decode())
        self.assertEqual(found.stderr, stderr.decode())


class Test_merge_outputs(ThisTestCase):
    def setUp(self):
        super().setUp()
        self.mocks = SimpleNamespace(open=mock.MagicMock(spec_set=open))

    def test_open_called_on_input_files(self):
        input_files = ['foo', 'bar', 'baz']

        MOD.merge_outputs(input_files, mock.Mock(), _di=self.mocks)
        for f in input_files:
            with self.subTest(f=f):
                self.mocks.open.assert_any_call(f)


# __END__
