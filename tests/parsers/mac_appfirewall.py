#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Mac AppFirewall log file parser."""

import unittest

from plaso.formatters import mac_appfirewall  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import mac_appfirewall

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MacAppFirewallUnitTest(test_lib.ParserTestCase):
  """Tests for Mac AppFirewall log file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'appfirewall.log'])
  def testParseFile(self):
    """Test parsing of a Mac Wifi log file."""
    parser = mac_appfirewall.MacAppFirewallParser()
    knowledge_base_values = {u'year': 2013}
    storage_writer = self._ParseFile(
        [u'appfirewall.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 47)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-02 04:07:35')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.agent, u'socketfilterfw[112]')
    self.assertEqual(event.computer_name, u'DarkTemplar-2.local')
    self.assertEqual(event.status, u'Error')
    self.assertEqual(event.process_name, u'Logging')
    self.assertEqual(event.action, u'creating /var/log/appfirewall.log')

    expected_message = (
        u'Computer: DarkTemplar-2.local '
        u'Agent: socketfilterfw[112] '
        u'Status: Error '
        u'Process name: Logging '
        u'Log: creating /var/log/appfirewall.log')
    expected_short_message = (
        u'Process name: Logging '
        u'Status: Error')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[9]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-03 13:25:15')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.agent, u'socketfilterfw[87]')
    self.assertEqual(event.computer_name, u'DarkTemplar-2.local')
    self.assertEqual(event.status, u'Info')
    self.assertEqual(event.process_name, u'Dropbox')
    self.assertEqual(event.action, u'Allow TCP LISTEN  (in:0 out:1)')

    expected_message = (
        u'Computer: DarkTemplar-2.local '
        u'Agent: socketfilterfw[87] '
        u'Status: Info '
        u'Process name: Dropbox '
        u'Log: Allow TCP LISTEN  (in:0 out:1)')
    expected_short_message = (
        u'Process name: Dropbox '
        u'Status: Info')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Check repeated lines.
    event = events[38]
    repeated_event = events[39]
    self.assertEqual(event.agent, repeated_event.agent)
    self.assertEqual(
        event.computer_name, repeated_event.computer_name)
    self.assertEqual(event.status, repeated_event.status)
    self.assertEqual(
        event.process_name, repeated_event.process_name)
    self.assertEqual(event.action, repeated_event.action)

    # Year changes.
    event = events[45]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-31 23:59:23')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[46]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-01 01:13:23')
    self.assertEqual(event.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
