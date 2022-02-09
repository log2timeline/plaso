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
    action (str): The logged Azure action.
  """

  DATA_TYPE = 'azure:activitylog:json'

  def __init__(self):
    """Initializes event data."""
    super(AzureActivityLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None


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
      event_data.action = json_log_entry['authorization']['action']

      # TODO: parse events here!

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

    first_line_json = None
    try:
      first_line = text_file_object.readline()
      first_line_json = json.loads(first_line)
    except json_decoder.JSONDecodeError:
      raise errors.WrongParser('could not decode json.')
    file_object.seek(0, os.SEEK_SET)

    if first_line_json and 'subscription_id' in first_line_json:
      self._ParseAzureActivityLog(parser_mediator, file_object)
    else:
      raise errors.WrongParser(
          'no "subscription_id" field, not an Azure activity log entry.')


manager.ParsersManager.RegisterParser(AzureActivityLogParser)
