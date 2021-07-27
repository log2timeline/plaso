# -*- coding: utf-8 -*-
"""Parser for fish history files."""
import io
import re

import yaml

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
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

  _FILENAME = 'fish_history'
  _YAML_FORMAT_RE_1 = re.compile(r'^- cmd: \S+')
  _YAML_FORMAT_RE_2 = re.compile(r'  when: [0-9]{9}')

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Fish history file from a file-like object

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      ParseError: if the file is not valid YAML or is not a fish history entry
      UnableToParseFile: when the file cannot be parsed.
    """
    filename = parser_mediator.GetFilename()

    if filename != self._FILENAME:
      raise errors.UnableToParseFile('Not a fish history file.')

    file_contents = file_object.read()

    file_contents_io = io.StringIO(file_contents.decode())
    header_line_1 = file_contents_io.readline()
    header_line_2 = file_contents_io.readline()
    if (not self._YAML_FORMAT_RE_1.match(header_line_1) or
        not self._YAML_FORMAT_RE_2.match(header_line_2)):
      raise errors.UnableToParseFile('Not a valid fish history file.')

    try:
      fish_history = yaml.safe_load(file_contents)
    except yaml.YAMLError as exception:
      raise errors.ParseError(
          'Error while loading/parsing YAML with error {0:s}'
          .format(exception))

    for history_entry in fish_history:
      if not ('cmd' in history_entry and 'when' in history_entry):
        raise errors.ParseError('Invalid yaml structure')

      event_data = FishHistoryEventData()
      event_data.command = history_entry.get('cmd')

      try:
        last_executed = history_entry.get('when')
        if not isinstance(last_executed, int):
          last_executed = int(last_executed, 10)
      except (TypeError, ValueError) as exception:
        logger.debug(
            'Invalid timestamp {0!s}, skipping record'.format(exception))
        continue
      date_time = dfdatetime_posix_time.PosixTime(timestamp=last_executed)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_RUN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(FishHistoryParser)
