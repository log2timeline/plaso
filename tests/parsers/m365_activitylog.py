#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the M365 Activity log parser."""

import unittest

from plaso.parsers import m365_activitylog

from tests.parsers import test_lib


class M365ActivityLogTest(test_lib.ParserTestCase):
  """Tests for the M365 Activity log table parser."""

  # pylint: disable=protected-access

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    parser =  m365_activitylog.M365ActivityLogParser()
    storage_writer = self._ParseFile(
        ['m365_activity_log_002.csv'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 15)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'application': 'Microsoft OneDrive for Business',
        'data_type': 'm365:activitylog:event',
        'ip_address': '82.181.16.164',
        'user_principal_name': 'test-user@test-company.tld'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
