# -*- coding: utf-8 -*-
"""Tests for the JSON-L parser plugin for Microsoft audit log files."""

import unittest

from plaso.parsers.jsonl_plugins import microsoft_audit_log

from tests.parsers.jsonl_plugins import test_lib


class MicrosoftAuditLogJSONLPluginTest(test_lib.JSONLPluginTestCase):
  """Tests for the JSON-L parser plugin for Microsoft 365 audit log files."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = microsoft_audit_log.MicrosoftAuditLogJSONLPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin(
        ['microsoft_audit_log.jsonl'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'audit_record_identifier': 'c9d2d808-0efe-48cb-eaec-08da3028eb80',
        'operation_name': 'Install-DefaultSharingPolicy',
        'organization_identifier': '5a0f38c6-710b-4503-92c0-3a9f6e00f726',
        'record_type': 1,
        'result_status': 'True',
        'user_key': 'NT AUTHORITY\\SYSTEM (Microsoft.Exchange.Servicehost)',
        'user_type': 3,
        'workload': 'Exchange',
        'object_identifier':
            'sst5f.onmicrosoft.com\\952cae95-808b-4aa7-b783-a9151be9a05a',
        'user_identifier':
            'NT AUTHORITY\\SYSTEM (Microsoft.Exchange.Servicehost)',
        'timestamp': '2022-05-07 12:55:53.000000'}
    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'audit_record_identifier': 'cd710ce3-52fa-4c70-aec8-08da3028fa73',
        'operation_name': 'Set-MailboxPlan',
        'organization_identifier': '5a0f38c6-710b-4503-92c0-3a9f6e00f726',
        'record_type': 1,
        'result_status': 'True',
        'user_key': 'NT AUTHORITY\\SYSTEM (Microsoft.Exchange.Servicehost)',
        'user_type': 3,
        'workload': 'Exchange',
        'user_identifier':
            'NT AUTHORITY\\SYSTEM (Microsoft.Exchange.Servicehost)',
        'timestamp': '2022-05-07 12:56:18.000000'}
    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'audit_record_identifier': 'cc0bb5b2-b540-4640-5e1c-08da3028fe4f',
        'operation_name': 'Set-AdminAuditLogConfig',
        'organization_identifier': '5a0f38c6-710b-4503-92c0-3a9f6e00f726',
        'record_type': 1,
        'result_status': 'True',
        'user_key': 'NT AUTHORITY\\SYSTEM (Microsoft.Exchange.Servicehost)',
        'user_type': 3,
        'workload': 'Exchange',
        'user_identifier':
            'NT AUTHORITY\\SYSTEM (Microsoft.Exchange.Servicehost)',
        'timestamp':'2022-05-07 12:56:24.000000'}
    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
    'audit_record_identifier': '0a454a7b-fbac-4329-a20c-72bad3bc5000',
    'operation_name': 'UserLoggedIn',
    'organization_identifier': '5a0f38c6-710b-4503-92c0-3a9f6e00f726',
    'record_type': 15,
    'result_status': 'Success',
    'user_key': '55425677-a6b7-4df1-8068-709eb4162d42',
    'user_type': 0,
    'workload': 'AzureActiveDirectory',
    'client_ip': '0.0.0.0',
    'object_identifier': '00000003-0000-0000-c000-000000000000',
    'user_identifier': 'piet@sst5f.onmicrosoft.com',
    'timestamp': '2022-05-08 15:13:41.000000'}
    self.CheckEventValues(storage_writer, events[3], expected_event_values)


if __name__ == '__main__':
  unittest.main()
    