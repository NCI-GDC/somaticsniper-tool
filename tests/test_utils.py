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
        found, base = MOD.get_region_from_name(path)
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
        mock_returncode = 0
        type(mock_popen).returncode = mock.PropertyMock(return_value=mock_returncode)
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
        timeout = 3600
        mock_popen = self._setup_popen(cmd_str)
        MOD.run_subprocess_command(cmd_str, timeout, shell=True, _di=self.mocks)
        self.mocks.subprocess.Popen.assert_called_once_with(expected_cmd, shell=True)

    def test_popen_command_split_on_shell_is_False_or_not_given(self):
        cmd_str = "ls /foo/bar"
        expected_cmd = MOD.shlex.split(cmd_str)
        timeout = 3600
        mock_popen = self._setup_popen(cmd_str)
        MOD.run_subprocess_command(cmd_str, timeout, _di=self.mocks)
        self.mocks.subprocess.Popen.assert_called_once_with(expected_cmd)

    def test_popen_killed_on_timeout_expired(self):
        expected_communicate_calls = (
            mock.call(timeout=3600),
            mock.call(),
        )
        cmd_str = "ls /foo/bar"
        mock_popen = self._setup_popen(cmd_str, do_raise=True)
        timeout = 3600
        with self.assertRaises(ValueError):
            MOD.run_subprocess_command(cmd_str, timeout, _di=self.mocks)
        mock_popen.communicate.assert_has_calls(expected_communicate_calls)
        mock_popen.kill.assert_called_once_with()

    def test_popen_returns_decoded_stdout_stderr(self):
        cmd_str = "ls /foo/bar"
        stdout = b"stdout"
        stderr = b"stderr"
        timeout = 3600
        mock_popen = self._setup_popen(cmd_str, stdout=stdout, stderr=stderr)
        found = MOD.run_subprocess_command(cmd_str, timeout, _di=self.mocks)

        self.assertEqual(found.stdout, stdout.decode())
        self.assertEqual(found.stderr, stderr.decode())

    def test_returns_None_when_communicate_returns_None(self):
        cmd_str = "ls /foo/bar"
        expected = MOD.PopenReturn(stdout=None, stderr=None)
        mock_popen = mock.MagicMock(spec_set=MOD.subprocess.Popen)
        mock_returncode = 0
        type(mock_popen).returncode = mock.PropertyMock(return_value=mock_returncode)
        mock_popen.communicate.return_value = (None, None)
        timeout = 3600
        self.mocks.subprocess.Popen.return_value = mock_popen
        found = MOD.run_subprocess_command(cmd_str, timeout, _di=self.mocks)
        self.assertEqual(expected, found)

    def test_returns_str_when_communicate_returns_str(self):
        cmd_str = "ls /foo/bar"
        expected = MOD.PopenReturn(stdout="foo", stderr="bar")
        mock_popen = mock.MagicMock(spec_set=MOD.subprocess.Popen)
        mock_returncode = 0
        type(mock_popen).returncode = mock.PropertyMock(return_value=mock_returncode)
        mock_popen.communicate.return_value = ("foo", "bar")
        timeout = 3600
        self.mocks.subprocess.Popen.return_value = mock_popen
        found = MOD.run_subprocess_command(cmd_str, timeout, _di=self.mocks)
        self.assertEqual(expected, found)


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
