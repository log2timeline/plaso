# -*- coding: utf-8 -*-
"""A parser for Portable Executable (PE) files."""

import pefile

from dfdatetime import posix_time as dfdatetime_posix_time
from dfvfs.helpers import data_slice as dfvfs_data_slice

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class PEEventData(events.EventData):
  """Portable Executable (PE) event data.

  Attributes:
    dll_name (str): name of an imported DLL.
    imphash (str): "Import Hash" of the pe file the event relates to. Also see:
        https://www.mandiant.com/blog/tracking-malware-import-hashing
    pe_type (str): type of PE file the event relates to.
    section_names (list[str]): names of the PE file's sections.
  """

  DATA_TYPE = 'pe'

  def __init__(self):
    """Initializes event data."""
    super(PEEventData, self).__init__(data_type=self.DATA_TYPE)
    self.dll_name = None
    self.imphash = None
    self.pe_type = None
    self.section_names = None


class PEParser(interface.FileObjectParser):
  """Parser for Portable Executable (PE) files."""

  NAME = 'pe'
  DATA_FORMAT = 'Portable Executable (PE) file'

  _PE_DIRECTORIES = [
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']]

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'MZ', offset=0)
    return format_specification

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

    timestamp = getattr(load_configuration_table.struct, 'TimeDateStamp', 0)
    if not timestamp:
      return

    event_data.data_type = 'pe:load_config:modification_time'

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

    event_data.data_type = 'pe:delay_import:import_time'

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

    event_data.data_type = 'pe:export_table'

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

    event_data.data_type = 'pe:import:import_time'

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
    resource_entries = getattr(pefile_object, 'DIRECTORY_ENTRY_RESOURCE', None)
    if not resource_entries:
      return

    event_data.data_type = 'pe:resource:creation_time'

    for resource_entry in resource_entries.entries:
      timestamp = getattr(resource_entry.directory, 'TimeDateStamp', 0)
      if not timestamp:
        continue

      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

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
    event_data.imphash = pefile_object.get_imphash()
    event_data.pe_type = self._GetPEType(pefile_object)
    event_data.section_names = self._GetSectionNames(pefile_object)

    # TODO: remove after refactoring the pe event formatter.
    event_data.data_type = 'pe:compilation:compilation_time'

    timestamp = getattr(pefile_object.FILE_HEADER, 'TimeDateStamp', None)
    # TODO: handle timestamp is None.
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
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
