# -*- coding: utf-8 -*-
"""Tests for the JSON-L parser plugin for Microsoft 365 audit log files."""

import unittest

from plaso.parsers.jsonl_plugins import microsoft365_audit_log

from tests.parsers.jsonl_plugins import test_lib


class Microsoft365AuditLogJSONLPluginTest(test_lib.JSONLPluginTestCase):
  """Tests for the JSON-L parser plugin for Microsoft 365 audit log files."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = microsoft365_audit_log.Microsoft365AuditLogJSONLPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin(
        ['microsoft_audit_log.jsonl'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'audit_record_identifier': 'c9d2d808-0efe-48cb-eaec-08da3028eb80',
        'operation_name': 'Install-DefaultSharingPolicy',
        'organization_identifier': '5a0f38c6-710b-4503-92c0-3a9f6e00f726',
        'record_type': 1,
        'recorded_time': '2022-05-07T12:55:53+00:00',
        'result_status': 'True',
        'user_key': 'NT AUTHORITY\\SYSTEM (Microsoft.Exchange.Servicehost)',
        'user_type': 3,
        'workload': 'Exchange',
        'object_identifier': (
            'sst5f.onmicrosoft.com\\952cae95-808b-4aa7-b783-a9151be9a05a'),
        'user_identifier': (
            'NT AUTHORITY\\SYSTEM (Microsoft.Exchange.Servicehost)')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
