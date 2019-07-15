# -*- coding: utf-8 -*-
"""A parser for Portable Executable format files."""

from __future__ import unicode_literals

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
  DESCRIPTION = 'Parser for Portable Executable (PE) files.'

  _PE_DIRECTORIES = [
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'],
      pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT']]

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'MZ', offset=0)
    return format_specification

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

  def _GetImportTimestamps(self, pefile_object):
    """Retrieves timestamps from the import directory, if available.

    Args:
      pefile_object (pefile.PE): pefile object.

    Returns:
      list[int]: import timestamps.
    """
    import_timestamps = []
    if not hasattr(pefile_object, 'DIRECTORY_ENTRY_IMPORT'):
      return import_timestamps
    for importdata in pefile_object.DIRECTORY_ENTRY_IMPORT:
      dll_name = getattr(importdata, 'dll', '')
      try:
        dll_name = dll_name.decode('ascii')
      except UnicodeDecodeError:
        dll_name = dll_name.decode('ascii', errors='replace')
      if not dll_name:
        dll_name = '<NO DLL NAME>'

      timestamp = getattr(importdata.struct, 'TimeDateStamp', 0)
      if timestamp:
        import_timestamps.append([dll_name, timestamp])
    return import_timestamps

  def _GetResourceTimestamps(self, pefile_object):
    """Retrieves timestamps from resource directory entries, if available.

    Args:
      pefile_object (pefile.PE): pefile object.

    Returns:
      list[int]: resource timestamps.
    """
    timestamps = []
    if not hasattr(pefile_object, 'DIRECTORY_ENTRY_RESOURCE'):
      return timestamps
    for entrydata in pefile_object.DIRECTORY_ENTRY_RESOURCE.entries:
      directory = entrydata.directory
      timestamp = getattr(directory, 'TimeDateStamp', 0)
      if timestamp:
        timestamps.append(timestamp)
    return timestamps

  def _GetLoadConfigTimestamp(self, pefile_object):
    """Retrieves the timestamp from the Load Configuration directory.

    Args:
      pefile_object (pefile.PE): pefile object.

    Returns:
      int: load configuration timestamps or None if there are none present.
    """
    if not hasattr(pefile_object, 'DIRECTORY_ENTRY_LOAD_CONFIG'):
      return None
    timestamp = getattr(
        pefile_object.DIRECTORY_ENTRY_LOAD_CONFIG.struct, 'TimeDateStamp', 0)
    return timestamp

  def _GetDelayImportTimestamps(self, pefile_object):
    """Retrieves timestamps from delay import entries, if available.

    Args:
      pefile_object (pefile.PE): pefile object.

    Returns:
      tuple[str, int]: name of the DLL being imported and the second is
          the timestamp of the entry.
    """
    delay_import_timestamps = []
    if not hasattr(pefile_object, 'DIRECTORY_ENTRY_DELAY_IMPORT'):
      return delay_import_timestamps
    for importdata in pefile_object.DIRECTORY_ENTRY_DELAY_IMPORT:
      dll_name = importdata.dll
      try:
        dll_name = dll_name.decode('ascii')
      except UnicodeDecodeError:
        dll_name = dll_name.decode('ascii', errors='replace')

      timestamp = getattr(importdata.struct, 'dwTimeStamp', 0)
      delay_import_timestamps.append([dll_name, timestamp])
    return delay_import_timestamps

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

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Portable Executable (PE) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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

    for dll_name, timestamp in self._GetImportTimestamps(pefile_object):
      if timestamp:
        event_data.dll_name = dll_name
        event_data.data_type = 'pe:import:import_time'

        date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    for dll_name, timestamp in self._GetDelayImportTimestamps(pefile_object):
      if timestamp:
        event_data.dll_name = dll_name
        event_data.data_type = 'pe:delay_import:import_time'

        date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    event_data.dll_name = None

    for timestamp in self._GetResourceTimestamps(pefile_object):
      if timestamp:
        event_data.data_type = 'pe:resource:creation_time'

        date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetLoadConfigTimestamp(pefile_object)
    if timestamp:
      event_data.data_type = 'pe:load_config:modification_time'

      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(PEParser)
