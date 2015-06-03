# -*- coding: utf-8 -*-
"""A parser for Portable Executable format files."""
import pefile

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class PEFormatException(Exception):
  """Exception indicating an unusual condition in the file being parsed."""
  pass


class PETimeEvent(time_events.PosixTimeEvent):
  """Parent class for events extracted by the PE parser."""
  DATA_TYPE = u'pe'
  TIMESTAMP_TYPE = None

  def __init__(self, timestamp, pe_type, section_names, imphash):
    """Initialize a new event.

    Args:
      timestamp: The timestamp of the event, as seconds since POSIX epoch.
      pe_type: A string indicating the type of PE file the event relates to.
      section_names: A list of strings of the names of the PE file's sections.
      imphash: A string representation of the "Import Hash" of the pe file the
        event relates to, as per
        https://www.mandiant.com/blog/tracking-malware-import-hashing/
    """
    super(PETimeEvent, self).__init__(
        timestamp, self.TIMESTAMP_TYPE, self.DATA_TYPE)
    self.pe_type = pe_type
    self.section_names = section_names
    self.imphash = imphash


class PECompilationEvent(PETimeEvent):
  """Convenience class for PE compile time events."""
  DATA_TYPE = u'pe:compilation:compilation_time'
  TIMESTAMP_TYPE = eventdata.EventTimestamp.CREATION_TIME


class PEImportModificationEvent(PETimeEvent):
  """Convenience class for PE import directory events."""
  DATA_TYPE = u'pe:import:import_time'
  TIMESTAMP_TYPE = eventdata.EventTimestamp.MODIFICATION_TIME

  def __init__(self, timestamp, pe_type, section_names, imphash, dll_name):
    """Initialize a new event.

    Args:
      timestamp: The timestamp of the event, as seconds since POSIX epoch.
      pe_type: A string indicating the type of PE file the event relates to.
      section_names: A list of strings of the names of the PE file's sections.
      imphash: A string representation of the "Import Hash" of the pe file the
        event relates to, as per
        https://www.mandiant.com/blog/tracking-malware-import-hashing/
      dll_name: A string containing the name of the DLL that the import
        timestamp relates to.
    """
    super(PEImportModificationEvent, self).__init__(
        timestamp, pe_type, section_names, imphash)
    self.dll_name = dll_name


class PEDelayImportModificationEvent(PETimeEvent):
  """Convenience class for PE delay import directory events."""
  DATA_TYPE = u'pe:delay_import:import_time'
  TIMESTAMP_TYPE = eventdata.EventTimestamp.MODIFICATION_TIME

  def __init__(self, timestamp, pe_type, section_names, imphash, dll_name):
    """Initialize a new event.

    Args:
      timestamp: The timestamp of the event, as seconds since POSIX epoch.
      pe_type: A string indicating the type of PE file the event relates to.
      section_names: A list of strings of the names of the PE file's sections.
      imphash: A string representation of the "Import Hash" of the pe file the
        event relates to, as per
        https://www.mandiant.com/blog/tracking-malware-import-hashing/
      dll_name: A string containing the name of the DLL that the import
        timestamp relates to.
    """
    super(PEDelayImportModificationEvent, self).__init__(
        timestamp, pe_type, section_names, imphash)
    self.dll_name = dll_name


class PEResourceCreationEvent(PETimeEvent):
  """Convenience class for PE resource creation events."""
  DATA_TYPE = u'pe:resource:creation_time'
  TIMESTAMP_TYPE = eventdata.EventTimestamp.CREATION_TIME


class PELoadConfigModificationEvent(PETimeEvent):
  """Convenience class for PE resource creation events."""
  DATA_TYPE = u'pe:load_config:modification_time'
  TIMESTAMP_TYPE = eventdata.EventTimestamp.MODIFICATION_TIME


class PEParser(interface.SingleFileBaseParser):
  """Parser for Portable Executable (PE) files."""
  _INITIAL_FILE_OFFSET = None
  NAME = u'pe'
  DESCRIPTION = u'Parser for Portable Executable (PE) files.'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'MZ', offset=0)
    return format_specification

  def _GetSectionNames(self, pefile_object):
    """Retrieves all PE section names.

    Args:
      pefile_object: The pefile object to get the names from
        (instance of pefile.PE).

    Returns:
      A list of the names of the sections.
    """
    section_names = []
    for section in pefile_object.sections:
      section_name = getattr(section, u'Name', b'')
      # Ensure the name is decoded correctly.
      try:
        section_name = u'{0:s}'.format(section_name.decode(u'unicode_escape'))
      except UnicodeDecodeError:
        section_name = u'{0:s}'.format(repr(section_name))
      section_names.append(section_name)

    return section_names

  def _GetImportTimestamps(self, pefile_object):
    """Retrieves timestamps from the import directory, if available.

    Args:
      pefile_object: The pefile object to get the names from
        (instance of pefile.PE).

    Returns:
      A list of the timestamps from the import directory.
    """
    import_timestamps = []
    if not hasattr(pefile_object, u'DIRECTORY_ENTRY_IMPORT'):
      return import_timestamps
    for importdata in pefile_object.DIRECTORY_ENTRY_IMPORT:
      timestamp = getattr(importdata.struct, u'TimeDateStamp', 0)
      dll_name = getattr(importdata, u'dll', u'<NO DLL NAME>')
      if timestamp:
        import_timestamps.append([dll_name, timestamp])
    return import_timestamps

  def _GetResourceTimestamps(self, pefile_object):
    """Retrieves timestamps from resource directory entries, if available.

    Args:
      pefile_object: The pefile object to get the names from
        (instance of pefile.PE).

    Returns:
      A list of the timestamps from the resource directory.
    """
    timestamps = []
    if not hasattr(pefile_object, u'DIRECTORY_ENTRY_RESOURCE'):
      return timestamps
    for entrydata in pefile_object.DIRECTORY_ENTRY_RESOURCE.entries:
      directory = entrydata.directory
      timestamp = getattr(directory, u'TimeDateStamp', 0)
      if timestamp:
        timestamps.append(timestamp)
    return timestamps

  def _GetLoadConfigTimestamp(self, pefile_object):
    """Retrieves the timestamp from the Load Configuration directory.

    Args:
      pefile_object: The pefile object to get the names from
        (instance of pefile.PE).

    Returns:
      A list of the timestamps from the resource directory.
    """
    if not hasattr(pefile_object, u'DIRECTORY_ENTRY_LOAD_CONFIG'):
      return
    timestamp = getattr(
        pefile_object.DIRECTORY_ENTRY_LOAD_CONFIG.struct, u'TimeDateStamp', 0)
    return timestamp

  def _GetDelayImportTimestamps(self, pefile_object):
    """Retrieves timestamps from delay import entries, if available.

    Args:
      pefile_object: The pefile object to get the names from
        (instance of pefile.PE).

    Returns:
      A list two-element lists, where the first element is the name of the DLL
      being imported, and the second is the timestamp of the entry.
    """
    delay_import_timestamps = []
    if not hasattr(pefile_object, u'DIRECTORY_ENTRY_DELAY_IMPORT'):
      return delay_import_timestamps
    for importdata in pefile_object.DIRECTORY_ENTRY_DELAY_IMPORT:
      dll_name = importdata.dll
      timestamp = getattr(importdata.struct, u'dwTimeStamp', 0)
      delay_import_timestamps.append([dll_name, timestamp])
    return delay_import_timestamps

  def _GetPEType(self, pefile_object):
    """Retrieves the type of the PE file.

    Args:
      pefile_object: The pefile object to get the names from
        (instance of pefile.PE).

    Returns:
      A string indicating the type of the file.
    """
    if pefile_object.is_dll():
      return u'Dynamic Link Library (DLL)'
    if pefile_object.is_exe():
      return u'Executable (EXE)'
    if pefile_object.is_driver():
      return u'Driver (SYS)'
    return u'Unknown PE type'

  def ParseFileObject(self, parser_mediator, file_object, **unused_kwargs):
    """Parses a Portable Executable (PE) file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    pe_data = file_object.read()
    try:
      pefile_object = pefile.PE(data=pe_data, fast_load=True)
      pefile_object.parse_data_directories(
          directories=[
              pefile.DIRECTORY_ENTRY[u'IMAGE_DIRECTORY_ENTRY_IMPORT'],
              pefile.DIRECTORY_ENTRY[u'IMAGE_DIRECTORY_ENTRY_EXPORT'],
              pefile.DIRECTORY_ENTRY[u'IMAGE_DIRECTORY_ENTRY_RESOURCE'],
              pefile.DIRECTORY_ENTRY[u'IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT'],])
    except:
      raise errors.UnableToParseFile()

    try:
      pe_type = self._GetPEType(pefile_object)
    except PEFormatException as error:
      message = u'Unable to parse PE file: {0:s}'.format(error.message)
      parser_mediator.ProduceParserError(message)
      return
    section_names = self._GetSectionNames(pefile_object)
    imphash = pefile_object.get_imphash()

    file_header_timestamp = getattr(
        pefile_object.FILE_HEADER, u'TimeDateStamp', None)
    event = PECompilationEvent(
        file_header_timestamp, pe_type, section_names, imphash)
    parser_mediator.ProduceEvent(event)

    for dll_name, timestamp in self._GetImportTimestamps(pefile_object):
      if timestamp and not timestamp == 0:
        event = PEImportModificationEvent(
            timestamp, pe_type, section_names, imphash, dll_name)
        parser_mediator.ProduceEvent(event)

    for dll_name, timestamp in self._GetDelayImportTimestamps(pefile_object):
      if timestamp and not timestamp == 0:
        event = PEDelayImportModificationEvent(
            timestamp, pe_type, section_names, imphash, dll_name)
        parser_mediator.ProduceEvent(event)

    for timestamp in self._GetResourceTimestamps(pefile_object):
      if timestamp and not timestamp == 0:
        event = PEResourceCreationEvent(
            timestamp, pe_type, section_names, imphash)
        parser_mediator.ProduceEvent(event)

    timestamp = self._GetLoadConfigTimestamp(pefile_object)
    if timestamp and not timestamp == 0:
      event = PELoadConfigModificationEvent(
          timestamp, pe_type, section_names, imphash)
      parser_mediator.ProduceEvent(event)


manager.ParsersManager.RegisterParser(PEParser)
