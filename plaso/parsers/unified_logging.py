# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) file parser."""

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.parsers.shared.unified_logging import dsc
from plaso.parsers.shared.unified_logging import timesync
from plaso.parsers.shared.unified_logging import tracev3
from plaso.parsers.shared.unified_logging import uuidfile

from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class AULParser(interface.FileEntryParser):
  """Parser for Apple Unified Logging (AUL) files."""

  NAME = 'aul_log'
  DATA_FORMAT = 'Apple Unified Log (AUL) file'

  def __init__(self):
    """Initializes an Apple Unified Logging parser."""
    super(AULParser, self).__init__()
    self._dsc_parser = None
    self._timesync_parser = None
    self._tracev3_parser = None
    self._uuid_parser = None

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(
        b'\x00\x10\x00\x00', offset=0)
    return format_specification

  def _ParseTimeSyncDatabases(self, parser_mediator, file_system, file_entry):
    """Parses the timesync database files.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_system (dfvfs.FileSystem): file system on which the Unified Logging
          files reside.
      file_entry (dfvfs.FileEntry): a tracev3 file entry.
    """
    self._timesync_parser = timesync.TimesyncDatabaseParser()

    # TODO: retrieve the file entry of the timesync directory and iterate
    # the sub file entries instead of using the file system searcher.

    searcher_object = file_system_searcher.FileSystemSearcher(
        file_system, file_entry.path_spec.parent)

    path_segments = file_system.SplitPath(file_entry.path_spec.location)[:-2]
    path_segments.extend(['timesync', '*.timesync'])

    timesync_file_glob = file_system.JoinPath(path_segments)
    find_spec = file_system_searcher.FindSpec(
          file_entry_types=[dfvfs_definitions.FILE_ENTRY_TYPE_FILE],
          location_glob=timesync_file_glob)

    for path_spec in searcher_object.Find(find_specs=[find_spec]):
      file_object = path_spec_resolver.Resolver.OpenFileObject(path_spec)
      if not file_object:
        relative_path = parser_mediator.GetRelativePathForPathSpec(path_spec)
        parser_mediator.ProduceExtractionWarning(
            'Unable to open timesync database file: {0:s}.'.format(
                relative_path))
        continue

      try:
        self._timesync_parser.ParseFileObject(file_object)
      except (IOError, errors.ParseError) as exception:
        relative_path = parser_mediator.GetRelativePathForPathSpec(path_spec)
        parser_mediator.ProduceExtractionWarning(
            'Unable to parse data block file: {0:s} with error: {1!s}'.format(
                relative_path, exception))

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses an Apple Unified Logging file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_entry (dfvfs.FileEntry): file entry.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_object = file_entry.GetFileObject()
    if not file_object:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] unable to open tracev3 file {1:s}'.format(
              self.NAME, display_name))

    file_system = file_entry.GetFileSystem()

    self._ParseTimeSyncDatabases(parser_mediator, file_system, file_entry)

    self._uuid_parser = uuidfile.UUIDFileParser(file_entry, file_system)
    self._dsc_parser = dsc.DSCFileParser(file_entry, file_system)

    self._tracev3_parser = tracev3.TraceV3FileParser(
        self._timesync_parser, self._uuid_parser, self._dsc_parser)

    try:
      self._tracev3_parser.ParseFileObject(parser_mediator, file_object)
    except (IOError, errors.ParseError) as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] unable to parse tracev3 file {1:s} with error: {2!s}'.format(
              self.NAME, display_name, exception))


manager.ParsersManager.RegisterParser(AULParser)
