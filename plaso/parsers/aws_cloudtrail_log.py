# -*- coding: utf-8 -*-
"""JSON-L parser plugin for AWS CloudTrail log files."""

import json
import os


from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.parsers import manager
from plaso.lib import errors
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import interface


class AWSCloudTrailEventData(events.EventData):
  """AWS CloudTrail log event data.

  Attributes:
    eventTime
    eventVersion
    userIdentity
    eventSource
    eventName
    awsRegion
    sourceIPAddress
    userAgent
    errorCode
    errorMessage
    requestParameters
    responseElements
    additionalEventData
    requestID
    eventID
    eventType
    apiVersion
    managementEvent
    readOnly
    resources
    recipientAccountId
    serviceEventDetails
    sharedEventID
    vpcEndpointId
    eventCategory
    addendum
    sessionCredentialFromConsole
    edgeDeviceDetails
    tlsDetails
    insightDetails
  """

  DATA_TYPE = 'aws:cloudtrail:entry'

  def __init__(self):
    """Initializes event data."""
    super(AWSCloudTrailEventData, self).__init__(data_type=self.DATA_TYPE)
    self.event_version = None
    self.user_identity = None
    self.event_source = None
    self.event_name = None
    self.aws_region = None
    self.source_ip_address = None
    self.user_agent = None
    self.error_code = None
    self.error_message = None
    self.request_parameters = None
    self.response_elements = None
    self.additional_event_data = None
    self.request_id = None
    self.event_id = None
    self.event_type = None
    self.api_version = None
    self.management_event = None
    self.read_only = None
    self.resources = None
    self.recipient_account_id = None
    self.service_event_details = None
    self.shared_event_id = None
    self.vpc_endpoint_id = None
    self.event_category = None
    self.addendum = None
    self.session_credential_from_console = None
    self.edge_device_details = None
    self.tls_details = None
    self.insight_details = None


class AWSCloudTrailLogParser(interface.FileObjectParser):
  """JSON parser for AWS CloudTrail log files."""

  NAME = 'aws_cloudtrail_log'
  DATA_FORMAT = 'AWS CloudTrail Log'

  # source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html
  _PROPERTIES = {
      'eventVersion': 'event_version',
      'eventSource': 'event_source',
      'eventName': 'event_name',
      'awsRegion': 'aws_region',
      'sourceIPAddress': 'source_ip_address',
      'userAgent': 'user_agent',
      'errorCode': 'error_code',
      'errorMessage': 'error_message',
      'additionalEventData': 'additional_event_data',
      'requestID': 'request_id',
      'eventID': 'event_id',
      'eventType': 'event_type',
      'apiVersion': 'api_version',
      'managementEvent': 'management_event',
      'readOnly': 'read_only',
      'resources': 'resources',
      'recipientAccountId': 'recipient_account_id',
      'serviceEventDetails': 'service_event_details',
      'sharedEventID': 'shared_event_id',
      'vpcEndpointId': 'vpc_endpoint_id',
      'eventCategory': 'event_category',
      'addendum': 'addendum',
      'sessionCredentialFromConsole': 'session_credential_from_console',
      'edgeDeviceDetails': 'edge_device_details',
      'tlsDetails': 'tls_details'
  }

  _JSON_PROPERTIES = {
    'userIdentity': 'user_identity',
    'requestParameters': 'request_parameters',
    'responseElements': 'response_elements',
    'insightDetails': 'insight_details'
  }

  REQUIRED_KEYS = frozenset(['eventVersion', 'userIdentity', 'eventSource', 'eventName', 'awsRegion'])

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an AWS CloudTrail log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # First pass check for initial character being open brace.
    if file_object.read(12) != b'{"Records":[':
      raise errors.WrongParser((
          '[{0:s}] {1:s} is not a valid log file, '
          'missing Records.').format(
              self.NAME, parser_mediator.GetDisplayName()))

    file_object.seek(0, os.SEEK_SET)
    file_content = file_object.read()
    json_records = []

    # Second pass to verify it's valid JSON
    try:
      json_dict = json.loads(file_content)
      json_records = json_dict['Records']
    except ValueError as exception:
      raise errors.WrongParser((
          '[{0:s}] Unable to parse file {1:s} as JSON: {2!s}').format(
              self.NAME, parser_mediator.GetDisplayName(), exception))
    except IOError as exception:
      raise errors.WrongParser((
          '[{0:s}] Unable to open file {1:s} for parsing as'
          'JSON: {2!s}').format(
              self.NAME, parser_mediator.GetDisplayName(), exception))
    except Exception as exception:
      raise errors.WrongParser((
          '[{0:s}] Unable to parse file {1:s} as JSON: {2!s}').format(
              self.NAME, parser_mediator.GetDisplayName(), exception))

    # Third pass to verify the file has the correct keys in it
    if not set(self.REQUIRED_KEYS).issubset(set(json_records[0].keys())):
      raise errors.WrongParser('File does not contain required keys.')

    for json_record in json_records:
      self._ParseRecord(parser_mediator, json_record)


  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses an AWS CloudTrail log record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the log record.
    """
    event_time = json_dict.get('eventTime')
    if not event_time:
      parser_mediator.ProduceExtractionWarning(
          'Event time value missing from cloudtrail log event')

    event_data = AWSCloudTrailEventData()
    for json_name, attribute_name in self._PROPERTIES.items():
      attribute_value = str(json_dict.get(json_name, ''))
      setattr(event_data, attribute_name, attribute_value)

    for json_name, attribute_name in self._JSON_PROPERTIES.items():
      attribute_value = json.dumps(json_dict.get(json_name, ''))
      setattr(event_data, attribute_name, attribute_value)

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(event_time)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse event time value: {0:s} with error: {1!s}'.format(
              event_time, exception))
      date_time = dfdatetime_semantic_time.InvalidTime()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(AWSCloudTrailLogParser)
