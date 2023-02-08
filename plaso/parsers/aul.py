# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) file parser."""

from plaso.lib.aul import dsc
from plaso.lib.aul import timesync
from plaso.lib.aul import tracev3
from plaso.lib.aul import uuidfile

from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class AULParser(interface.FileEntryParser):
  """Parser for Apple Unified Logging (AUL) files.

  Attributes:
    dsc_parser (DSCFileParser): Instance of a DSC file parser.
    timesync_parser (TimesyncParser): Instance of a TimeSync parser.
    tracev3_parser (TraceV3FileParser): Instance of a Tracev3 parser.
    uuid_parser (UUIDFileParser): Instance of a UUID file parser.
  """

  NAME = 'aul_log'
  DATA_FORMAT = 'Apple Unified Log (AUL) file'

  def __init__(self):
    """Initializes an Apple Unified Logging parser."""
    super(AULParser, self).__init__()
    self.dsc_parser = None
    self.timesync_parser = timesync.TimesyncParser()
    self.tracev3_parser = None
    self.uuid_parser = None

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

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses an Apple Unified Logging file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_entry (dfvfs.FileEntry): file entry.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_object = file_entry.GetFileObject()
    if not file_object:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] unable to parse tracev3 file {1:s}'.format(
              self.NAME, display_name))

    # Parse timesync files
    file_system = file_entry.GetFileSystem()
    self.timesync_parser.ParseAll(parser_mediator, file_entry, file_system)

    self.uuid_parser = uuidfile.UUIDFileParser(file_entry, file_system)
    self.dsc_parser = dsc.DSCFileParser(file_entry, file_system)

    self.tracev3_parser = tracev3.TraceV3FileParser(
        self.timesync_parser, self.uuid_parser, self.dsc_parser)

    try:
      self.tracev3_parser.ParseFileObject(parser_mediator, file_object)
    except (IOError, errors.ParseError) as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] unable to parse tracev3 file {1:s} with error: {2!s}'.format(
              self.NAME, display_name, exception))


manager.ParsersManager.RegisterParser(AULParser)
