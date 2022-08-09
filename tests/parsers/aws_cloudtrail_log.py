# -*- coding: utf-8 -*
"""Tests for the JSON parser for AWS CloudTrail log files."""

import unittest

from plaso.parsers import aws_cloudtrail_log

from tests.parsers import test_lib


class AWSCloudTrailLogParserTest(test_lib.ParserTestCase):
  """Tests for the JSON parser for AWS CloudTrail log files."""


  def testParse(self):
    """Tests the Parse function."""
    parser = aws_cloudtrail_log.AWSCloudTrailLogParser()
    storage_writer = self._ParseFile(['aws_cloudtrail.json'], parser)


    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        "event_version": "1.0",
        "user_identity": '{"type": "IAMUser", "principalId": "EX_PRINCIPAL_ID", "arn": "arn:aws:iam::123456789012:user/Alice", "accessKeyId": "EXAMPLE_KEY_ID", "accountId": "123456789012", "userName": "Alice"}',
        "timestamp": "2014-03-06 21:22:54.000000",
        "event_source": "ec2.amazonaws.com",
        "event_name": "StartInstances",
        "aws_region": "us-east-2",
        "source_ip_address": "205.251.233.176",
        "user_agent": "ec2-api-tools 1.6.12.2",
        "request_parameters": '{"instancesSet": {"items": [{"instanceId": "i-ebeaf9e2"}]}}',
        "response_elements": '{"instancesSet": {"items": [{"instanceId": "i-ebeaf9e2", "currentState": {"code": 0, "name": "pending"}, "previousState": {"code": 80, "name": "stopped"}}]}}'
    }
    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        "event_version": "1.0",
        "user_identity": '{"type": "IAMUser", "principalId": "EX_PRINCIPAL_ID", "arn": "arn:aws:iam::123456789012:user/Alice", "accountId": "123456789012", "accessKeyId": "EXAMPLE_KEY_ID", "userName": "Alice"}',
        "timestamp": "2014-03-06 21:01:59.000000",
        "event_source": "ec2.amazonaws.com",
        "event_name": "StopInstances",
        "aws_region": "us-east-2",
        "source_ip_address": "205.251.233.176",
        "user_agent": "ec2-api-tools 1.6.12.2",
        "request_parameters": '{"instancesSet": {"items": [{"instanceId": "i-ebeaf9e2"}]}, "force": false}',
        "response_elements": '{"instancesSet": {"items": [{"instanceId": "i-ebeaf9e2", "currentState": {"code": 64, "name": "stopping"}, "previousState": {"code": 16, "name": "running"}}]}}'
    }
    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        "event_version": "1.07",
        "timestamp": "2019-11-14 00:51:00.000000",
        "aws_region": "us-east-1",
        "event_id": "EXAMPLE8-9621-4d00-b913-beca2EXAMPLE",
        "event_type": "AwsCloudTrailInsight",
        "recipient_account_id": "123456789012",
        "shared_event_id": "EXAMPLE2-1729-42f1-b735-5d8c0EXAMPLE",
        "insight_details": '{"state": "Start", "eventSource": "ssm.amazonaws.com", "eventName": "UpdateInstanceInformation", "insightType": "ApiCallRateInsight", "insightContext": {"statistics": {"baseline": {"average": 85.4202380952}, "insight": {"average": 664}}}}',
        "event_category": "Insight"
    }
    self.CheckEventValues(storage_writer, events[7], expected_event_values)

if __name__ == '__main__':
  unittest.main()
