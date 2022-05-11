#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the bencode parser plugin for Transmission BitTorrent files."""

import unittest

from plaso.parsers import ips_parser

from tests.parsers.ips_plugins import test_lib


class AppleCrashLogPluginTest(test_lib.IPSPluginTestCase):
  """Tests for ips log parser plugin for Apple Crash Log files."""

  def testProcess(self):
    """Tests the Process function."""
    parser = ips_parser.IPSParser()
    storage_writer = self._ParseFile(
        ['ips', 'application_crash_log.ips'], parser)

    # This was the first real test that failed.
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'application_name': 'AmongUs',
        'application_version': '2021.11.10',
        'bug_type': '309',
        'bundle_identifier': 'com.innersloth.amongus',
        'device_model': 'iPad5,1',
        'incident_identifier': 'D4E7538A-63F2-4116-8673-D9C0D9EE5A07',
        'os_version': 'iPhone OS 15.1 (19B74)',
        'parent_process': 'launchd',
        'parent_process_identifier': 1,
        'process_identifier': 3723,
        'process_launch': '2021-12-08 12:23:28.2790 -0500',
        'process_path': (
            '/private/var/containers/Bundle/Application/'
            '6C9C5A92-BC0D-476F-BCEF-8D4E0D5CAA40/AmongUs.app/AmongUs'),
        'user_identifier': 501}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
