# -*- coding: utf-8 -*-
"""Parser for Windows Shortcut (LNK) files."""

import uuid

import pylnk

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import windows_events
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers.shared import shell_items


class WinLnkLinkEventData(events.EventData):
  """Windows Shortcut (LNK) link event data.

  Attributes:
    access_time (dfdatetime.DateTimeValues): file entry last access date
        and time.
    birth_droid_file_identifier (str): distributed link tracking birth droid
        file identifier.
    birth_droid_volume_identifier (str): distributed link tracking birth droid
        volume identifier.
    command_line_arguments (str): command line arguments.
    creation_time (dfdatetime.DateTimeValues): file entry creation date
        and time.
    description (str): description of the linked item.
    drive_serial_number (int): drive serial number where the linked item
        resides.
    drive_type (str): drive type where the linked item resided.
    droid_file_identifier (str): distributed link tracking droid file
        identifier.
    droid_volume_identifier (str): distributed link tracking droid volume
        identifier.
    env_var_location (str): environment variables loction.
    file_attribute_flags (int): file attribute flags of the linked item.
    file_size (int): size of the linked item.
    icon_location (str): icon location.
    link_target (str): shell item list of the link target.
    local_path (str): local path of the linked item.
    modification_time (dfdatetime.DateTimeValues): file entry last modification
        date and time.
    network_path (str): local path of the linked item.
    relative_path (str): relative path.
    volume_label (str): volume label where the linked item resided.
    working_directory (str): working directory.
  """

  DATA_TYPE = 'windows:lnk:link'

  def __init__(self):
    """Initializes event data."""
    super(WinLnkLinkEventData, self).__init__(data_type=self.DATA_TYPE)
    self.access_time = None
    self.birth_droid_file_identifier = None
    self.birth_droid_volume_identifier = None
    self.command_line_arguments = None
    self.creation_time = None
    self.description = None
    self.drive_serial_number = None
    self.drive_type = None
    self.droid_file_identifier = None
    self.droid_volume_identifier = None
    self.env_var_location = None
    self.file_attribute_flags = None
    self.file_size = None
    self.icon_location = None
    self.link_target = None
    self.local_path = None
    self.modification_time = None
    self.network_path = None
    self.relative_path = None
    self.volume_label = None
    self.working_directory = None


class WinLnkParser(interface.FileObjectParser):
  """Parses Windows Shortcut (LNK) files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'lnk'
  DATA_FORMAT = 'Windows Shortcut (LNK) file'

  def _GetDateTime(self, filetime):
    """Retrieves the date and time from a FILETIME timestamp.

    Args:
      filetime (int): FILETIME timestamp.

    Returns:
      dfdatetime.DateTimeValues: date and time or None if not set.
    """
    if not filetime:
      return None

    return dfdatetime_filetime.Filetime(timestamp=filetime)

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(
        b'\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46',
        offset=4)
    return format_specification

  def _ParseDistributedTrackingIdentifier(
      self, parser_mediator, uuid_string, origin):
    """Extracts data from a Distributed Tracking identifier.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      uuid_string (str): UUID string of the Distributed Tracking identifier.
      origin (str): origin of the event (event source).
    """
    uuid_object = uuid.UUID(uuid_string)

    if uuid_object.version == 1:
      event_data = windows_events.WindowsDistributedLinkTrackingEventData(
          uuid_object, origin)
      parser_mediator.ProduceEventData(event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Shortcut (LNK) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.
    """
    display_name = parser_mediator.GetDisplayName()
    self.ParseFileLNKFile(parser_mediator, file_object, display_name)

  def ParseFileLNKFile(
      self, parser_mediator, file_object, display_name):
    """Parses a Windows Shortcut (LNK) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.
      display_name (str): display name.
    """
    code_page = parser_mediator.GetCodePage()

    lnk_file = pylnk.file()
    lnk_file.set_ascii_codepage(code_page)

    try:
      lnk_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open file with error: {0!s}'.format(exception))
      return

    link_target = None
    if lnk_file.link_target_identifier_data:  # pylint: disable=using-constant-test
      # TODO: change file_entry.name to display name once it is generated
      # correctly.
      display_name = parser_mediator.GetFilename()
      shell_items_parser = shell_items.ShellItemsParser(display_name)
      shell_items_parser.ParseByteStream(
          parser_mediator, lnk_file.link_target_identifier_data,
          codepage=code_page)

      link_target = shell_items_parser.CopyToPath()

    event_data = WinLnkLinkEventData()
    event_data.access_time = self._GetDateTime(
        lnk_file.get_file_access_time_as_integer())
    event_data.birth_droid_file_identifier = (
        lnk_file.birth_droid_file_identifier)
    event_data.birth_droid_volume_identifier = (
        lnk_file.birth_droid_volume_identifier)
    event_data.command_line_arguments = lnk_file.command_line_arguments
    event_data.creation_time = self._GetDateTime(
        lnk_file.get_file_creation_time_as_integer())
    event_data.description = lnk_file.description
    event_data.drive_serial_number = lnk_file.drive_serial_number
    event_data.drive_type = lnk_file.drive_type
    event_data.droid_file_identifier = lnk_file.droid_file_identifier
    event_data.droid_volume_identifier = lnk_file.droid_volume_identifier
    event_data.env_var_location = lnk_file.environment_variables_location
    event_data.file_attribute_flags = lnk_file.file_attribute_flags
    event_data.file_size = lnk_file.file_size
    event_data.icon_location = lnk_file.icon_location
    event_data.link_target = link_target
    event_data.local_path = lnk_file.local_path
    event_data.modification_time = self._GetDateTime(
        lnk_file.get_file_modification_time_as_integer())
    event_data.network_path = lnk_file.network_path
    event_data.relative_path = lnk_file.relative_path
    event_data.volume_label = lnk_file.volume_label
    event_data.working_directory = lnk_file.working_directory

    parser_mediator.ProduceEventData(event_data)

    if lnk_file.droid_file_identifier:  # pylint: disable=using-constant-test
      try:
        self._ParseDistributedTrackingIdentifier(
            parser_mediator, lnk_file.droid_file_identifier, display_name)
      except (TypeError, ValueError) as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to read droid file identifier with error: {0!s}.'.format(
                exception))

    if lnk_file.birth_droid_file_identifier:  # pylint: disable=using-constant-test
      try:
        self._ParseDistributedTrackingIdentifier(
            parser_mediator, lnk_file.birth_droid_file_identifier, display_name)
      except (TypeError, ValueError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read birth droid file identifier with error: '
            '{0!s}.').format(exception))

    lnk_file.close()


manager.ParsersManager.RegisterParser(WinLnkParser)
