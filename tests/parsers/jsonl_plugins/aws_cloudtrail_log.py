# -*- coding: utf-8 -*
"""Tests for the JSON-L parser plugin for AWS CloudTrail log files."""

import unittest

from plaso.parsers.jsonl_plugins import aws_cloudtrail_log

from tests.parsers.jsonl_plugins import test_lib


class AWSCloudTrailLogJSONLPluginTest(test_lib.JSONLPluginTestCase):
  """Tests for the JSON-L parser plugin for AWS CloudTrail log files."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = aws_cloudtrail_log.AWSCloudTrailLogJSONLPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin(
        ['aws_cloudtrail.jsonl'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_key': '0123456789ABCDEFGHIJ',
        'event_name': 'DescribeInstances',
        'event_source': 'ec2.amazonaws.com',
        'recorded_time': '2022-02-08T09:23:37.000000+11:00',
        'source_ip': '1.2.3.4',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
