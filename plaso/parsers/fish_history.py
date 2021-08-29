# -*- coding: utf-8 -*-
"""Parser for fish history files."""

import os
import re

import yaml

from dfdatetime import posix_time as dfdatetime_posix_time

from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import interface


class FishHistoryEventData(events.EventData):
  """Fish history log event data.

  Attributes:
    command (str): command that was executed.
  """

  DATA_TYPE = 'fish:history:command'

  def __init__(self):
    """Initializes event data."""
    super(FishHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None


class FishHistoryParser(interface.FileObjectParser):
  """Parses events from Fish history files."""

  NAME = 'fish_history'
  DATA_FORMAT = 'Fish history file'

  _ENCODING = 'utf-8'

  # 50 MiB is the maximum supported fish history file size.
  _MAXIMUM_FISH_HISTORY_FILE_SIZE = 50 * 1024 * 1024

  _FILENAME = 'fish_history'

  _YAML_FORMAT_RE_1 = re.compile(r'^- cmd: \S+')
  _YAML_FORMAT_RE_2 = re.compile(r'  when: [0-9]{9}')

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a fish history file from a file-like object

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    filename = parser_mediator.GetFilename()

    if filename != self._FILENAME:
      raise errors.UnableToParseFile('Not a Fish history file.')

    text_file_object = text_file.TextFile(file_object, encoding='utf-8')

    header_line_1 = text_file_object.readline()
    header_line_2 = text_file_object.readline()
    if (not self._YAML_FORMAT_RE_1.match(header_line_1) or
        not self._YAML_FORMAT_RE_2.match(header_line_2)):
      raise errors.UnableToParseFile('Not a valid fish history file.')

    file_size = file_object.get_size()
    if file_size > self._MAXIMUM_FISH_HISTORY_FILE_SIZE:
      parser_mediator.ProduceExtractionWarning(
          'Fish history file size: {0:d} exceeds maxmimum'.format(file_size))
      return

    file_object.seek(0, os.SEEK_SET)

    try:
      fish_history = yaml.safe_load(file_object)
    except yaml.YAMLError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Error reading YAML with error: {0:s}'.format(exception))
      return

    for entry_index, history_entry in enumerate(fish_history):
      if not ('cmd' in history_entry and 'when' in history_entry):
        parser_mediator.ProduceExtractionWarning(
            'Unsupported history entry: {0:d}'.format(entry_index))
        return

      event_data = FishHistoryEventData()
      event_data.command = history_entry.get('cmd')

      last_executed = history_entry.get('when')
      if not isinstance(last_executed, int):
        try:
          last_executed = int(last_executed, 10)
        except (TypeError, ValueError) as exception:
          parser_mediator.ProduceExtractionWarning(
              'Unsupported timestamp: {0!s} in history entry: {1:s}'.format(
                  last_executed, entry_index))
          continue

      date_time = dfdatetime_posix_time.PosixTime(timestamp=last_executed)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_RUN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(FishHistoryParser)
