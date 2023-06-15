#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple IPS file parser plugin for recovery logd report."""

import unittest

from plaso.parsers.ips_plugins import recovery_logd

from tests.parsers.ips_plugins import test_lib


class AppleRecoveryLogdIPSPluginTest(test_lib.IPSPluginTestCase):
  """Tests for the Apple IPS file parser plugin for recovery logd report."""

  def testProcess(self):
    """Tests for the Process function."""
    plugin = recovery_logd.AppleRecoveryLogdIPSPlugin()
    storage_writer = self._ParseIPSFileWithPlugin(
        ['ips_files', 'recoverylogd-2023-06-08-144913.ips'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
      'event_data')
    self.assertEqual(number_of_event_data, 1)

    expected_event_values = {
        'application_name': 'recoverylogd',
        'application_version': '',
        'bug_type': '309',
        'device_model': 'iBridge2,14',
        'exception_type': 'EXC_CRASH',
        'event_time': '2023-06-08T14:49:13.520+00:00',
        'incident_identifier': '9505C5CC-07DE-4E81-BCCE-60D07C96D1B1',
        'os_version': 'Bridge OS 7.5 (20P5058)',
        'parent_process': 'launchd',
        'parent_process_identifier': 1,
        'process_identifier': 74,
        'process_launch_time': '2023-06-08T14:49:12.507+00:00',
        'user_identifier': 501}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
