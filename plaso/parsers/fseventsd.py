# -*- coding: utf-8 -*-
"""Parsers for MacOS fseventsd files."""

from __future__ import unicode_literals

import construct

from dfdatetime import semantic_time as dfdatetime_semantic_time

from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class FseventsdEventData(events.EventData):
  """MacOS file system event (fseventsd) event data

  Attributes:
    event_identifier (int): the record event identifier.
    flags (int): flags stored in the record.
    node_identifier (int): file system node identifier related to the file
        system event.
    path (str): path recorded in the fseventsd record.
  """

  DATA_TYPE = 'macos:fseventsd:record'

  def __init__(self):
    """Initializes an Fseventsd event data."""
    super(FseventsdEventData, self).__init__(data_type=self.DATA_TYPE)
    self.event_identifier = None
    self.flags = None
    self.node_identifier = None
    self.path = None


class FseventsdParser(interface.FileObjectParser):
  """Parser for fseventsd files.

  This parser supports both version 1 and version 2 fseventsd files.
  Refer to http://nicoleibrahim.com/apple-fsevents-forensics/ for details.
  """

  NAME = 'fsevents'

  DESCRIPTION = 'Parser for fseventsd files.'

  # The version 1 format was used in Mac OS X 10.5 (Leopard) through macOS 10.12
  # (Sierra).
  _DLS_V1_SIGNATURE = b'1SLD'
  _DLS_RECORD_V1 = construct.Struct(
      'dls_record_v1',
      construct.CString('path'),
      construct.ULInt64('event_identifier'),
      construct.UBInt32('flags'))

  # The version 2 format was introduced in MacOS High Sierra (10.13).
  _DLS_V2_SIGNATURE = b'2SLD'
  _DLS_RECORD_V2 = construct.Struct(
      'dls_record_v2',
      construct.CString('path'),
      construct.ULInt64('event_identifier'),
      construct.UBInt32('flags'),
      construct.ULInt64('node_identifier'))

  _DLS_SIGNATURES = [_DLS_V1_SIGNATURE, _DLS_V2_SIGNATURE]

  _DLS_PAGE_HEADER = construct.Struct(
      'dls_header',
      construct.OneOf(construct.Bytes('signature', 4), _DLS_SIGNATURES),
      construct.Padding(4),
      construct.ULInt32('page_size'))

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(cls._DLS_V1_SIGNATURE, offset=0)
    format_specification.AddNewSignature(cls._DLS_V2_SIGNATURE, offset=0)
    return format_specification

  def _ParseDLSPageHeader(self, file_object):
    """Parses a DLS page header from a file-like object.

    Args:
      file_object (file): file-like object to read the header from.

    Returns:
      construct.Container: parsed record structure.

    Raises:
      UnableToParseFile: when the header cannot be parsed.
    """
    try:
      return self._DLS_PAGE_HEADER.parse_stream(file_object)
    except construct.ConstructError:
      raise errors.UnableToParseFile('Unable to parse DLS header from file')

  def _BuildEventData(self, record):
    """Builds an FseventsdData object from a parsed structure.

    Args:
      record (construct.Container): parsed record structure.

    Returns:
      FseventsdEventData: event data attribute container.
    """
    event_data = FseventsdEventData()
    event_data.path = record.path
    event_data.flags = record.flags
    event_data.event_identifier = record.event_identifier
    # Node identifier is only set in DLS V2 records.
    event_data.node_identifier = getattr(record, 'node_identifier', None)

    return event_data

  def _GetParentModificationTime(self, gzip_file_entry):
    """Retrieves the modification time of the file entry's parent file.

    Note that this retrieves the time from the file entry of the parent of the
    gzip file entry's path spec, which is different from trying to retrieve it
    from the gzip file entry's parent file entry.

    It would be preferable to retrieve the modification time from the metadata
    in the gzip file itself, but it appears to not be set when the file is
    written by fseventsd.

    Args:
      gzip_file_entry (dfvfs.FileEntry): file entry of the gzip file containing
          the fseventsd data.

    Returns:
      dfdatetime.DateTimeValues: parent modification time, or None if not
          available.
    """
    parent_path_spec = gzip_file_entry.path_spec.parent
    parent_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        parent_path_spec)
    time_values = parent_file_entry.modification_time
    return time_values

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an fseventsd file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the header cannot be parsed.
    """
    page_header = self._ParseDLSPageHeader(file_object)
    current_page_end = page_header.page_size
    file_entry = parser_mediator.GetFileEntry()
    date_time = self._GetParentModificationTime(file_entry)
    # TODO: Change this to use a more representative time definition (time span)
    # when https://github.com/log2timeline/dfdatetime/issues/65 is resolved.
    if date_time:
      timestamp_description = definitions.TIME_DESCRIPTION_RECORDED
    else:
      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      timestamp_description = definitions.TIME_DESCRIPTION_NOT_A_TIME
    event = time_events.DateTimeValuesEvent(date_time, timestamp_description)

    while file_object.get_offset() < file_object.get_size():
      if file_object.get_offset() >= current_page_end:
        page_header = self._ParseDLSPageHeader(file_object)
        current_page_end += page_header.page_size
        continue
      if page_header.signature == self._DLS_V1_SIGNATURE:
        record = self._DLS_RECORD_V1.parse_stream(file_object)
      else:
        record = self._DLS_RECORD_V2.parse_stream(file_object)

      event_data = self._BuildEventData(record)
      parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(FseventsdParser)
