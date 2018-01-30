# -*- coding: utf-8 -*-
"""Parser for Google Drive Sync log files."""

from __future__ import unicode_literals

import logging
# TODO: DO NOT SUBMIT, remove
logging.basicConfig(level=logging.DEBUG)

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class GDriveSyncLogEventData(events.EventData):
  """GDrive Sync log event data.

  Attributes:
    time (str): time of event (string, time with offset and timezone of user).
    log_level (str): logging level of event (e.g., DEBUG, WARN, INFO, ERR).
    pid (int): process ID of process which logged event.
    thread (str): ID:name of thread which logged event (colon-separated).
    source_code (str): filename:line_number of source file which logged event.
    message (str): log message.
  """

  DATA_TYPE = 'gdrive_sync:log:line'

  def __init__(self):
    """Initializes event data."""
    super(GDriveSyncLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.time = None
    self.log_level = None
    self.pid = None
    self.thread = None
    self.source_code = None
    self.message = None


class GDriveSyncLogParser(text_parser.PyparsingMultiLineTextParser):
  """Parses events from GDrive Sync log files."""

  NAME = 'gdrive_synclog'

  DESCRIPTION = 'Parser for GDrive Sync log files.'

  # TODO: confirm this is ascii on OS X, Linux?
  _ENCODING = 'ascii'

  # Common structures.
  _HYPHEN = text_parser.PyparsingConstants.HYPHEN

  _FOUR_DIGITS = text_parser.PyparsingConstants.FOUR_DIGITS
  _THREE_DIGITS = text_parser.PyparsingConstants.THREE_DIGITS
  _TWO_DIGITS = text_parser.PyparsingConstants.TWO_DIGITS

  # Ignore commas and spaces.
  IGNORE_FIELD = pyparsing.CharsNotIn(',').suppress()

  _GDS_DATE_TIME = (
      _FOUR_DIGITS.setResultsName('year') + _HYPHEN +
      _TWO_DIGITS.setResultsName('month') + _HYPHEN +
      _TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME_MSEC_ELEMENTS +
      # TODO: consider adding tz-offset support to parsers/text_parser.py?
      pyparsing.Word(pyparsing.printables).setResultsName('time_zone_offset')
  ).setResultsName('date_time')

  # Multiline entry end marker, matched from right to left.
  _GDS_ENTRY_END = pyparsing.StringEnd() | _GDS_DATE_TIME

  _GDS_LINE = (
      _GDS_DATE_TIME +
      pyparsing.Word(pyparsing.alphas).setResultsName('log_level') +
      # TODO: strip pid= out, cast to integers?
      pyparsing.Word(pyparsing.printables).setResultsName('pid') +
      # TODO: consider stripping thread identifier/cleaning up thread name?
      pyparsing.Word(pyparsing.printables).setResultsName('thread') +
      pyparsing.Word(pyparsing.printables).setResultsName('source_code') +
      pyparsing.SkipTo(_GDS_ENTRY_END).setResultsName('message') +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  LINE_STRUCTURES = [
      ('logline', _GDS_LINE),
  ]

  def _ParseLine(self, parser_mediator, structure):
    """Parses a logline and store appropriate attributes.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    # Some hacks follow: our log source uses a different datetime format than
    # dfdatetime does, and there appear to be some pending changes surrounding
    # is_local_time and converting to UTC (see
    # https://github.com/log2timeline/dfdatetime/issues/47, possibly others).
    # As such, I'm hacking around things with some string reformats to get it
    # working for a first-pass, and will take direction from jbmetz when I have
    # more context on the ongoing work/best practices.
    year, month, day_of_month, hours, minutes, seconds, milliseconds, tz = (
        structure.date_time)

    # TimeElementsInMilliseconds appears not to support local timezones, yet,
    # and time_elements.CopyFromDateTimeString requires a different format.
    # Initialize it without the TZ, then convert to a TZ-aware value with
    # a formatting hack and CopyFromDateTimeString.
    dfdatetime_obj = dfdatetime_time_elements.TimeElementsInMilliseconds(
        [year, month, day_of_month, hours, minutes, seconds, milliseconds])

    dt_hack = '{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}.{:03d}{!s}:{!s}'.format(
        year, month, day_of_month, hours, minutes, seconds, milliseconds,
        # TODO(johngalvin): Make this less awful.
        tz[0:3], tz[3:5])
    try:
      dfdatetime_obj.CopyFromDateTimeString(dt_hack)
    except ValueError:
      parser_mediator.ProduceExtractionError(
          'invalid date time value: {0!s}'.format(structure.date_time))
      return

    event_data = GDriveSyncLogEventData()
    event_data.log_level = structure.log_level
    event_data.pid = structure.pid
    event_data.thread = structure.thread
    event_data.source_code = structure.source_code
    # Replace newlines with spaces in structure.message to preserve output.
    event_data.message = structure.message.replace('\n', ' ')

    event = time_events.DateTimeValuesEvent(
        dfdatetime_obj, definitions.TIME_DESCRIPTION_ADDED)

    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse each record structure and return an EventObject if applicable.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): identifier of the structure of tokens.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    # Note: this may be overcomplicated/unnecessary; I'm mostly cloning SkyDrive
    # parser but GDrive sync seems to have no header/other key types: consider
    # refactoring or extending this in the future.
    if key == 'logline':
      self._ParseLine(parser_mediator, structure)
    else:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

  def VerifyStructure(self, parser_mediator, lines):
    """Verify that this file is a GDrive Sync log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      structure = self._GDS_LINE.parseString(lines)
    except pyparsing.ParseException as e:
      logging.debug('Not a GDrive Sync log file: %s' % e)
      return False

    try:
      dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=structure.header_date_time)
    except ValueError:
      logging.debug(
          'Not a GDrive Sync log file, invalid date and time: {0!s}'.format(
              structure.header_date_time))
      return False

    return True


manager.ParsersManager.RegisterParser(GDriveSyncLogParser)
