# -*- coding: utf-8 -*-
"""Parser for Windows Shortcut (LNK) files."""

import pylnk

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers.shared import shell_items


if pylnk.get_version() < '20141026':
  raise ImportWarning('WinLnkParser requires at least pylnk 20141026.')


class WinLnkLinkEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows Shortcut (LNK) link event."""

  DATA_TYPE = 'windows:lnk:link'

  def __init__(self, timestamp, timestamp_description, lnk_file, link_target):
    """Initializes the event object.

    Args:
      timestamp: The FILETIME value for the timestamp.
      timestamp_description: The usage string for the timestamp value.
      lnk_file: The LNK file (instance of pylnk.file).
      link_target: String representation of the link target shell item list
                   or None.
    """
    super(WinLnkLinkEvent, self).__init__(timestamp, timestamp_description)

    self.offset = 0
    self.file_size = lnk_file.file_size
    self.file_attribute_flags = lnk_file.file_attribute_flags
    self.drive_type = lnk_file.drive_type
    self.drive_serial_number = lnk_file.drive_serial_number
    self.description = lnk_file.description
    self.volume_label = lnk_file.volume_label
    self.local_path = lnk_file.local_path
    self.network_path = lnk_file.network_path
    self.command_line_arguments = lnk_file.command_line_arguments
    self.env_var_location = lnk_file.environment_variables_location
    self.relative_path = lnk_file.relative_path
    self.working_directory = lnk_file.working_directory
    self.icon_location = lnk_file.icon_location

    if link_target:
      self.link_target = link_target


class WinLnkParser(interface.BaseParser):
  """Parses Windows Shortcut (LNK) files."""

  NAME = u'lnk'
  DESCRIPTION = u'Parser for Windows Shortcut (LNK) files.'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(
        b'\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46',
        offset=4)
    return format_specification

  def Parse(self, parser_mediator, **kwargs):
    """Parses a Windows Shortcut (LNK) file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    file_object = parser_mediator.GetFileObject()
    try:
      self.ParseFileObject(parser_mediator, file_object)
    finally:
      file_object.close()

  def ParseFileObject(self, parser_mediator, file_object, display_name=None):
    """Parses a Windows Shortcut (LNK) file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.
      display_name: Optional display name.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    if not display_name:
      display_name = parser_mediator.GetDisplayName()

    lnk_file = pylnk.file()
    lnk_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      lnk_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s} with error: {2:s}'.format(
              self.NAME, display_name, exception))

    link_target = None
    if lnk_file.link_target_identifier_data:
      # TODO: change file_entry.name to display name once it is generated
      # correctly.
      file_entry = parser_mediator.GetFileEntry()
      display_name = file_entry.name
      shell_items_parser = shell_items.ShellItemsParser(display_name)
      parser_mediator.AppendToParserChain(shell_items_parser)
      try:
        shell_items_parser.Parse(
            parser_mediator, lnk_file.link_target_identifier_data,
            codepage=parser_mediator.codepage)
      finally:
        parser_mediator.PopFromParserChain()

      link_target = shell_items_parser.CopyToPath()

    parser_mediator.ProduceEvents(
        [WinLnkLinkEvent(
            lnk_file.get_file_access_time_as_integer(),
            eventdata.EventTimestamp.ACCESS_TIME, lnk_file, link_target),
         WinLnkLinkEvent(
             lnk_file.get_file_creation_time_as_integer(),
             eventdata.EventTimestamp.CREATION_TIME, lnk_file, link_target),
         WinLnkLinkEvent(
             lnk_file.get_file_modification_time_as_integer(),
             eventdata.EventTimestamp.MODIFICATION_TIME, lnk_file,
             link_target)])

    # TODO: add support for the distributed link tracker.

    lnk_file.close()

  def UpdateChainAndParseFileObject(
      self, parser_mediator, file_object, display_name=None):
    """Wrapper for ParseFileObject to synchronize the parser chain.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.
      display_name: Optional display name.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    parser_mediator.AppendToParserChain(self)
    self.ParseFileObject(parser_mediator, file_object, display_name)


manager.ParsersManager.RegisterParser(WinLnkParser)
