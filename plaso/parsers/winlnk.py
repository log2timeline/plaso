# -*- coding: utf-8 -*-
"""Parser for Windows Shortcut (LNK) files."""

import uuid

import pylnk

from plaso import dependencies
from plaso.events import time_events
from plaso.events import windows_events
from plaso.lib import eventdata
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers.shared import shell_items


dependencies.CheckModuleVersion(u'pylnk')


class WinLnkLinkEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows Shortcut (LNK) link event.

  Attributes:
    birth_droid_file_identifier: the distributed link tracking brith droid
                                 file identifier.
    birth_droid_volume_identifier: the distributed link tracking brith droid
                                   volume identifier.
    command_line_arguments: the command line arguments.
    description: the description of the linked item.
    drive_serial_number: the drive serial number where the linked item resides.
    drive_type: the drive type where the linked item resided.
    droid_file_identifier: the distributed link tracking droid file
                           identifier.
    droid_volume_identifier: the distributed link tracking droid volume
                             identifier.
    env_var_location: the evironment variables loction.
    file_attribute_flags: the file attribute flags of the linked item.
    file_size: the size of the linked item.
    icon_location: the icon location..
    link_target: shell item list of the link target.
    local_path: the local path of the linked item.
    network_path: the local path of the linked item.
    offset: the data offset of the event.
    relative_path: the relative path.
    volume_label: the volume label where the linked item resided.
    working_directory: the working directory.
  """

  DATA_TYPE = u'windows:lnk:link'

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

    self.droid_volume_identifier = lnk_file.droid_volume_identifier
    self.droid_file_identifier = lnk_file.droid_file_identifier
    self.birth_droid_volume_identifier = lnk_file.birth_droid_volume_identifier
    self.birth_droid_file_identifier = lnk_file.birth_droid_file_identifier


class WinLnkParser(interface.FileObjectParser):
  """Parses Windows Shortcut (LNK) files."""

  _INITIAL_FILE_OFFSET = None

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

  def ParseFileObject(
      self, parser_mediator, file_object, display_name=None, **kwargs):
    """Parses a Windows Shortcut (LNK) file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.
      display_name: Optional display name.
    """
    if not display_name:
      display_name = parser_mediator.GetDisplayName()

    lnk_file = pylnk.file()
    lnk_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      lnk_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceParseError(
          u'unable to open file with error: {0:s}'.format(exception))
      return

    link_target = None
    if lnk_file.link_target_identifier_data:
      # TODO: change file_entry.name to display name once it is generated
      # correctly.
      display_name = parser_mediator.GetFilename()
      shell_items_parser = shell_items.ShellItemsParser(display_name)
      shell_items_parser.ParseByteStream(
          parser_mediator, lnk_file.link_target_identifier_data,
          codepage=parser_mediator.codepage)

      link_target = shell_items_parser.CopyToPath()

    access_time = lnk_file.get_file_access_time_as_integer()
    if access_time > 0:
      parser_mediator.ProduceEvent(
          WinLnkLinkEvent(
              access_time, eventdata.EventTimestamp.ACCESS_TIME, lnk_file,
              link_target))

    creation_time = lnk_file.get_file_creation_time_as_integer()
    if creation_time > 0:
      parser_mediator.ProduceEvent(
          WinLnkLinkEvent(
              creation_time, eventdata.EventTimestamp.CREATION_TIME, lnk_file,
              link_target))

    modification_time = lnk_file.get_file_modification_time_as_integer()
    if modification_time > 0:
      parser_mediator.ProduceEvent(
          WinLnkLinkEvent(
              modification_time, eventdata.EventTimestamp.MODIFICATION_TIME,
              lnk_file, link_target))

    if access_time == 0 and creation_time == 0 and modification_time == 0:
      parser_mediator.ProduceEvent(
          WinLnkLinkEvent(
              modification_time, eventdata.EventTimestamp.NOT_A_TIME,
              lnk_file, link_target))

    try:
      uuid_object = uuid.UUID(lnk_file.droid_file_identifier)
      if uuid_object.version == 1:
        event_object = (
            windows_events.WindowsDistributedLinkTrackingCreationEvent(
                uuid_object, display_name))
        parser_mediator.ProduceEvent(event_object)
    except (TypeError, ValueError):
      pass

    try:
      uuid_object = uuid.UUID(lnk_file.birth_droid_file_identifier)
      if uuid_object.version == 1:
        event_object = (
            windows_events.WindowsDistributedLinkTrackingCreationEvent(
                uuid_object, display_name))
        parser_mediator.ProduceEvent(event_object)
    except (TypeError, ValueError):
      pass

    lnk_file.close()


manager.ParsersManager.RegisterParser(WinLnkParser)
