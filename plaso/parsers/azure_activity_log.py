# -*- coding: utf-8 -*-
"""Parser for Azure activity logging saved to a file."""

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
    caller (str): The Azure identity associated with the log entry.
    event_data_id (str): Event data ID for the log entry.
    correlation_id (str): Correlation ID for the log entry.
    event_name (str): The name of the event associated with the log
      entry.
    client_ip (str): The client IP address associated with the log entry.
    level (str): The log level associated with the log entry.
    resource_group (str): The resource group associated with the log entry.
    resource_provider (str): The API service associated with the log entry.
    resource_id (str): The resource associated with the log entry.
    resource_type (str): The resource type associated with the log entry.
    operation_id (str): Operation ID associated with the log entry.
    operation_name (str): The operation name associated with the log entry.
    subscription_id (str): The subscription ID associated with the log entry.
    tenant_id (str): The tenant ID associated with the log entry.
  """

  DATA_TYPE = 'azure:activitylog:json'

  def __init__(self):
    """Initializes event data."""
    super(AzureActivityLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.caller = None
    self.event_data_id = None
    self.correlation_id = None
    self.event_name = None
    self.client_ip = None
    self.level = None
    self.resource_group = None
    self.resource_provider = None
    self.resource_id = None
    self.resource_type = None
    self.operation_id = None
    self.operation_name = None
    self.subscription_id = None
    self.tenant_id = None


class AzureActivityLogParser(interface.FileObjectParser):
  """Parser for Azure activity logs saved in JSON-L format."""

  NAME = 'azure_activitylog'
  DATA_FORMAT = 'Azure Activity Logging'

  _ENCODING = 'utf-8'

  def _ParseAzureActivityLog(self, parser_mediator, file_object):
    """Extract events from Azure activity logging in JSON-L format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
    """
    text_file_object = text_file.TextFile(file_object)

    for line in text_file_object:
      json_log_entry = json.loads(line)

      time_string = json_log_entry.get('event_timestamp')
      if not time_string:
        continue

      event_data = AzureActivityLogEventData()
      event_data.caller = json_log_entry.get('caller')
      event_data.event_data_id = json_log_entry.get('event_data_id')
      event_data.correlation_id = json_log_entry.get('correlation_id')

      if 'event_name' in json_log_entry:
        event_data.event_name = json_log_entry['event_name'].get('value')

      if 'http_request' in json_log_entry:
        event_data.client_ip = json_log_entry['http_request'].get(
          'client_ip_address')
      event_data.level = json_log_entry.get('level')
      event_data.resource_group = json_log_entry.get('resource_group_name')

      if 'resource_provider_name' in json_log_entry:
        event_data.resource_provider = (
            json_log_entry['resource_provider_name'].get('value'))
      event_data.resource_id = json_log_entry.get('resource_id')

      if 'resource_type' in json_log_entry:
        event_data.resource_type = json_log_entry['resource_type'].get('value')
      event_data.operation_id = json_log_entry.get('operation_id')

      if 'operation_name' in json_log_entry:
        event_data.operation_name = json_log_entry['operation_name'].get(
            'value')
      event_data.subscription_id = json_log_entry.get('subscription_id')
      event_data.tenant_id = json_log_entry.get('tenant_id')

      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(time_string)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning(
            f'Unable to parse time string: {time_string} with error: '
            f'{str(exception)}')
        date_time = dfdatetime_semantic_time.InvalidTime()

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses Azure activity logging saved in JSON-L format.

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

    try:
      first_line = text_file_object.readline()
      first_line_json = json.loads(first_line)
    except json_decoder.JSONDecodeError:
      raise errors.WrongParser('could not decode json.')

    if not first_line_json:
      raise errors.WrongParser('no JSON found in file.')

    if 'subscription_id' not in first_line_json:
      raise errors.WrongParser(
          'no "subscription_id" field, not an Azure activity log entry.')

    file_object.seek(0, os.SEEK_SET)
    self._ParseAzureActivityLog(parser_mediator, file_object)


manager.ParsersManager.RegisterParser(AzureActivityLogParser)
