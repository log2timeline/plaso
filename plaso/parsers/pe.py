# -*- coding: utf-8 -*-
"""A parser for Portable Executable (PE) files."""

import os

import pefile

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfvfs.helpers import data_slice as dfvfs_data_slice

from plaso.containers import artifacts
from plaso.containers import events
from plaso.containers import time_events
from plaso.helpers.windows import languages
from plaso.helpers.windows import resource_files
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class PEEventData(events.EventData):
  """Portable Executable (PE) event data.

  Attributes:
    dll_name (str): name of an imported DLL.
    imphash (str): "Import Hash" of the pe file the event relates to. Also see:
        https://www.mandiant.com/resources/tracking-malware-import-hashing
    pe_attribute (str): attribute of PE file the event relates to.
    pe_type (str): type of PE file the event relates to.
    section_names (list[str]): names of the sections in the PE file.
  """

  DATA_TYPE = 'pe'

  def __init__(self):
    """Initializes event data."""
    super(PEEventData, self).__init__(data_type=self.DATA_TYPE)
    self.dll_name = None
    self.imphash = None
    self.pe_attribute = None
    self.pe_type = None
    self.section_names = None


class PEParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parser for Portable Executable (PE) files."""

  NAME = 'pe'
  DATA_FORMAT = 'Portable Executable (PE) file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'pe_resources.yaml')

  _PE_DIRECTORIES = [
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']]

  def __init__(self):
    """Initializes a PE parser."""
    super(PEParser, self).__init__()
    self._resouce_file_helper = resource_files.WindowsResourceFileHelper

  def _GetPEType(self, pefile_object):
    """Retrieves the type of the PE file.

    Args:
      pefile_object (pefile.PE): pefile object.

    Returns:
      str: type of the Portable Executable (PE) file.
    """
    if pefile_object.is_dll():
      return 'Dynamic Link Library (DLL)'
    if pefile_object.is_exe():
      return 'Executable (EXE)'
    if pefile_object.is_driver():
      return 'Driver (SYS)'
    return 'Unknown PE type'

  def _GetSectionNames(self, pefile_object):
    """Retrieves all PE section names.

    Args:
      pefile_object (pefile.PE): pefile object.

    Returns:
      list[str]: names of the sections.
    """
    section_names = []
    for section in pefile_object.sections:
      section_name = getattr(section, 'Name', b'')
      # Ensure the name is decoded correctly.
      try:
        section_name = '{0:s}'.format(section_name.decode('unicode_escape'))
      except UnicodeDecodeError:
        section_name = '{0:s}'.format(repr(section_name))
      section_names.append(section_name)

    return section_names

  def _ParseLoadConfigurationTable(
      self, parser_mediator, pefile_object, event_data):
    """Parses the load configuration table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      pefile_object (pefile.PE): pefile object.
      event_data (PEEventData): event data.
    """
    load_configuration_table = getattr(
        pefile_object, 'DIRECTORY_ENTRY_LOAD_CONFIG', None)
    if not load_configuration_table:
      return

    timestamp = getattr(load_configuration_table.struct, 'TimeDateStamp', None)
    if timestamp:
      event_data.pe_attribute = 'DIRECTORY_ENTRY_LOAD_CONFIG'

      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseDelayImportTable(self, parser_mediator, pefile_object, event_data):
    """Parses the delay import table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      pefile_object (pefile.PE): pefile object.
      event_data (PEEventData): event data.
    """
    delay_import_table = getattr(
        pefile_object, 'DIRECTORY_ENTRY_DELAY_IMPORT', None)
    if not delay_import_table:
      return

    for table_entry in delay_import_table:
      timestamp = getattr(table_entry.struct, 'dwTimeStamp', 0)
      if not timestamp:
        continue

      dll_name = getattr(table_entry, 'dll', '')
      try:
        dll_name = dll_name.decode('ascii')
      except UnicodeDecodeError:
        dll_name = dll_name.decode('ascii', errors='replace')
      if not dll_name:
        dll_name = '<NO DLL NAME>'

      event_data.pe_attribute = 'DIRECTORY_ENTRY_DELAY_IMPORT'
      event_data.dll_name = dll_name

      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    event_data.dll_name = None

  def _ParseExportTable(self, parser_mediator, pefile_object, event_data):
    """Parses the export table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      pefile_object (pefile.PE): pefile object.
      event_data (PEEventData): event data.
    """
    export_table = getattr(pefile_object, 'DIRECTORY_ENTRY_EXPORT', None)
    if not export_table:
      return

    timestamp = getattr(export_table.struct, 'TimeDateStamp', 0)
    if not timestamp:
      return

    dll_name = getattr(export_table, 'name', '')
    try:
      dll_name = dll_name.decode('ascii')
    except UnicodeDecodeError:
      dll_name = dll_name.decode('ascii', errors='replace')
    if not dll_name:
      dll_name = '<NO DLL NAME>'

    event_data.pe_attribute = 'DIRECTORY_ENTRY_EXPORT'
    event_data.dll_name = dll_name

    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    event_data.dll_name = None

  def _ParseImportTable(self, parser_mediator, pefile_object, event_data):
    """Parses the import table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      pefile_object (pefile.PE): pefile object.
      event_data (PEEventData): event data.
    """
    import_table = getattr(pefile_object, 'DIRECTORY_ENTRY_IMPORT', None)
    if not import_table:
      return

    for table_entry in import_table:
      timestamp = getattr(table_entry.struct, 'TimeDateStamp', 0)
      if not timestamp:
        continue

      dll_name = getattr(table_entry, 'dll', '')
      try:
        dll_name = dll_name.decode('ascii')
      except UnicodeDecodeError:
        dll_name = dll_name.decode('ascii', errors='replace')
      if not dll_name:
        dll_name = '<NO DLL NAME>'

      event_data.pe_attribute = 'DIRECTORY_ENTRY_IMPORT'
      event_data.dll_name = dll_name

      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    event_data.dll_name = None

  def _ParseResourceSection(self, parser_mediator, pefile_object, event_data):
    """Parses the resource section.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      pefile_object (pefile.PE): pefile object.
      event_data (PEEventData): event data.
    """
    resources = getattr(pefile_object, 'DIRECTORY_ENTRY_RESOURCE', None)
    if not resources:
      return

    message_table_resource = None
    for resource in resources.entries:
      if resource.id == 11:
        message_table_resource = resource

      timestamp = getattr(resource.directory, 'TimeDateStamp', None)
      if timestamp:
        event_data.pe_attribute = 'DIRECTORY_ENTRY_RESOURCE: {0!s}'.format(
            resource.id)

        date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    if not parser_mediator.extract_winevt_resources:
      return

    if (not message_table_resource or not message_table_resource.directory or
        not message_table_resource.directory.entries or
        not message_table_resource.directory.entries[0].directory):
      return

    # Only extract message strings from EventLog message files.
    message_file = parser_mediator.GetWindowsEventLogMessageFile()
    if not message_file:
      return

    for entry in message_table_resource.directory.entries[0].directory.entries:
      language_tag = languages.WindowsLanguageHelper.GetLanguageTagForLCID(
          entry.id)
      if not language_tag or language_tag.lower() != parser_mediator.language:
        continue

      parser_mediator.AddWindowsEventLogMessageFile(message_file)

      # TODO: use file offset?
      offset = getattr(entry.data.struct, 'OffsetToData', None)
      size = getattr(entry.data.struct, 'Size', None)
      data = pefile_object.get_memory_mapped_image()[offset:offset + size]

      self._ParseMessageTable(parser_mediator, message_file, entry.id, data)

  def _ParseMessageTable(
      self, parser_mediator, message_file, language_identifier, data):
    """Parses a message table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      message_file (WindowsEventLogMessageFileArtifact): Windows EventLog
          message file.
      language_identifier (int): language indentifier (LCID).
      data (bytes): message table data.

    Raises:
      ParseError: when the message table cannot be parsed.
    """
    message_file_identifier = message_file.GetIdentifier()

    message_table_header_map = self._GetDataTypeMap('message_table_header')
    message_table_entry_map = self._GetDataTypeMap('message_table_entry')
    message_table_string_map = self._GetDataTypeMap('message_table_string')

    data_offset = 0

    try:
      message_table_header = self._ReadStructureFromByteStream(
          data, data_offset, message_table_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to read message table header with error: {0!s}'.format(
              exception))

    data_offset += message_table_header_map.GetByteSize()

    for entry_index in range(message_table_header.number_of_entries):
      try:
        message_table_entry = self._ReadStructureFromByteStream(
            data[data_offset:], data_offset, message_table_entry_map)
      except (ValueError, errors.ParseError) as exception:
        raise errors.ParseError((
            'Unable to read message table entry: {0:d} at offset: {1:d} with '
            'error: {2!s}').format(entry_index, data_offset, exception))

      data_offset += message_table_entry_map.GetByteSize()

      message_identifier = message_table_entry.first_message_identifier
      string_offset = message_table_entry.first_string_offset
      while message_identifier <= message_table_entry.last_message_identifier:
        try:
          message_table_string = self._ReadStructureFromByteStream(
              data[string_offset:], string_offset, message_table_string_map)
        except (ValueError, errors.ParseError) as exception:
          raise errors.ParseError((
              'Unable to read message table string: 0x{0:08x} at offset: {1:d} '
              'with error: {2!s}').format(
                  message_identifier, string_offset, exception))

        if message_table_string.flags & 0x01:
          string_encoding = 'utf-16-le'
        else:
          string_encoding = parser_mediator.codepage

        try:
          string = message_table_string.data.decode(string_encoding)
        except UnicodeDecodeError:
          raise errors.ParseError((
              'Unable to decode {0:s} encoded message table string: 0x{1:08x} '
              'at offset: {2:d} with error: {3!s}').format(
                  string_encoding, message_identifier, string_offset,
                  exception))

        string_offset += message_table_string.data_size

        _, alignment_padding = divmod(string_offset, 4)
        if alignment_padding > 0:
          string_offset += 4 - alignment_padding

        string = self._resouce_file_helper.FormatMessageStringInPEP3101(string)

        message_string = artifacts.WindowsEventLogMessageStringArtifact(
            language_identifier=language_identifier,
            message_identifier=message_identifier, string=string)
        message_string.SetMessageFileIdentifier(message_file_identifier)
        parser_mediator.AddWindowsEventLogMessageString(message_string)

        message_identifier += 1

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'MZ', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Portable Executable (PE) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    pe_data_slice = dfvfs_data_slice.DataSlice(file_object)
    try:
      pefile_object = pefile.PE(data=pe_data_slice, fast_load=True)
      pefile_object.parse_data_directories(directories=self._PE_DIRECTORIES)
    except Exception as exception:
      raise errors.UnableToParseFile(
          'Unable to read PE file with error: {0!s}'.format(exception))

    event_data = PEEventData()
    # Note that the result of get_imphash() is an empty string if there is no
    # import hash.
    event_data.imphash = pefile_object.get_imphash() or None
    event_data.pe_type = self._GetPEType(pefile_object)
    event_data.section_names = self._GetSectionNames(pefile_object)

    timestamp = getattr(pefile_object.FILE_HEADER, 'TimeDateStamp', None)
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    else:
      date_time = dfdatetime_semantic_time.NotSet()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    self._ParseExportTable(parser_mediator, pefile_object, event_data)

    self._ParseImportTable(parser_mediator, pefile_object, event_data)

    self._ParseLoadConfigurationTable(
        parser_mediator, pefile_object, event_data)

    self._ParseDelayImportTable(parser_mediator, pefile_object, event_data)

    self._ParseResourceSection(parser_mediator, pefile_object, event_data)


manager.ParsersManager.RegisterParser(PEParser)
