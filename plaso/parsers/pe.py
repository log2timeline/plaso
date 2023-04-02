# -*- coding: utf-8 -*-
"""A parser for Portable Executable (PE) files.

Also see:
  https://www.mandiant.com/resources/blog/tracking-malware-import-hashing
"""

import os

import pefile

from dfdatetime import posix_time as dfdatetime_posix_time
from dfvfs.helpers import data_slice as dfvfs_data_slice
from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import artifacts
from plaso.containers import events
from plaso.helpers.windows import languages
from plaso.helpers.windows import resource_files
from plaso.lib import errors
from plaso.lib import dtfabric_helper
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class PEDLLImportEventData(events.EventData):
  """Portable Executable (PE) DLL import event data.

  Attributes:
    delayed_import (bool): True if the DLL is imported at run-time.
    modification_time (dfdatetime.DateTimeValues): last modification date and
        time.
    name (str): name of the imported DLL.
  """

  DATA_TYPE = 'pe_coff:dll_import'

  def __init__(self):
    """Initializes event data."""
    super(PEDLLImportEventData, self).__init__(data_type=self.DATA_TYPE)
    self.delayed_import = None
    self.modification_time = None
    self.name = None


class PEFileEventData(events.EventData):
  """Portable Executable (PE) file event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): creation date and time.
    export_dll_name (str): name of the exported DLL.
    export_table_modification_time (dfdatetime.DateTimeValues): export table
        last modification date and time.
    imphash (str): "Import Hash" of the Portable Executable (PE) file.
    load_configuration_table_modification_time (dfdatetime.DateTimeValues):
        load configuration table last modification date and time.
    pe_type (str): type of Portable Executable (PE) file.
    section_names (list[str]): names of the sections in the Portable Executable
        (PE) file.
  """

  DATA_TYPE = 'pe_coff:file'

  def __init__(self):
    """Initializes event data."""
    super(PEFileEventData, self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.export_dll_name = None
    self.export_table_modification_time = None
    self.imphash = None
    self.load_configuration_table_modification_time = None
    self.pe_type = None
    self.section_names = None


class PEResourceEventData(events.EventData):
  """Portable Executable (PE) resource event data.

  Attributes:
    identifier (int): identifier of the resource.
    modification_time (dfdatetime.DateTimeValues): last modification date and
        time.
    name (str): name of the resource.
  """

  DATA_TYPE = 'pe_coff:resource'

  def __init__(self):
    """Initializes event data."""
    super(PEResourceEventData, self).__init__(data_type=self.DATA_TYPE)
    self.identifier = None
    self.modification_time = None
    self.name = None


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
    self._resource_file_helper = resource_files.WindowsResourceFileHelper

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

  def _ParseLoadConfigurationTable(self, pefile_object, event_data):
    """Parses the load configuration table.

    Args:
      pefile_object (pefile.PE): pefile object.
      event_data (PEFileEventData): event data.
    """
    load_configuration_table = getattr(
        pefile_object, 'DIRECTORY_ENTRY_LOAD_CONFIG', None)
    if not load_configuration_table:
      return

    timestamp = getattr(load_configuration_table.struct, 'TimeDateStamp', None)
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event_data.load_configuration_table_modification_time = date_time

  def _ParseDelayImportTable(self, parser_mediator, pefile_object):
    """Parses the delay import table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      pefile_object (pefile.PE): pefile object.
    """
    delay_import_table = getattr(
        pefile_object, 'DIRECTORY_ENTRY_DELAY_IMPORT', None)
    if not delay_import_table:
      return

    for table_entry in delay_import_table:
      timestamp = getattr(table_entry.struct, 'dwTimeStamp', None)
      if not timestamp:
        continue

      dll_name = getattr(table_entry, 'dll', '')
      try:
        dll_name = dll_name.decode('ascii')
      except UnicodeDecodeError:
        dll_name = dll_name.decode('ascii', errors='replace')

      event_data = PEDLLImportEventData()
      event_data.delayed_import = True
      event_data.name = dll_name or None

      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event_data.modification_time = date_time

      parser_mediator.ProduceEventData(event_data)

  def _ParseExportTable(self, pefile_object, event_data):
    """Parses the export table.

    Args:
      pefile_object (pefile.PE): pefile object.
      event_data (PEFileEventData): event data.
    """
    export_table = getattr(pefile_object, 'DIRECTORY_ENTRY_EXPORT', None)
    if not export_table:
      return

    dll_name = getattr(export_table, 'name', '')
    try:
      dll_name = dll_name.decode('ascii')
    except UnicodeDecodeError:
      dll_name = dll_name.decode('ascii', errors='replace')

    event_data.export_dll_name = dll_name or None

    timestamp = getattr(export_table.struct, 'TimeDateStamp', None)
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event_data.export_table_modification_time = date_time

  def _ParseImportTable(self, parser_mediator, pefile_object):
    """Parses the import table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      pefile_object (pefile.PE): pefile object.
    """
    import_table = getattr(pefile_object, 'DIRECTORY_ENTRY_IMPORT', None)
    if not import_table:
      return

    for table_entry in import_table:
      timestamp = getattr(table_entry.struct, 'TimeDateStamp', None)
      if not timestamp:
        continue

      dll_name = getattr(table_entry, 'dll', '')
      try:
        dll_name = dll_name.decode('ascii')
      except UnicodeDecodeError:
        dll_name = dll_name.decode('ascii', errors='replace')

      event_data = PEDLLImportEventData()
      event_data.delayed_import = False
      event_data.name = dll_name or None

      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event_data.modification_time = date_time

      parser_mediator.ProduceEventData(event_data)

  def _ParseResourceSection(self, parser_mediator, pefile_object):
    """Parses the resource section.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      pefile_object (pefile.PE): pefile object.
    """
    resources = getattr(pefile_object, 'DIRECTORY_ENTRY_RESOURCE', None)
    if not resources:
      return

    message_table_resource = None
    winevt_template_resource = None
    for resource in resources.entries:
      if resource.name:
        resource_name = str(resource.name)
      else:
        resource_name = None

      timestamp = getattr(resource.directory, 'TimeDateStamp', None)
      if timestamp:
        event_data = PEResourceEventData()
        event_data.identifier = resource.id
        event_data.name = resource_name

        date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
        event_data.modification_time = date_time

        parser_mediator.ProduceEventData(event_data)

      # Only extract message strings from the first message table resource.
      if resource.id == 11 and not message_table_resource:
        message_table_resource = resource

      # Need to cast resource.name name to a string since it is of type
      # pefile.UnicodeStringWrapperPostProcessor and would fail the comparison
      # with 'WEVT_TEMPLATE' otherwise.
      elif resource_name == 'WEVT_TEMPLATE' and not winevt_template_resource:
        winevt_template_resource = resource

    if parser_mediator.extract_winevt_resources:
      # Only extract message strings from EventLog message files.
      message_file = parser_mediator.GetWindowsEventLogMessageFile()
      if message_file:
        parser_mediator.AddWindowsEventLogMessageFile(message_file)

        if message_table_resource:
          self._ParseMessageTableResource(
              parser_mediator, pefile_object, message_file,
              message_table_resource)

        if winevt_template_resource:
          self._ParseWevtTemplateResource(
              parser_mediator, pefile_object, message_file,
              winevt_template_resource)

  def _ParseMessageTable(
      self, parser_mediator, message_file, language_identifier, data):
    """Parses a message table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      message_file (WindowsEventLogMessageFileArtifact): Windows EventLog
          message file.
      language_identifier (int): language identifier (LCID).
      data (bytes): message table data.

    Raises:
      ParseError: when the message table cannot be parsed.
    """
    message_file_identifier = message_file.GetIdentifier()

    message_table_header_map = self._GetDataTypeMap('message_table_header')
    message_table_entry_map = self._GetDataTypeMap('message_table_entry')
    message_table_string_map = self._GetDataTypeMap('message_table_string')

    data_offset = 0

    context = dtfabric_data_maps.DataTypeMapContext()

    try:
      message_table_header = self._ReadStructureFromByteStream(
          data, data_offset, message_table_header_map, context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to read message table header with error: {0!s}'.format(
              exception))

    data_offset += context.byte_size

    for entry_index in range(message_table_header.number_of_entries):
      context = dtfabric_data_maps.DataTypeMapContext()

      try:
        message_table_entry = self._ReadStructureFromByteStream(
            data[data_offset:], data_offset, message_table_entry_map,
            context=context)
      except (ValueError, errors.ParseError) as exception:
        raise errors.ParseError((
            'Unable to read message table entry: {0:d} at offset: {1:d} with '
            'error: {2!s}').format(entry_index, data_offset, exception))

      data_offset += context.byte_size

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
          string_encoding = parser_mediator.GetCodePage()

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

        string = self._resource_file_helper.FormatMessageStringInPEP3101(string)

        message_string = artifacts.WindowsEventLogMessageStringArtifact(
            language_identifier=language_identifier,
            message_identifier=message_identifier, string=string)
        message_string.SetMessageFileIdentifier(message_file_identifier)
        parser_mediator.AddWindowsEventLogMessageString(message_string)

        message_identifier += 1

  def _ParseMessageTableResource(
      self, parser_mediator, pefile_object, message_file,
      message_table_resource):
    """Parses a message table resource.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      pefile_object (pefile.PE): pefile object.
      message_file (WindowsEventLogMessageFileArtifact): Windows EventLog
          message file.
      message_table_resource (pefile.ResourceDirEntryData): message table
          resource.
    """
    if (not message_table_resource or not message_table_resource.directory or
        not message_table_resource.directory.entries or
        not message_table_resource.directory.entries[0].directory):
      return

    desired_language_tag = parser_mediator.GetLanguageTag().lower()

    for entry in message_table_resource.directory.entries[0].directory.entries:
      language_tag = languages.WindowsLanguageHelper.GetLanguageTagForLCID(
          entry.id)
      # TODO: add support for common language tag fallback.
      if not language_tag or language_tag.lower() != desired_language_tag:
        continue

      # TODO: use file offset?
      offset = getattr(entry.data.struct, 'OffsetToData', None)
      size = getattr(entry.data.struct, 'Size', None)
      data = pefile_object.get_memory_mapped_image()[offset:offset + size]

      self._ParseMessageTable(parser_mediator, message_file, entry.id, data)

  def _ParseWevtTemplate(self, parser_mediator, message_file, data):
    """Parses a WEVT_TEMPLATE.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      message_file (WindowsEventLogMessageFileArtifact): Windows EventLog
          message file.
      data (bytes): message table data.

    Raises:
      ParseError: when the message table cannot be parsed.
    """
    message_file_identifier = message_file.GetIdentifier()

    wevt_manifest_map = self._GetDataTypeMap('wevt_instrumentation_manifest')
    wevt_event_provider_map = self._GetDataTypeMap('wevt_event_provider')
    wevt_event_definitions_map = self._GetDataTypeMap('wevt_event_definitions')

    try:
      manifest = self._ReadStructureFromByteStream(
          data, 0, wevt_manifest_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to read WEVT instrumentation manifest with error: '
          '{0!s}').format(exception))

    for event_provider_descriptor in manifest.event_provider_descriptors:
      data_offset = event_provider_descriptor.data_offset
      try:
        event_provider = self._ReadStructureFromByteStream(
            data[data_offset:], data_offset, wevt_event_provider_map)
      except (ValueError, errors.ParseError) as exception:
        raise errors.ParseError(
            'Unable to read WEVT event provider with error: {0!s}'.format(
                exception))

      provider_identifier = '{{{0!s}}}'.format(
          event_provider_descriptor.provider_identifier)

      for provider_element_descriptor in (
          event_provider.provider_element_descriptors):
        data_offset = provider_element_descriptor.data_offset

        # Only extract event definitions.
        if data[data_offset:data_offset + 4] == b'EVNT':
          try:
            event_definitions = self._ReadStructureFromByteStream(
                data[data_offset:], data_offset, wevt_event_definitions_map)
          except (ValueError, errors.ParseError) as exception:
            raise errors.ParseError((
                'Unable to read WEVT event definitions with error: '
                '{0!s}').format(exception))
          for event_definition in event_definitions.definitions:
            event_definition = artifacts.WindowsWevtTemplateEvent(
                identifier=event_definition.identifier,
                message_identifier=event_definition.message_identifier,
                provider_identifier=provider_identifier,
                version=event_definition.version)
            event_definition.SetMessageFileIdentifier(message_file_identifier)

            parser_mediator.AddWindowsWevtTemplateEvent(event_definition)

  def _ParseWevtTemplateResource(
      self, parser_mediator, pefile_object, message_file,
      wevt_template_resource):
    """Parses a WEVT_TEMPLATE resource.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      pefile_object (pefile.PE): pefile object.
      message_file (WindowsEventLogMessageFileArtifact): Windows EventLog
          message file.
      wevt_template_resource (pefile.ResourceDirEntryData): WEVT_TEMPLATE
          resource.

    Raises:
      ParseError: when the message table cannot be parsed.
    """
    if (not wevt_template_resource or not wevt_template_resource.directory or
        not wevt_template_resource.directory.entries or
        not wevt_template_resource.directory.entries[0].directory):
      return

    desired_language_tag = parser_mediator.GetLanguageTag().lower()

    for entry in wevt_template_resource.directory.entries[0].directory.entries:
      language_tag = languages.WindowsLanguageHelper.GetLanguageTagForLCID(
          entry.id)
      # TODO: add support for common language tag fallback.
      if not language_tag or language_tag.lower() != desired_language_tag:
        continue

      # TODO: use file offset?
      offset = getattr(entry.data.struct, 'OffsetToData', None)
      size = getattr(entry.data.struct, 'Size', None)
      data = pefile_object.get_memory_mapped_image()[offset:offset + size]

      self._ParseWevtTemplate(parser_mediator, message_file, data)

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
      WrongParser: when the file cannot be parsed.
    """
    pe_data_slice = dfvfs_data_slice.DataSlice(file_object)
    try:
      pefile_object = pefile.PE(data=pe_data_slice, fast_load=True)
      pefile_object.parse_data_directories(directories=self._PE_DIRECTORIES)
    except Exception as exception:
      raise errors.WrongParser(
          'Unable to read PE file with error: {0!s}'.format(exception))

    event_data = PEFileEventData()
    # Note that the result of get_imphash() is an empty string if there is no
    # import hash.
    event_data.imphash = pefile_object.get_imphash() or None
    event_data.pe_type = self._GetPEType(pefile_object)
    event_data.section_names = self._GetSectionNames(pefile_object)

    timestamp = getattr(pefile_object.FILE_HEADER, 'TimeDateStamp', None)
    if timestamp:
      event_data.creation_time = dfdatetime_posix_time.PosixTime(
          timestamp=timestamp)

    self._ParseExportTable(pefile_object, event_data)

    self._ParseLoadConfigurationTable(pefile_object, event_data)

    parser_mediator.ProduceEventData(event_data)

    self._ParseImportTable(parser_mediator, pefile_object)

    self._ParseDelayImportTable(parser_mediator, pefile_object)

    self._ParseResourceSection(parser_mediator, pefile_object)


manager.ParsersManager.RegisterParser(PEParser)
