# -*- coding: utf-8 -*-
"""Parser for Azure activity log files."""

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


class AzureActivityLogEventData(events.EventData):
  """Azure activity log event data.

  Attributes:
    caller (str): Azure identity.
    client_ip (str): client IP address.
    correlation_identifier (str): Correlation identifier.
    event_data_identifier (str): Event data identifier.
    event_name (str): name of the event.
    level (str): log level.
    operation_identifier (str): Operation identifier.
    operation_name (str): operation name.
    resource_group (str): resource group.
    resource_identifier (str): resource.
    resource_provider (str): API service.
    resource_type (str): resource type.
    subscription_identifier (str): subscription identifier.
    tenant_identifier (str): tenant identifier.
  """

  DATA_TYPE = 'azure:activitylog:entry'

  def __init__(self):
    """Initializes event data."""
    super(AzureActivityLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.caller = None
    self.client_ip = None
    self.correlation_identifier = None
    self.event_data_identifier = None
    self.event_name = None
    self.level = None
    self.operation_identifier = None
    self.operation_name = None
    self.resource_group = None
    self.resource_identifier = None
    self.resource_provider = None
    self.resource_type = None
    self.subscription_identifier = None
    self.tenant_identifier = None


class AzureActivityLogParser(interface.FileObjectParser):
  """Parser for Azure activity log files."""

  NAME = 'azure_activitylog'
  DATA_FORMAT = 'Azure Activity Logging'

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

  def _ParseAzureActivityLog(self, parser_mediator, json_dict):
    """Extracts events from an Azure activity log entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): log entry JSON dictionary.
    """
    time_string = json_dict.get('event_timestamp')
    if not time_string:
      parser_mediator.ProduceExtractionWarning(
          'Event timestamp value missing from activity log entry')
      return

    event_data = AzureActivityLogEventData()
    event_data.caller = self._GetJSONValue(json_dict, 'caller')
    event_data.event_data_identifier = self._GetJSONValue(
        json_dict, 'event_data_id')
    event_data.correlation_identifier = self._GetJSONValue(
        json_dict, 'correlation_id')

    event_name_json = json_dict.get('event_name')
    if event_name_json:
      event_data.event_name = self._GetJSONValue(event_name_json, 'value')

    http_request_json = json_dict.get('http_request')
    if http_request_json:
      event_data.client_ip = self._GetJSONValue(
        http_request_json, 'client_ip_address')

    event_data.level = self._GetJSONValue(json_dict, 'level')
    event_data.resource_group = self._GetJSONValue(
        json_dict, 'resource_group_name')

    resource_provider_name_json = json_dict.get('resource_provider_name')
    if resource_provider_name_json:
      event_data.resource_provider = self._GetJSONValue(
          resource_provider_name_json, 'value')

    event_data.resource_identifier = self._GetJSONValue(
        json_dict, 'resource_id')

    resource_type_json = json_dict.get('resource_type')
    if resource_type_json:
      event_data.resource_type = self._GetJSONValue(
          resource_type_json, 'value')

    event_data.operation_identifier = self._GetJSONValue(
        json_dict, 'operation_id')

    operation_name_json = json_dict.get('operation_name')
    if operation_name_json:
      event_data.operation_name = self._GetJSONValue(
          operation_name_json, 'value')

    event_data.subscription_identifier = self._GetJSONValue(
        json_dict, 'subscription_id')
    event_data.tenant_identifier = self._GetJSONValue(json_dict, 'tenant_id')

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(time_string)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse time string: {0:s} with error: {1!s}'.format(
              time_string, exception))
      date_time = dfdatetime_semantic_time.InvalidTime()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an Azure activity log file-object.

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

    if 'subscription_id' not in first_line_json:
      raise errors.WrongParser(
          'no "subscription_id" field, not an Azure activity log entry.')

    file_object.seek(0, os.SEEK_SET)
    text_file_object = text_file.TextFile(file_object)

    for line in text_file_object:
      json_log_entry = json.loads(line)
      self._ParseAzureActivityLog(parser_mediator, json_log_entry)


manager.ParsersManager.RegisterParser(AzureActivityLogParser)
