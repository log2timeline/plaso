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
    self.assertEqual(number_of_event_data, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'caller_ip': '1.1.1.1',
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
        'request_name': None,
        'request_target_tags': None,
        'resource_labels': [
            'network_id: 4881930676783516364', 'project_id: fake-project'],
        'resource_name': 'projects/fake-project/global/networks/test',
        'service_account_display_name': None,
        'service_name': 'compute.googleapis.com',
        'severity': 'NOTICE',
        'text_payload': None,
        'user_agent': 'UserAgent'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testComputeInstancesInsert(self):
    """Tests for the JSON-L parser plugin parsing request type
    compute.instances.insert."""
    plugin = gcp_log.GCPLogJSONLPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin(
        ['gcp_logging.jsonl'], plugin)

    expected_event_values = {
        'caller_ip': '1.1.1.1',
        'container': None,
        'dcsa_emails': ['fake-service-account@fake-project.com'],
        'dcsa_scopes': ['https://www.googleapis.com/auth/cloud-platform'],
        'delegation_chain': (
            'service-account-one@fake-project.com->'
            'service-account-two@fake-project.com'),
        'event_subtype': 'beta.compute.instances.insert',
        'event_type': None,
        'filename': None,
        'firewall_rules': None,
        'firewall_source_ranges': None,
        'gcloud_command_id': 'a1b2c3d4e5f6',
        'gcloud_command_partial': 'gcloud compute instances insert',
        'log_name': (
            'projects/fake-project/logs/cloudaudit.googleapis.com%2Factivity'),
        'method_name': 'beta.compute.instances.insert',
        'message': None,
        'permissions': [
            'compute.instances.create',
            'compute.disks.create',
            'compute.subnetworks.use',
            'compute.subnetworks.useExternalIp',
            'compute.instances.setMetadata',
            'compute.instances.setLabels',
            'compute.instances.setServiceAccount'],
        'policy_deltas': None, 
        'principal_email': 'fake-account@fake-project.com',
        'principal_subject': 'user:fake-account@fake-project.com',
        'recorded_time': '2024-04-26T20:10:10.024055+00:00',
        'request_account_identifier': None,
        'request_description': 'Fake GCE instance',
        'request_direction': None,
        'request_email': None,
        'request_member': None,
        'request_metadata': None,
        'request_name': 'fake-compute-instance',
        'request_target_tags': None,
        'resource_labels': [
            'instance_id: 9876543210',
            'project_id: fake-project',
            'zone: us-central1-b'],
        'resource_name': (
            'projects/1234567890/zones/us-central1-b/instances/'
            'fake-compute-instance'),
        'service_account_delegation': [
            'service-account-one@fake-project.com',
            'service-account-two@fake-project.com'],
        'service_account_display_name': None,
        'service_account_key_name': None,
        'service_name': 'compute.googleapis.com',
        'severity': 'NOTICE',
        'source_images': [
            'projects/fake-project/global/images/fake-source-image'],
        'status_code': '',
        'status_message': '',
        'text_payload': None,
        'user_agent': (
            'fake-user-agent-string command/gcloud.compute.instances.insert'
            ' invocation-id/a1b2c3d4e5f6 environment/GCE')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 9)
    self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
  unittest.main()
