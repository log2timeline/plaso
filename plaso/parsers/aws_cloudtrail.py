# -*- coding: utf-8 -*-
"""Parser for AWS Cloudtrail logging saved to a file."""

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
  """AWS Cloudtrail log event data.

  Attributes:
    event_name (str): The logged AWS event name.
    access_key_id (str): The access key ID associated with the event.
    event_source (str): The AWS service associated with the event.
    user_name (str): The account associated with the event.
    resources (str): The resources associated with the event.
    cloud_trail_event (str): The logged CloudTrailEvent in full.
    source_ip (str): The source IP address associated with the event.
    user_identity_arn (str): The AWS ARN for the user associated with the
      event.
    account_id (str): The AWS account ID associcated with the event.
  """

  DATA_TYPE = 'aws:cloudtrail:json'

  def __init__(self):
    """Initializes event data."""
    super(AWSCloudTrailEventData, self).__init__(data_type=self.DATA_TYPE)
    self.event_name = None
    self.access_key_id = None
    self.event_source = None
    self.user_name = None
    self.resources = None
    self.cloud_trail_event = None
    self.source_ip = None
    self.user_identity_arn = None
    self.account_id = None


class AWSCloudTrailParser(interface.FileObjectParser):
  """Parser for AWS Cloudtrail logs saved in JSON-L format."""

  NAME = 'aws_cloudtrail'
  DATA_FORMAT = 'AWS Cloudtrail Logging'

  _ENCODING = 'utf-8'

  def _ParseAWSCloudtrailLog(self, parser_mediator, file_object):
    """Extract events from AWS Cloudtrail logging in JSON-L format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
    """
    text_file_object = text_file.TextFile(file_object)

    for line in text_file_object:
      json_log_entry = json.loads(line)

      time_string = json_log_entry.get('EventTime')
      if not time_string:
        continue

      event_data = AWSCloudTrailEventData()
      event_data.event_name = json_log_entry.get('EventName')
      event_data.access_key_id = json_log_entry.get('AccessKeyId')
      event_data.event_source = json_log_entry.get('EventSource')
      event_data.user_name = json_log_entry.get('Username')

      resource_list = json_log_entry.get('Resources')
      # Flatten multiple resources into a string of resource names.
      if resource_list:
        event_data.resources = ', '.join(
            [resource['ResourceName'] for resource in resource_list])

      event_data.cloud_trail_event = json_log_entry.get('CloudTrailEvent')
      if event_data.cloud_trail_event:
        ct_event_json = None
        try:
          ct_event_json = json.loads(event_data.cloud_trail_event)
        except json_decoder.JSONDecodeError as exception:
          parser_mediator.ProduceExtractionWarning(
              f'Unable to decode CloudTrailEvent JSON {str(exception)}')
        if ct_event_json:
          event_data.source_ip = ct_event_json.get('sourceIPAddress')
          user_id_json = ct_event_json.get('userIdentity')
          if user_id_json:
            event_data.user_identity_arn = user_id_json.get('arn')
            event_data.account_id = ct_event_json.get('accountId')

      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDateTimeString(time_string)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning(
            f'Unable to parse time string: {time_string} with error: '
            f'{str(exception)}')
        date_time = dfdatetime_semantic_time.InvalidTime()

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses AWS Cloudtrail logging saved in JSON-L format.
    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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

    first_line_json = None
    try:
      first_line = text_file_object.readline()
      first_line_json = json.loads(first_line)
    except json_decoder.JSONDecodeError:
      raise errors.WrongParser('could not decode json.')
    file_object.seek(0, os.SEEK_SET)

    if first_line_json and 'CloudTrailEvent' in first_line_json:
      self._ParseAWSCloudtrailLog(parser_mediator, file_object)
    else:
      raise errors.WrongParser(
          'no "CloudTrailEvent" field, not an AWS log entry.')


manager.ParsersManager.RegisterParser(AWSCloudTrailParser)
