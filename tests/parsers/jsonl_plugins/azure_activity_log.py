# -*- coding: utf-8 -*
"""Tests for the JSON-L parser plugin for Azure activity log files."""

import unittest

from plaso.parsers.jsonl_plugins import azure_activity_log

from tests.parsers.jsonl_plugins import test_lib


class AzureActivityLogJSONLPluginTest(test_lib.JSONLPluginTestCase):
  """Tests for the JSON-L parser plugin for Azure activity log files."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = azure_activity_log.AzureActivityLogJSONLPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin(
        ['azure_activity_log.jsonl'], plugin)

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
        'caller': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'client_ip': '1.2.3.4',
        'correlation_identifier': 'c0c54eb6-3a17-42e2-b6f6-37484ac276c4',
        'event_data_identifier': '587eda65-125e-48c2-9b04-ab5e8d3a1d8e',
        'event_name': 'BeginRequest',
        'level': 'Informational',
        'operation_identifier': '80287633-d288-49d7-b25e-7ba8cf6bf1da',
        'operation_name': 'Microsoft.Compute/disks/delete',
        'recorded_time': '2022-02-09T03:04:54.297853+00:00',
        'resource_group': 'TEST-RESOURCE-GROUP',
        'resource_identifier': (
            '/subscriptions/12345678-9abc-defg-hijk-lmnopqrstuvw/'
            'resourceGroups/TEST-RESOURCE-GROUP/providers/Microsoft.Compute'
            '/disks/test-vm_disk1_cd8883de78cb4cda97cb858dfe0cda3a'),
        'resource_provider': 'Microsoft.Compute',
        'resource_type': 'Microsoft.Compute/disks',
        'subscription_identifier': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'tenant_identifier': '12345678-9abc-defg-hijk-lmnopqrstuvw'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
