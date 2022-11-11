# -*- coding: utf-8 -*-
"""Parsers for MacOS fseventsd files.

Also see:
  https://github.com/libyal/dtformats/blob/main/documentation/MacOS%20File%20System%20Events%20Disk%20Log%20Stream%20format.asciidoc
"""

import os

from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class FseventsdEventData(events.EventData):
  """MacOS file system event (fseventsd) event data

  Attributes:
    event_identifier (int): the record event identifier.
    file_entry_modification_time (dfdatetime.DateTimeValues): file entry
        last modification date and time.
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
    self.file_entry_modification_time = None
    self.flags = None
    self.node_identifier = None
    self.path = None


class FseventsdParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parser for fseventsd files.

  This parser supports both version 1 and version 2 fseventsd files.
  """

  NAME = 'fseventsd'
  DATA_FORMAT = 'MacOS File System Events Disk Log Stream (fseventsd) file'

  # The version 1 format was used in Mac OS X 10.5 (Leopard) through macOS 10.12
  # (Sierra).
  _DLS_V1_SIGNATURE = b'1SLD'

  # The version 2 format was introduced in MacOS High Sierra (10.13).
  _DLS_V2_SIGNATURE = b'2SLD'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'fseventsd.yaml')

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

  def _ParseDLSPageHeader(self, file_object, page_offset):
    """Parses a DLS page header from a file-like object.

    Args:
      file_object (file): file-like object to read the header from.
      page_offset (int): offset of the start of the page header, relative
          to the start of the file.

    Returns:
      tuple: containing:

        dls_page_header: parsed record structure.
        int: header size.

    Raises:
      ParseError: when the header cannot be parsed.
    """
    page_header_map = self._GetDataTypeMap('dls_page_header')

    try:
      page_header, page_size = self._ReadStructureFromFileObject(
          file_object, page_offset, page_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse page header at offset: 0x{0:08x} '
          'with error: {1!s}'.format(page_offset, exception))

    return page_header, page_size

  def _BuildEventData(self, record):
    """Builds an FseventsdData object from a parsed structure.

    Args:
      record (dls_record_v1|dls_record_v2): parsed record structure.

    Returns:
      FseventsdEventData: event data attribute container.
    """
    event_data = FseventsdEventData()
    event_data.path = record.path
    event_data.flags = record.event_flags
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
    parent_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        gzip_file_entry.path_spec.parent)
    if not parent_file_entry:
      return None

    return parent_file_entry.modification_time

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an fseventsd file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the header cannot be parsed.
    """
    page_header_map = self._GetDataTypeMap('dls_page_header')

    try:
      page_header, file_offset = self._ReadStructureFromFileObject(
          file_object, 0, page_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          'Unable to parse page header with error: {0!s}'.format(
              exception))

    current_page_end = page_header.page_size

    file_entry = parser_mediator.GetFileEntry()
    date_time = self._GetParentModificationTime(file_entry)

    file_size = file_object.get_size()
    while file_offset < file_size:
      if file_offset >= current_page_end:
        try:
          page_header, header_size = self._ParseDLSPageHeader(
              file_object, file_offset)
        except errors.ParseError as exception:
          parser_mediator.ProduceExtractionWarning(
              'Unable to parse page header with error: {0!s}'.format(
                  exception))
          break

        current_page_end += page_header.page_size
        file_offset += header_size
        continue

      if page_header.signature == self._DLS_V1_SIGNATURE:
        record_map = self._GetDataTypeMap('dls_record_v1')
      else:
        record_map = self._GetDataTypeMap('dls_record_v2')

      try:
        record, record_length = self._ReadStructureFromFileObject(
            file_object, file_offset, record_map)
        file_offset += record_length
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning(
            'Unable to parse page record with error: {0!s}'.format(
                exception))
        break

      event_data = self._BuildEventData(record)
      event_data.file_entry_modification_time = date_time

      parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(FseventsdParser)
