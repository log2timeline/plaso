# -*- coding: utf-8 -*
"""Tests for the AWS Cloudtrail logging parser."""

import unittest

from plaso.parsers import aws_cloudtrail
from tests.parsers import test_lib


class AWSCloudTrailTest(test_lib.ParserTestCase):
  """Tests for the AWS Cloudtrail logging parser."""

  def testParseAWSCloudtrail(self):
    """Tests that AWS Cloudtrail logs are correctly parsed."""

    expected_timestamps = [
      '2022-02-07 22:23:37.000000',
      '2022-02-07 22:23:18.000000',
      '2022-02-07 22:23:03.000000',
      '2022-02-07 22:19:07.000000',
      '2022-02-07 22:19:05.000000',
      '2022-02-07 22:19:04.000000',
    ]

    expected_event_values = [
      {
        'access_key_id': '0123456789ABCDEFGHIJ',
        'event_name': 'DescribeInstances',
        'event_source': 'ec2.amazonaws.com',
        'source_ip': '1.2.3.4',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'
      },
      {
        'access_key_id': '0123456789ABCDEFGHIJ',
        'event_name': 'TerminateInstances',
        'event_source': 'ec2.amazonaws.com',
        'resources': 'i-01234567890123456',
        'source_ip': '1.2.3.4',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'
      },
      {
        'access_key_id': '0123456789ABCDEFGHIJ',
        'event_name': 'StopInstances',
        'event_source': 'ec2.amazonaws.com',
        'resources': 'i-01234567890123456',
        'source_ip': '1.2.3.4',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'
      },
      {
        'event_name': 'SharedSnapshotVolumeCreated',
        'event_source': 'ec2.amazonaws.com',
        'source_ip': 'ec2.amazonaws.com'
      },
      {
        'access_key_id': '0123456789ABCDEFGHIJ',
        'event_name': 'RunInstances',
        'event_source': 'ec2.amazonaws.com',
        'resources': (
            'vpc-01234567890123456, ami-01234567890123456, '
            'eni-01234567890123456, i-01234567890123456, aws-testing, '
            'no-access, sg-01234567890123456, subnet-01234567890123456'),
        'source_ip': '1.2.3.4',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'
      },
      {
        'access_key_id': '0123456789ABCDEFGHIJ',
        'event_name': 'CreateSecurityGroup',
        'event_source': 'ec2.amazonaws.com',
        'resources': 'vpc-01234567890123456, no-access, sg-01234567890123456',
        'source_ip': '1.2.3.4',
        'user_identity_arn': 'arn:aws:iam::012345678901:user/fakeusername',
        'user_name': 'fakeusername'
      },
    ]

    parser = aws_cloudtrail.AWSCloudTrailParser()
    path_segments = ['aws_cloudtrail.jsonl']
    storage_writer = self._ParseFile(path_segments, parser)

    self.assertEqual(storage_writer.number_of_events, 6)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())
    for index, event in enumerate(events):
      self.CheckTimestamp(event.timestamp, expected_timestamps[index])
      self.CheckEventValues(
          storage_writer, event, expected_event_values[index])


if __name__ == '__main__':
  unittest.main()
