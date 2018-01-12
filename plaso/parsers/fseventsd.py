# -*- coding: utf-8 -*-
"""Parsers for MacOS fseventsd files."""

from __future__ import unicode_literals

import logging

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
  """Fseventsd event data.

  Attributes:
    event_identifier (int): the record event id.
    flags (int): object type and event flags stored in the record.
    node_identifier (str): node identifier stored in the fseventsd record.
    offset (int): offset of the record in the fseventsd file.
    path (str): path recorded in the fseventsd record.
  """

  DATA_TYPE = 'macos:fseventsd:record'

  def __init__(self):
    """Initializes an Fseventsd event data."""
    super(FseventsdEventData, self).__init__()
    # Offset of the record within the fsevent file.
    self.event_identifier = None
    self.flags = None
    self.node_identifier = None
    self.offset = None
    self.path = None


class FseventsdParser(interface.FileObjectParser):
  """Superclass for fseventsd file parsers.

  Refer to http://nicoleibrahim.com/apple-fsevents-forensics/ for details.
  """

  # The version 1 format was used in Mac OS X 10.5 (Leopard) through macOS 10.12
  # (Sierra).

  _DLS_HEADER_V1 = construct.Struct(
      'dls_header_v1',
      construct.Const(construct.Bytes('signature', 4), b'1SLD'),
      construct.Padding(4),
      construct.ULInt32('page_size'))

  _DLS_RECORD_V1 = construct.Struct(
      'dls_record_v1',
      construct.CString('filename'),
      construct.ULInt32('event_identifier'),
      construct.Bytes('flags', 8))

  # The version 2 format was introduced in MacOS High Sierra (10.13)
  _DLS_HEADER_V2 = construct.Struct(
      'dls_header_v2',
      construct.Const(construct.Bytes('signature', 4), b'2SLD'),
      construct.Padding(4),
      construct.ULInt32('page_size'))

  _DLS_RECORD_V2 = construct.Struct(
      'dls_record_v2',
      construct.CString('filename'),
      construct.ULInt32('event_identifier'),
      construct.Bytes('flags', 8),
      construct.Bytes('node_identifier', 8))

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'1SLD', offset=0)
    format_specification.AddNewSignature(b'2SLD', offset=0)
    return format_specification


  def _ParseDLSHeader(self, file_object):
    """Parses a SLD header from a stream.

    Args:
      file_object (file): file-like object to read the header from.

    Returns:
      tuple: containing:
        int: the version of the header that was parsed, either 1 or 2.
        construct.Container: parsed record structure.

    Raises:
      UnableToParseFile: when the header cannot be parsed.
    """
    file_position = file_object.get_offset()
    headers = {1: self._DLS_HEADER_V1, 2: self._DLS_HEADER_V2}
    for version, header_type in headers.items():
      try:
        return version, header_type.parse_stream(file_object)
      except construct.ConstructError as exception:
        file_object.seek(file_position)
        logging.debug('Unable to parse DLS header with error: {0:s}'.format(
            exception))

    raise errors.UnableToParseFile('Unable to parse DLS header from file')

  def _BuildEventData(self, record):
    """Builds an FseventsdData object from a parsed structure.

    Args:
      record (construct.Container): parsed record structure.

    Returns:
      FseventsdEventData: event data attribute container.
    """
    data = FseventsdEventData()
    data.path = record.filename
    data.flags = record.flags
    data.event_identifier = record.event_identifier
    # Node identifier is only set in DLS V2 records.
    data.node_identifier = getattr(record, 'node_identifier', None)

    return data

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
      dfdatetime.DateTimeValues: time values, or None if not available.
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
    version, header = self._ParseDLSHeader(file_object)
    current_page_end = header.page_size
    file_entry = parser_mediator.GetFileEntry()
    date_time = self._GetParentModificationTime(file_entry)
    # TODO: Change this to use a more representative time definition after
    # https://github.com/log2timeline/dfdatetime/issues/65 is resolved.
    if date_time:
      timestamp_description = definitions.TIME_DESCRIPTION_RECORDED
    else:
      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      timestamp_description = definitions.TIME_DESCRIPTION_NOT_A_TIME
    event = time_events.DateTimeValuesEvent(date_time, timestamp_description)

    while file_object.get_offset() < file_object.get_size():
      if file_object.get_offset() >= current_page_end:
        version, header = self._ParseDLSHeader(file_object)
        current_page_end += header.page_size
        continue
      if version == 1:
        record = self._DLS_RECORD_V1.parse_stream(file_object)
      else:
        record = self._DLS_RECORD_V2.parse_stream(file_object)

      data = self._BuildEventData(record)
      parser_mediator.ProduceEventWithEventData(event, data)


manager.ParsersManager.RegisterParser(FseventsdParser)
