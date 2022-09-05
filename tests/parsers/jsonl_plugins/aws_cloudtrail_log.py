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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'access_key': '0123456789ABCDEFGHIJ',
        'event_name': 'DescribeInstances',
        'event_source': 'ec2.amazonaws.com',
        'source_ip': '1.2.3.4',
        'timestamp': '2022-02-07 22:23:37.000000',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'}
    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'access_key': '0123456789ABCDEFGHIJ',
        'event_name': 'TerminateInstances',
        'event_source': 'ec2.amazonaws.com',
        'resources': 'i-01234567890123456',
        'source_ip': '1.2.3.4',
        'timestamp': '2022-02-07 22:23:18.000000',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'}
    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'access_key': '0123456789ABCDEFGHIJ',
        'event_name': 'StopInstances',
        'event_source': 'ec2.amazonaws.com',
        'resources': 'i-01234567890123456',
        'source_ip': '1.2.3.4',
        'timestamp': '2022-02-07 22:23:03.000000',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'}
    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'event_name': 'SharedSnapshotVolumeCreated',
        'event_source': 'ec2.amazonaws.com',
        'source_ip': 'ec2.amazonaws.com',
        'timestamp': '2022-02-07 22:19:07.000000'}
    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'access_key': '0123456789ABCDEFGHIJ',
        'event_name': 'RunInstances',
        'event_source': 'ec2.amazonaws.com',
        'resources': (
            'vpc-01234567890123456, ami-01234567890123456, '
            'eni-01234567890123456, i-01234567890123456, aws-testing, '
            'no-access, sg-01234567890123456, subnet-01234567890123456'),
        'source_ip': '1.2.3.4',
        'timestamp': '2022-02-07 22:19:05.000000',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'}
    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'access_key': '0123456789ABCDEFGHIJ',
        'event_name': 'CreateSecurityGroup',
        'event_source': 'ec2.amazonaws.com',
        'resources': 'vpc-01234567890123456, no-access, sg-01234567890123456',
        'source_ip': '1.2.3.4',
        'timestamp': '2022-02-07 22:19:04.000000',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'}
    self.CheckEventValues(storage_writer, events[5], expected_event_values)


if __name__ == '__main__':
  unittest.main()
