# -*- coding: utf-8 -*
"""Tests for the JSON-L parser plugin for Google Cloud (GCP) log files."""

import unittest

from plaso.parsers.jsonl_plugins import gcp_log

from tests.parsers.jsonl_plugins import test_lib


class GCPLogJSONLPluginTest(test_lib.JSONLPluginTestCase):
  """Tests for the JSON-L parser plugin for Google Cloud (GCP) log files."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = gcp_log.GCPLogJSONLPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin(
        ['gcp_logging.jsonl'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'container': None,
        'event_subtype': 'beta.compute.networks.insert',
        'event_type': None,
        'filename': None,
        'firewall_rules': None,
        'firewall_source_ranges': None,
        'log_name': (
            'projects/fake-project/logs/cloudaudit.googleapis.com%2Factivity'),
        'message': None,
        'policy_deltas': None,
        'recorded_time': '2021-10-19T02:57:47.339377+00:00',
        'request_account_identifier': None,
        'request_description': None,
        'request_direction': None,
        'request_email': None,
        'request_member': None,
        'request_metadata': [
            'callerIp: 1.1.1.1', 'callerSuppliedUserAgent: UserAgent'],
        'request_name': None,
        'request_target_tags': None,
        'resource_labels': [
            'network_id: 4881930676783516364', 'project_id: fake-project'],
        'resource_name': 'projects/fake-project/global/networks/test',
        'service_account_display_name': None,
        'service_name': 'compute.googleapis.com',
        'severity': 'NOTICE',
        'text_payload': None,
        'user': 'fakeemailxyz@gmail.com'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
