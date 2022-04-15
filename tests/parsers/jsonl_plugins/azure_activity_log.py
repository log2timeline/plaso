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
        'caller': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'client_ip': '1.2.3.4',
        'correlation_identifier': 'c0c54eb6-3a17-42e2-b6f6-37484ac276c4',
        'event_data_identifier': '587eda65-125e-48c2-9b04-ab5e8d3a1d8e',
        'event_name': 'BeginRequest',
        'level': 'Informational',
        'operation_identifier': '80287633-d288-49d7-b25e-7ba8cf6bf1da',
        'operation_name': 'Microsoft.Compute/disks/delete',
        'resource_group': 'TEST-RESOURCE-GROUP',
        'resource_identifier': (
            '/subscriptions/12345678-9abc-defg-hijk-lmnopqrstuvw/'
            'resourceGroups/TEST-RESOURCE-GROUP/providers/Microsoft.Compute'
            '/disks/test-vm_disk1_cd8883de78cb4cda97cb858dfe0cda3a'),
        'resource_provider': 'Microsoft.Compute',
        'resource_type': 'Microsoft.Compute/disks',
        'subscription_identifier': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'tenant_identifier': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'timestamp': '2022-02-09 03:04:54.297853' }
    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'caller': 'fakeemail@fakedomain.com',
        'client_ip': '1.2.3.4',
        'correlation_identifier': 'c0c54eb6-3a17-42e2-b6f6-37484ac276c4',
        'event_data_identifier': '648230f9-fba4-4def-8a83-118b158b748a',
        'event_name': 'BeginRequest',
        'level': 'Informational',
        'operation_identifier': 'fed1601f-d659-48af-8df7-59ca477866c2',
        'operation_name': 'Microsoft.Compute/virtualMachines/delete',
        'resource_group': 'test-resource-group',
        'resource_identifier': (
             '/subscriptions/12345678-9abc-defg-hijk-lmnopqrstuvw/'
             'resourceGroups/test-resource-group/providers/Microsoft.Compute/'
             'virtualMachines/test-vm'),
        'resource_provider': 'Microsoft.Compute',
        'resource_type': 'Microsoft.Compute/virtualMachines',
        'subscription_identifier': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'tenant_identifier': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'timestamp': '2022-02-09 03:04:26.492650'}
    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'caller': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'client_ip': '1.2.3.4',
        'correlation_identifier': '3a5fe8ed-a996-4b9b-863b-237520d07dc2',
        'event_data_identifier': 'b7c5ffc4-db38-48eb-8a66-ff67bbf05f93',
        'event_name': 'BeginRequest',
        'level': 'Informational',
        'operation_identifier': 'c26e6db5-6d08-42e8-b7d7-0d0c135b48ef',
        'operation_name': 'Microsoft.Compute/disks/write',
        'resource_group': 'TEST-RESOURCE-GROUP',
        'resource_identifier': (
            '/subscriptions/12345678-9abc-defg-hijk-lmnopqrstuvw/'
            'resourceGroups/TEST-RESOURCE-GROUP/providers/Microsoft.Compute/'
            'disks/test-vm_disk1_cd8883de78cb4cda97cb858dfe0cda3a'),
        'resource_provider': 'Microsoft.Compute',
        'resource_type': 'Microsoft.Compute/disks',
        'subscription_identifier': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'tenant_identifier': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'timestamp': '2022-02-09 03:00:39.333461' }
    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'caller': 'fakeemail@fakedomain.com',
        'client_ip': '1.2.3.4',
        'correlation_identifier': '3a5fe8ed-a996-4b9b-863b-237520d07dc2',
        'event_data_identifier': 'bd04315c-9658-451e-943f-27ed6fc345a4',
        'event_name': 'BeginRequest',
        'level': 'Informational',
        'operation_identifier': '93e52404-5229-437b-ad61-48af3c3281eb',
        'operation_name': 'Microsoft.Compute/virtualMachines/write',
        'resource_group': 'test-resource-group',
        'resource_identifier': (
            '/subscriptions/12345678-9abc-defg-hijk-lmnopqrstuvw/'
            'resourcegroups/test-resource-group/providers/Microsoft.Compute/'
            'virtualMachines/test-vm'),
        'resource_provider': 'Microsoft.Compute',
        'resource_type': 'Microsoft.Compute/virtualMachines',
        'subscription_identifier': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'tenant_identifier': '12345678-9abc-defg-hijk-lmnopqrstuvw',
        'timestamp': '2022-02-09 03:00:37.136728'}
    self.CheckEventValues(storage_writer, events[3], expected_event_values)


if __name__ == '__main__':
  unittest.main()
