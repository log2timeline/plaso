# -*- coding: utf-8 -*-
"""JSON-L parser plugin for AWS CloudTrail log files."""

import json

from json import decoder as json_decoder

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class AWSCloudTrailEventData(events.EventData):
  """AWS CloudTrail log event data.

  Attributes:
    access_key (str): access key identifier.
    account_identifier (str): AWS account identifier.
    cloud_trail_event (str): CloudTrail event.
    event_name (str): event name.
    event_source (str): AWS service.
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    resources (str): resources.
    source_ip (str): source IP address.
    user_identity_arn (str): AWS ARN of the user.
    user_name (str): name of the AWS user.
  """

  DATA_TYPE = 'aws:cloudtrail:entry'

  def __init__(self):
    """Initializes event data."""
    super(AWSCloudTrailEventData, self).__init__(data_type=self.DATA_TYPE)
    self.access_key = None
    self.account_identifier = None
    self.cloud_trail_event = None
    self.event_name = None
    self.event_source = None
    self.recorded_time = None
    self.resources = None
    self.source_ip = None
    self.user_identity_arn = None
    self.user_name = None


class AWSCloudTrailLogJSONLPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for AWS CloudTrail log files."""

  NAME = 'aws_cloudtrail_log'
  DATA_FORMAT = 'AWS CloudTrail Log'

  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses an AWS CloudTrail log record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the log record.
    """
    date_time = None

    event_time = self._GetJSONValue(json_dict, 'EventTime')
    if event_time:
      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDateTimeString(event_time)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning(
            'Unable to parse EventTime value: {0:s} with error: {1!s}'.format(
               event_time, exception))
        date_time = None

    resource_list = self._GetJSONValue(
        json_dict, 'Resources', default_value=[])
    # Flatten multiple resources into a string of resource names.
    resources = ', '.join(
        [resource['ResourceName'] for resource in resource_list])

    cloud_trail_event = self._GetJSONValue(
        json_dict, 'CloudTrailEvent', default_value='{}')
    try:
      cloud_trail_event_json = json.loads(cloud_trail_event)
    except json_decoder.JSONDecodeError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to decode CloudTrail event with error: {0!s}'.format(
              exception))
      cloud_trail_event_json = {}

    user_identity_json = self._GetJSONValue(
        cloud_trail_event_json, 'userIdentity')

    event_data = AWSCloudTrailEventData()
    event_data.access_key = self._GetJSONValue(json_dict, 'AccessKeyId')
    event_data.account_identifier = self._GetJSONValue(
        cloud_trail_event_json, 'accountId')
    event_data.cloud_trail_event = cloud_trail_event
    event_data.event_name = self._GetJSONValue(json_dict, 'EventName')
    event_data.event_source = self._GetJSONValue(json_dict, 'EventSource')
    event_data.recorded_time = date_time
    event_data.resources = resources or None
    event_data.source_ip = self._GetJSONValue(
        cloud_trail_event_json, 'sourceIPAddress')
    event_data.user_identity_arn = self._GetJSONValue(user_identity_json, 'arn')
    event_data.user_name = self._GetJSONValue(json_dict, 'Username')

    parser_mediator.ProduceEventData(event_data)

  def CheckRequiredFormat(self, json_dict):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      json_dict (dict): JSON dictionary of the log record.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    cloud_trail_event = self._GetJSONValue(json_dict, 'CloudTrailEvent')
    event_time = self._GetJSONValue(json_dict, 'EventTime')

    if None in (cloud_trail_event, event_time):
      return False

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

    try:
      date_time.CopyFromDateTimeString(event_time)
    except ValueError:
      return False

    return True


jsonl_parser.JSONLParser.RegisterPlugin(AWSCloudTrailLogJSONLPlugin)
