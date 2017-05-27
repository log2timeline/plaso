# -*- coding: utf-8 -*-
"""Parser for Windows Restore Point (rp.log) files."""

import os

import construct

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


class RestorePointEventData(events.EventData):
  """Windows Restore Point event data.

  Attributes:
    description (str): description.
    restore_point_event_type (str): restore point event type.
    restore_point_type (str): restore point type.
    sequence_number (str): sequence number.
  """

  DATA_TYPE = u'windows:restore_point:info'

  def __init__(self):
    """Initializes Windows Recycle Bin event data."""
    super(RestorePointEventData, self).__init__(data_type=self.DATA_TYPE)
    self.description = None
    self.restore_point_event_type = None
    self.restore_point_type = None
    self.sequence_number = None


class RestorePointLogParser(interface.FileObjectParser):
  """A parser for Windows Restore Point (rp.log) files."""

  NAME = u'rplog'
  DESCRIPTION = u'Parser for Windows Restore Point (rp.log) files.'

  FILTERS = frozenset([
      interface.FileNameFileEntryFilter(u'rp.log')])

  _FILE_HEADER_STRUCT = construct.Struct(
      u'file_header',
      construct.ULInt32(u'event_type'),
      construct.ULInt32(u'restore_point_type'),
      construct.ULInt64(u'sequence_number'),
      construct.RepeatUntil(
          lambda character, ctx: character == b'\x00\x00',
          construct.Field(u'description', 2)))

  _FILE_FOOTER_STRUCT = construct.Struct(
      u'file_footer',
      construct.ULInt64(u'creation_time'))

  def ParseFileObject(self, parser_mediator, file_object, **unused_kwargs):
    """Parses a Windows Restore Point (rp.log) log file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    try:
      file_header_struct = self._FILE_HEADER_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError(
          u'unable to parse file header with error: {0:s}'.format(exception))
      return

    file_object.seek(-8, os.SEEK_END)

    try:
      file_footer_struct = self._FILE_FOOTER_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError(
          u'unable to parse file footer with error: {0:s}'.format(exception))
      return

    try:
      description = b''.join(file_header_struct.description)
      # The struct includes the end-of-string character that we need
      # to strip off.
      description = description.decode(u'utf16')[:-1]
    except UnicodeDecodeError as exception:
      description = u''
      parser_mediator.ProduceExtractionError((
          u'unable to decode description UTF-16 stream with error: '
          u'{0:s}').format(exception))

    if file_footer_struct.creation_time == 0:
      date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
    else:
      date_time = dfdatetime_filetime.Filetime(
          timestamp=file_footer_struct.creation_time)

    event_data = RestorePointEventData()
    event_data.description = description
    event_data.restore_point_event_type = file_header_struct.event_type
    event_data.restore_point_type = file_header_struct.restore_point_type
    event_data.sequence_number = file_header_struct.sequence_number

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(RestorePointLogParser)
