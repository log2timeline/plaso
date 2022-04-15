# -*- coding: utf-8 -*-
"""Parser for AWS CloudTrail log files."""

import json
import json.decoder as json_decoder
import os

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements
from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import interface


class AWSCloudTrailEventData(events.EventData):
  """AWS CloudTrail log event data.

  Attributes:
    access_key (str): access key identifier.
    account_identifier (str): AWS account identifier.
    cloud_trail_event (str): CloudTrail event.
    event_name (str): event name.
    event_source (str): AWS service.
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
    self.resources = None
    self.source_ip = None
    self.user_identity_arn = None
    self.user_name = None


class AWSCloudTrailParser(interface.FileObjectParser):
  """Parser for JSON-L AWS CloudTrail log files."""

  NAME = 'aws_cloudtrail'
  DATA_FORMAT = 'AWS CloudTrail log'

  _ENCODING = 'utf-8'

  def _GetJSONValue(self, json_dict, name):
    """Retrieves a value from a JSON dict.

    Args:
      json_dict (dict): JSON dictionary.
      name (str): name of the value to retrieve.

    Returns:
      object: value of the JSON log entry or None if not set.
    """
    json_value = json_dict.get(name)
    if json_value == '':
      json_value = None
    return json_value

  def _ParseAWSCloudTrailLog(self, parser_mediator, json_dict):
    """Extract events from an AWS CloudTrail log entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): log entry JSON dictionary.
    """
    time_string = json_dict.get('EventTime')
    if not time_string:
      parser_mediator.ProduceExtractionWarning(
          'Event time value missing from CloudTrail log entry')
      return

    event_data = AWSCloudTrailEventData()
    event_data.event_name = self._GetJSONValue(json_dict, 'EventName')
    event_data.access_key = self._GetJSONValue(json_dict, 'AccessKeyId')
    event_data.event_source = self._GetJSONValue(json_dict, 'EventSource')
    event_data.user_name = self._GetJSONValue(json_dict, 'Username')

    resource_list = json_dict.get('Resources')
    # Flatten multiple resources into a string of resource names.
    if resource_list:
      event_data.resources = ', '.join(
          [resource['ResourceName'] for resource in resource_list])

    event_data.cloud_trail_event = json_dict.get('CloudTrailEvent')
    if event_data.cloud_trail_event:
      try:
        cloud_trail_event_json = json.loads(event_data.cloud_trail_event)
      except json_decoder.JSONDecodeError as exception:
        cloud_trail_event_json = None
        parser_mediator.ProduceExtractionWarning(
            'Unable to decode CloudTrail event with error: {0!s}'.format(
                exception))

      if cloud_trail_event_json:
        event_data.source_ip = self._GetJSONValue(
            cloud_trail_event_json, 'sourceIPAddress')
        user_identify_json = self._GetJSONValue(
            cloud_trail_event_json, 'userIdentity')

        if user_identify_json:
          event_data.user_identity_arn = self._GetJSONValue(
              user_identify_json, 'arn')
          event_data.account_identifier = self._GetJSONValue(
              cloud_trail_event_json, 'accountId')

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDateTimeString(time_string)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse time string: {0:s} with error: {1!s}'.format(
             time_string, exception))
      date_time = dfdatetime_semantic_time.InvalidTime()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an AWS CloudTrail log file-object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # Trivial JSON format check: first character must be an open brace.
    if file_object.read(1) != b'{':
      raise errors.WrongParser(
          'is not a valid JSON file, missing opening brace.')

    file_object.seek(0, os.SEEK_SET)
    text_file_object = text_file.TextFile(file_object)

    try:
      first_line = text_file_object.readline()
      first_line_json = json.loads(first_line)
    except json_decoder.JSONDecodeError:
      raise errors.WrongParser('could not decode JSON.')

    if not first_line_json:
      raise errors.WrongParser('no JSON found in file.')

    if 'CloudTrailEvent' not in first_line_json:
      raise errors.WrongParser(
          'no "CloudTrailEvent" field, not an AWS log entry.')

    file_object.seek(0, os.SEEK_SET)
    text_file_object = text_file.TextFile(file_object)

    for line in text_file_object:
      json_log_entry = json.loads(line)
      self._ParseAWSCloudTrailLog(parser_mediator, json_log_entry)


manager.ParsersManager.RegisterParser(AWSCloudTrailParser)
