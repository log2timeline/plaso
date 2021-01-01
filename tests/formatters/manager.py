#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event formatters manager."""

import unittest

from plaso.formatters import manager
from plaso.lib import definitions

from tests import test_lib as shared_test_lib


class FormattersManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the event formatters manager."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'filename': 'c:/Users/joesmith/NTUSER.DAT',
       'hostname': 'MYHOSTNAME',
       'random': 'random',
       'text': '',
       'timestamp': 0,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'username': 'joesmith'},
      {'data_type': 'windows:registry:key_value',
       'hostname': 'MYHOSTNAME',
       'key_path': 'MY AutoRun key',
       'timestamp': '2012-04-20 22:38:46.929596',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: c:/Temp/evil.exe'},
      {'data_type': 'windows:registry:key_value',
       'hostname': 'MYHOSTNAME',
       'key_path': 'HKEY_CURRENT_USER\\Secret\\EvilEmpire\\Malicious_key',
       'timestamp': '2012-04-20 23:56:46.929596',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: send all the exes to the other world'},
      {'data_type': 'windows:registry:key_value',
       'hostname': 'MYHOSTNAME',
       'key_path': 'HKEY_CURRENT_USER\\Windows\\Normal',
       'timestamp': '2012-04-20 16:44:46',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: run all the benign stuff'},
      {'data_type': 'test:event',
       'filename': 'c:/Temp/evil.exe',
       'hostname': 'MYHOSTNAME',
       'text': 'This log line reads ohh so much.',
       'timestamp': '2012-04-30 10:29:47.929596',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'filename': 'c:/Temp/evil.exe',
       'hostname': 'MYHOSTNAME',
       'text': 'Nothing of interest here, move on.',
       'timestamp': '2012-04-30 10:29:47.929596',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'filename': 'c:/Temp/evil.exe',
       'hostname': 'MYHOSTNAME',
       'text': 'Mr. Evil just logged into the machine and got root.',
       'timestamp': '2012-04-30 13:06:47.939596',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'filename': 'c:/Temp/evil.exe',
       'hostname': 'nomachine',
       'offset': 12,
       'text': (
           'This is a line by someone not reading the log line properly. And '
           'since this log line exceeds the accepted 80 chars it will be '
           'shortened.'),
       'timestamp': '2012-06-05 22:14:19.000000',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'username': 'johndoe'}]

  def testReadFormattersFile(self):
    """Tests the _ReadFormattersFile function."""
    test_file_path = self._GetTestFilePath(['formatters', 'format_test.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    manager.FormattersManager._formatters = {}
    manager.FormattersManager._ReadFormattersFile(test_file_path)
    self.assertEqual(len(manager.FormattersManager._formatters), 2)

    manager.FormattersManager._formatters = {}

  def testReadFormattersFromDirectory(self):
    """Tests the ReadFormattersFromDirectory function."""
    test_directory_path = self._GetTestFilePath(['formatters'])
    self._SkipIfPathNotExists(test_directory_path)

    manager.FormattersManager._formatters = {}
    manager.FormattersManager.ReadFormattersFromDirectory(test_directory_path)
    self.assertEqual(len(manager.FormattersManager._formatters), 2)

    manager.FormattersManager._formatters = {}

  def testReadFormattersFromFile(self):
    """Tests the ReadFormattersFromFile function."""
    test_file_path = self._GetTestFilePath(['formatters', 'format_test.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    manager.FormattersManager._formatters = {}
    manager.FormattersManager.ReadFormattersFromFile(test_file_path)
    self.assertEqual(len(manager.FormattersManager._formatters), 2)

    manager.FormattersManager._formatters = {}


if __name__ == '__main__':
  unittest.main()
