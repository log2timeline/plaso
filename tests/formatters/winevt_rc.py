#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Event Log resources database reader."""

import unittest

from plaso.formatters import winevt_rc

from tests import test_lib as shared_test_lib


class WinevtResourcesSqlite3DatabaseReaderTest(shared_test_lib.BaseTestCase):
  """Tests for the Event Log resources sqlite3 database reader."""

  @shared_test_lib.skipUnlessHasTestFile([u'winevt-rc.db'])
  def testGetMessage(self):
    """Tests the GetMessage function."""
    database_path = self._GetTestFilePath([u'winevt-rc.db'])
    database_reader = winevt_rc.WinevtResourcesSqlite3DatabaseReader()

    database_reader.Open(database_path)

    expected_message_string = (
        u'Your computer has detected that the IP address {0:s} for the Network '
        u'Card with network address {2:s} is already in use on the network. '
        u'Your computer will automatically attempt to obtain a different '
        u'address.')

    message_string = database_reader.GetMessage(
        u'Microsoft-Windows-Dhcp-Client', 0x00000409, 0xb00003ed)
    self.assertEqual(message_string, expected_message_string)

    database_reader.Close()


if __name__ == '__main__':
  unittest.main()
