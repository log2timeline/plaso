# -*- coding: utf-8 -*-
"""Parser for fseventsd files."""

from __future__ import unicode_literals

import construct

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.lib import errors
from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class FSEventsdEventData(events.EventData):
  """FSEventsd event data.

  Attributes:
    offset (int):
    path (str):
    flags (int):
    event_id (int):
  """

  DATA_TYPE = 'macos:fseventsd:record'

  def __init__(self):
    super(FSEventsdEventData, self).__init__()
    # Offset of the record within the fsevent file
    self.offset = None
    self.path = None
    self.event_id = None
    self.flags = None


class FSEventsdParser(interface.FileObjectParser):
  """FSEventsd file parser.

  Refer to https://nicoleibrahim.com/apple-fsevents-forensics/ for details.
  """

  _SLD_HEADER = construct.Struct(
      'sld_header',
      construct.Const(construct.String('signature', 4), b'1SLD'),
      construct.Bytes('unknown', 4),
      construct.ULInt32('page_size'),
  )

  _SLD_RECORD = construct.Struct(
      'sld_record',
      construct.CString('filename'),
      construct.ULInt32('event_id'),
      construct.Bytes('flags', 8),
  )

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'1SLD', offset=0)
    return format_specification

  def _ParseSLDHeader(self, file_object):
    """Parses a SLD header from a stream.

    Raises:
      UnableToParseFile: when the header cannot be parsed.
    """
    try:
      sld_header = self._SLD_HEADER.parse_stream(file_object)
    except construct.ConstructError as exception:
      raise errors.UnableToParseFile(
          'Unable to parse SLD header with error: {0:s}'.format(exception))
    return sld_header

  def _BuildEventData(self, record):
    """Builds an FSEventsData object from a parsed structure.

    Args:
      record (construct.Container): parsed record structure.

    Returns:
      FSEventsdEventData: event data attribute container.
    """
    data = FSEventsdEventData()
    data.path = record.filename
    data.flags = record.flags
    data.event_id = record.event_id
    return data

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a fseventsd file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the header cannot be parsed.
    """
    header = self._ParseSLDHeader(file_object)
    current_page_end = header.page_size
    file_entry = parser_mediator.GetFileEntry()
    stat_object = file_entry.GetStat()
    timestamp = getattr(stat_object, 'mtime', None)
    # TODO: Change this to use a more precise time definition after
    # https://github.com/log2timeline/dfdatetime/issues/65 is resolved.
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp)
      timestamp_description = definitions.TIME_DESCRIPTION_RECORDED
    else:
      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      timestamp_description = definitions.TIME_DESCRIPTION_NOT_A_TIME
    event = time_events.DateTimeValuesEvent(date_time, timestamp_description)

    while file_object.get_offset() < file_object.get_size():
      if file_object.get_offset() >= current_page_end:
        header = self._ParseSLDHeader(file_object)
        current_page_end += header.page_size
        continue
      record = self._SLD_RECORD.parse_stream(file_object)
      data = self._BuildEventData(record)
      parser_mediator.ProduceEventWithEventData(event, data)


manager.ParsersManager.RegisterParser(FSEventsdParser)
