#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Mac AppFirewall log file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_appfirewall as _  # pylint: disable=unused-import
from plaso.parsers import mac_appfirewall

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MacAppFirewallUnitTest(test_lib.ParserTestCase):
  """Tests for Mac AppFirewall log file parser."""

  @shared_test_lib.skipUnlessHasTestFile(['appfirewall.log'])
  def testParseFile(self):
    """Test parsing of a Mac Wifi log file."""
    parser = mac_appfirewall.MacAppFirewallParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['appfirewall.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 47)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-11-02 04:07:35.000000')

    self.assertEqual(event.agent, 'socketfilterfw[112]')
    self.assertEqual(event.computer_name, 'DarkTemplar-2.local')
    self.assertEqual(event.status, 'Error')
    self.assertEqual(event.process_name, 'Logging')
    self.assertEqual(event.action, 'creating /var/log/appfirewall.log')

    expected_message = (
        'Computer: DarkTemplar-2.local '
        'Agent: socketfilterfw[112] '
        'Status: Error '
        'Process name: Logging '
        'Log: creating /var/log/appfirewall.log')
    expected_short_message = (
        'Process name: Logging '
        'Status: Error')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[9]

    self.CheckTimestamp(event.timestamp, '2013-11-03 13:25:15.000000')

    self.assertEqual(event.agent, 'socketfilterfw[87]')
    self.assertEqual(event.computer_name, 'DarkTemplar-2.local')
    self.assertEqual(event.status, 'Info')
    self.assertEqual(event.process_name, 'Dropbox')
    self.assertEqual(event.action, 'Allow TCP LISTEN  (in:0 out:1)')

    expected_message = (
        'Computer: DarkTemplar-2.local '
        'Agent: socketfilterfw[87] '
        'Status: Info '
        'Process name: Dropbox '
        'Log: Allow TCP LISTEN  (in:0 out:1)')
    expected_short_message = (
        'Process name: Dropbox '
        'Status: Info')

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

    self.CheckTimestamp(event.timestamp, '2013-12-31 23:59:23.000000')

    event = events[46]

    self.CheckTimestamp(event.timestamp, '2014-01-01 01:13:23.000000')


if __name__ == '__main__':
  unittest.main()
