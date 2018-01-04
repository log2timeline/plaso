# -*- coding: utf-8 -*-
"""Parsers for MacOS fseventsd files."""

from __future__ import unicode_literals

import construct

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import semantic_time as dfdatetime_semantic_time

from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import errors
from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class FseventsdEventData(events.EventData):
  """Fseventsd event data.

  Attributes:
    offset (int): offset of the record in the fseventsd file.
    path (str): path recorded in the fseventsd record.
    flags (int): object type and event flags stored in the record.
    event_id (int): the record event id.
  """

  DATA_TYPE = 'macos:fseventsd:record'

  def __init__(self):
    super(FseventsdEventData, self).__init__()
    # Offset of the record within the fsevent file
    self.offset = None
    self.path = None
    self.event_id = None
    self.flags = None
    self.node_id = None


class BaseFseventsdParser(interface.FileObjectParser):
  """Superclass for fseventsd file parsers.

  Refer to https://nicoleibrahim.com/apple-fsevents-forensics/ for details.
  """

  # Struct definition for a fseventsd section header.
  # Must be overridden in subclass.
  _SLD_HEADER = None

  # Struct definition for a single fseventsd event record.
  # Must be overridden in subclass.
  _SLD_RECORD = None

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
    """Builds an FseventsData object from a parsed structure.

    Args:
      record (construct.Container): parsed record structure.

    Returns:
      FseventsdEventData: event data attribute container.
    """
    data = FseventsdEventData()
    data.path = record.filename
    data.flags = record.flags
    data.event_id = record.event_id
    data.node_id = getattr(record, 'node_id', None)

    return data

  def _GetTimestamp(self, gzip_file_entry):
    """Retrieves the modification time of the file entry's parent file.

    Note that this retrieves the time from the file entry of the parent of the
    gzip file entry's path spec, which is different from trying to retrieve it
    from the gzip file entry's parent file entry.

    It would be preferable to retrieve the modification time from the metadata
    in the gzip file itself, but it appears to not be set when the file is
    written by fseventsd.

    Returns:
      float: posix timestamp, or None if none modification time is available.
    """
    parent_path_spec = gzip_file_entry.path_spec.parent
    parent_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        parent_path_spec)
    stat_object = parent_file_entry.GetStat()
    timestamp = getattr(stat_object, 'mtime', None)
    return timestamp

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
    timestamp = self._GetTimestamp(file_entry)
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


class FseventsdParserV1(BaseFseventsdParser):
  """Parser for format version 1 fseventsd files.

  The version 1 format was used in Mac OS X 10.5 (Leopard) through macOS 10.12
  (Sierra).

  """

  NAME = 'fseventsv1'

  DESCRIPTION = 'Parser for pre-macOS 10.13 fseventsd files'

  _SLD_HEADER = construct.Struct(
      'sld_header',
      construct.Const(construct.String('signature', 4), b'1SLD'),
      construct.Bytes('unknown', 4),
      construct.ULInt32('page_size'))

  _SLD_RECORD = construct.Struct(
      'sld_record',
      construct.CString('filename'),
      construct.ULInt32('event_id'),
      construct.Bytes('flags', 8))

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'1SLD', offset=0)
    return format_specification


class FseventsdParserV2(BaseFseventsdParser):
  """Parser for format version 2 Fseventsd files.

  The version 2 format was introduced in MacOS High Sierra (10.13).
  """

  NAME = 'fseventsv2'

  DESCRIPTION = 'Parser for post-macOS 10.13 fseventsd files'

  _SLD_HEADER = construct.Struct(
      'sld_header',
      construct.Const(construct.String('signature', 4), b'2SLD'),
      construct.Bytes('unknown', 4),
      construct.ULInt32('page_size'))

  _SLD_RECORD = construct.Struct(
      'sld_record',
      construct.CString('filename'),
      construct.ULInt32('event_id'),
      construct.Bytes('flags', 8),
      construct.Bytes('node_id', 8))

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'2SLD', offset=0)
    return format_specification


manager.ParsersManager.RegisterParsers([FseventsdParserV1, FseventsdParserV2])
