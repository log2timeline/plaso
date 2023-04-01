#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Event Log resources database reader."""

import unittest

from plaso.output import winevt_rc

from tests import test_lib as shared_test_lib


class WinevtResourcesSqlite3DatabaseReaderTest(shared_test_lib.BaseTestCase):
  """Windows EventLog resources SQLite database reader."""

  def testGetMessage(self):
    """Tests the GetMessage function."""
    database_path = self._GetTestFilePath(['winevt-rc.db'])
    self._SkipIfPathNotExists(database_path)

    database_reader = winevt_rc.WinevtResourcesSqlite3DatabaseReader()

    database_reader.Open(database_path)

    expected_message_string = (
        'Your computer has detected that the IP address {0:s} for the Network '
        'Card with network address {2:s} is already in use on the network. '
        'Your computer will automatically attempt to obtain a different '
        'address.')

    message_string = database_reader.GetMessage(
        'Microsoft-Windows-Dhcp-Client', 0x00000409, 0xb00003ed)
    self.assertEqual(message_string, expected_message_string)

    database_reader.Close()


class WinevtResourcesHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows EventLog resources helper."""

  # pylint: disable=protected-access

  def testGetWinevtRcDatabaseMessageString(self):
    """Tests the _GetWinevtRcDatabaseMessageString function."""
    database_path = self._GetTestFilePath(['winevt-rc.db'])
    self._SkipIfPathNotExists(database_path)

    test_helper = winevt_rc.WinevtResourcesHelper(
        None, shared_test_lib.TEST_DATA_PATH, 0x00000409)

    expected_message_string = (
        'Your computer has detected that the IP address {0:s} for the Network '
        'Card with network address {2:s} is already in use on the network. '
        'Your computer will automatically attempt to obtain a different '
        'address.')

    message_string = test_helper._GetWinevtRcDatabaseMessageString(
        'Microsoft-Windows-Dhcp-Client', 0xb00003ed)
    self.assertEqual(message_string, expected_message_string)

  def testGetMessageString(self):
    """Tests the GetMessageString function."""
    database_path = self._GetTestFilePath(['winevt-rc.db'])
    self._SkipIfPathNotExists(database_path)

    test_helper = winevt_rc.WinevtResourcesHelper(
        None, shared_test_lib.TEST_DATA_PATH, 0x00000409)

    expected_message_string = (
        'Your computer has detected that the IP address {0:s} for the Network '
        'Card with network address {2:s} is already in use on the network. '
        'Your computer will automatically attempt to obtain a different '
        'address.')

    message_string = test_helper.GetMessageString(
        '{15a7a4f8-0072-4eab-abad-f98a4d666aed}',
        'Microsoft-Windows-Dhcp-Client', 0xb00003ed, None)
    self.assertEqual(message_string, expected_message_string)


if __name__ == '__main__':
  unittest.main()
