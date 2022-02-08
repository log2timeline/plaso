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
      "2022-02-07 22:23:37.000000",
      "2022-02-07 22:23:18.000000",
      "2022-02-07 22:23:03.000000",
      "2022-02-07 22:19:07.000000",
      "2022-02-07 22:19:05.000000",
      "2022-02-07 22:19:04.000000",
    ]

    # pylint: disable=line-too-long
    expected_event_values = [
      {
        "user": "fakeusername",
        "action": "DescribeInstances",
        "resource": "(no resource)"
      },
      {
        "user": "fakeusername",
        "action": "TerminateInstances",
        "resource": "i-01234567890123456"
      },
      {
        "user": "fakeusername",
        "action": "StopInstances",
        "resource": "i-01234567890123456"
      },
      {
        "user": "(no user)",
        "action": "SharedSnapshotVolumeCreated",
        "resource": "(no resource)"
      },
      {
        "user": "fakeusername",
        "action": "RunInstances",
        "resource": "vpc-01234567890123456, ami-01234567890123456, eni-01234567890123456, i-01234567890123456, aws-testing, no-access, sg-01234567890123456, subnet-01234567890123456"
      },
      {
        "user": "fakeusername",
        "action": "CreateSecurityGroup",
        "resource": "vpc-01234567890123456, no-access, sg-01234567890123456"
      },
    ]
    # pylint: enable=line-too-long

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
