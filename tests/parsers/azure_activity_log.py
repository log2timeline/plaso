# -*- coding: utf-8 -*
"""Tests for the Azure Activity logging parser."""

import unittest

from plaso.parsers import azure_activity_log
from tests.parsers import test_lib


class AzureActivityLogTest(test_lib.ParserTestCase):
  """Tests for the Azure Activity logging parser."""

  def testParseAzureActivityLog(self):
    """Tests that Azure Activity logs are correctly parsed."""

    expected_timestamps = [
      '2022-02-09 03:04:54.297853',
      '2022-02-09 03:04:26.492650',
      '2022-02-09 03:00:39.333461',
      '2022-02-09 03:00:37.136728'
    ]

    # pylint: disable=line-too-long
    expected_events = [
      {
        "caller": "12345678-9abc-defg-hijk-lmnopqrstuvw",
        "client_ip": "1.2.3.4",
        "correlation_id": "c0c54eb6-3a17-42e2-b6f6-37484ac276c4",
        "event_data_id": "587eda65-125e-48c2-9b04-ab5e8d3a1d8e",
        "event_name": "BeginRequest",
        "level": "Informational",
        "operation_id": "80287633-d288-49d7-b25e-7ba8cf6bf1da",
        "operation_name": "Microsoft.Compute/disks/delete",
        "resource_group": "TEST-RESOURCE-GROUP",
        "resource_id": "/subscriptions/12345678-9abc-defg-hijk-lmnopqrstuvw/resourceGroups/TEST-RESOURCE-GROUP/providers/Microsoft.Compute/disks/test-vm_disk1_cd8883de78cb4cda97cb858dfe0cda3a",
        "resource_provider": "Microsoft.Compute",
        "resource_type": "Microsoft.Compute/disks",
        "subscription_id": "12345678-9abc-defg-hijk-lmnopqrstuvw",
        "tenant_id": "12345678-9abc-defg-hijk-lmnopqrstuvw"
      },
      {
        "caller": "fakeemail@fakedomain.com",
        "client_ip": "1.2.3.4",
        "correlation_id": "c0c54eb6-3a17-42e2-b6f6-37484ac276c4",
        "event_data_id": "648230f9-fba4-4def-8a83-118b158b748a",
        "event_name": "BeginRequest",
        "level": "Informational",
        "operation_id": "fed1601f-d659-48af-8df7-59ca477866c2",
        "operation_name": "Microsoft.Compute/virtualMachines/delete",
        "resource_group": "test-resource-group",
        "resource_id": "/subscriptions/12345678-9abc-defg-hijk-lmnopqrstuvw/resourceGroups/test-resource-group/providers/Microsoft.Compute/virtualMachines/test-vm",
        "resource_provider": "Microsoft.Compute",
        "resource_type": "Microsoft.Compute/virtualMachines",
        "subscription_id": "12345678-9abc-defg-hijk-lmnopqrstuvw",
        "tenant_id": "12345678-9abc-defg-hijk-lmnopqrstuvw"
      },
      {
        "caller": "12345678-9abc-defg-hijk-lmnopqrstuvw",
        "client_ip": "1.2.3.4",
        "correlation_id": "3a5fe8ed-a996-4b9b-863b-237520d07dc2",
        "event_data_id": "b7c5ffc4-db38-48eb-8a66-ff67bbf05f93",
        "event_name": "BeginRequest",
        "level": "Informational",
        "operation_id": "c26e6db5-6d08-42e8-b7d7-0d0c135b48ef",
        "operation_name": "Microsoft.Compute/disks/write",
        "resource_group": "TEST-RESOURCE-GROUP",
        "resource_id": "/subscriptions/12345678-9abc-defg-hijk-lmnopqrstuvw/resourceGroups/TEST-RESOURCE-GROUP/providers/Microsoft.Compute/disks/test-vm_disk1_cd8883de78cb4cda97cb858dfe0cda3a",
        "resource_provider": "Microsoft.Compute",
        "resource_type": "Microsoft.Compute/disks",
        "subscription_id": "12345678-9abc-defg-hijk-lmnopqrstuvw",
        "tenant_id": "12345678-9abc-defg-hijk-lmnopqrstuvw"
      },
      {
        "caller": "fakeemail@fakedomain.com",
        "client_ip": "1.2.3.4",
        "correlation_id": "3a5fe8ed-a996-4b9b-863b-237520d07dc2",
        "event_data_id": "bd04315c-9658-451e-943f-27ed6fc345a4",
        "event_name": "BeginRequest",
        "level": "Informational",
        "operation_id": "93e52404-5229-437b-ad61-48af3c3281eb",
        "operation_name": "Microsoft.Compute/virtualMachines/write",
        "resource_group": "test-resource-group",
        "resource_id": "/subscriptions/12345678-9abc-defg-hijk-lmnopqrstuvw/resourcegroups/test-resource-group/providers/Microsoft.Compute/virtualMachines/test-vm",
        "resource_provider": "Microsoft.Compute",
        "resource_type": "Microsoft.Compute/virtualMachines",
        "subscription_id": "12345678-9abc-defg-hijk-lmnopqrstuvw",
        "tenant_id": "12345678-9abc-defg-hijk-lmnopqrstuvw"
      }
    ]
    # pylint: enable=line-too-long

    parser = azure_activity_log.AzureActivityLogParser()
    storage_writer = self._ParseFile(['azure_activity_log.jsonl'], parser)

    self.assertEqual(storage_writer.number_of_events, 4)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = storage_writer.GetEvents()
    for event, expected_event, expected_timestamp in zip(
        events, expected_events, expected_timestamps):
      self.CheckTimestamp(event.timestamp, expected_timestamp)
      self.CheckEventValues(storage_writer, event, expected_event)


if __name__ == '__main__':
  unittest.main()
