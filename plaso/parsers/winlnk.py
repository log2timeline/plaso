# -*- coding: utf-8 -*-
"""Parser for Windows Shortcut (LNK) files."""

import uuid

import pylnk

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import uuid_time as dfdatetime_uuid_time

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers.shared import shell_items


class WinLnkLinkEvent(time_events.DateTimeValuesEvent):
  """Convenience class for a Windows Shortcut (LNK) link event.

  Attributes:
    birth_droid_file_identifier (str): distributed link tracking brith droid
        file identifier.
    birth_droid_volume_identifier (str): distributed link tracking brith droid
        volume identifier.
    command_line_arguments (str): command line arguments.
    description (str): description of the linked item.
    drive_serial_number (int): drive serial number where the linked item
        resides.
    drive_type (str): drive type where the linked item resided.
    droid_file_identifier (str): distributed link tracking droid file
        identifier.
    droid_volume_identifier (str): distributed link tracking droid volume
        identifier.
    env_var_location (str): evironment variables loction.
    file_attribute_flags (int): file attribute flags of the linked item.
    file_size (int): size of the linked item.
    icon_location (str): icon location.
    link_target (str): shell item list of the link target.
    local_path (str): local path of the linked item.
    network_path (str): local path of the linked item.
    offset (int): data offset of the event.
    relative_path (str): relative path.
    volume_label (str): volume label where the linked item resided.
    working_directory (str): working directory.
  """

  DATA_TYPE = u'windows:lnk:link'

  def __init__(
      self, date_time, date_time_description, lnk_file, link_target, offset=0):
    """Initializes an event.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date
          and time values.
      lnk_file (pylnk.file): LNK file.
      link_target (str): link target shell item list.
      offset (Optional[int]): data offset of the event.
    """
    super(WinLnkLinkEvent, self).__init__(date_time, date_time_description)
    self.birth_droid_file_identifier = lnk_file.birth_droid_file_identifier
    self.birth_droid_volume_identifier = lnk_file.birth_droid_volume_identifier
    self.command_line_arguments = lnk_file.command_line_arguments
    self.description = lnk_file.description
    self.drive_serial_number = lnk_file.drive_serial_number
    self.drive_type = lnk_file.drive_type
    self.droid_file_identifier = lnk_file.droid_file_identifier
    self.droid_volume_identifier = lnk_file.droid_volume_identifier
    self.env_var_location = lnk_file.environment_variables_location
    self.file_attribute_flags = lnk_file.file_attribute_flags
    self.file_size = lnk_file.file_size
    self.icon_location = lnk_file.icon_location
    self.link_target = link_target
    self.local_path = lnk_file.local_path
    self.network_path = lnk_file.network_path
    self.offset = offset
    self.relative_path = lnk_file.relative_path
    self.volume_label = lnk_file.volume_label
    self.working_directory = lnk_file.working_directory


class WinLnkParser(interface.FileObjectParser):
  """Parses Windows Shortcut (LNK) files."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'lnk'
  DESCRIPTION = u'Parser for Windows Shortcut (LNK) files.'

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
          and other components, such as storage and dfvfs.
      uuid_string (str): UUID string of the Distributed Tracking identifier.
      origin (str): origin of the event (event source).
    """
    uuid_object = uuid.UUID(uuid_string)

    if uuid_object.version == 1:
      event_data = windows_events.WindowsDistributedLinkTrackingEventData(
          uuid_object, origin)
      date_time = dfdatetime_uuid_time.UUIDTime(timestamp=uuid_object.time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(
      self, parser_mediator, file_object, display_name=None, **kwargs):
    """Parses a Windows Shortcut (LNK) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
      display_name (Optional[str]): display name.
    """
    if not display_name:
      display_name = parser_mediator.GetDisplayName()

    lnk_file = pylnk.file()
    lnk_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      lnk_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionError(
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
    if access_time != 0:
      date_time = dfdatetime_filetime.Filetime(timestamp=access_time)
      event = WinLnkLinkEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS, lnk_file,
          link_target)
      parser_mediator.ProduceEvent(event)

    creation_time = lnk_file.get_file_creation_time_as_integer()
    if creation_time != 0:
      date_time = dfdatetime_filetime.Filetime(timestamp=creation_time)
      event = WinLnkLinkEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION, lnk_file,
          link_target)
      parser_mediator.ProduceEvent(event)

    modification_time = lnk_file.get_file_modification_time_as_integer()
    if modification_time != 0:
      date_time = dfdatetime_filetime.Filetime(timestamp=modification_time)
      event = WinLnkLinkEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION,
          lnk_file, link_target)
      parser_mediator.ProduceEvent(event)

    if access_time == 0 and creation_time == 0 and modification_time == 0:
      date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
      event = WinLnkLinkEvent(
          date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME, lnk_file,
          link_target)
      parser_mediator.ProduceEvent(event)

    if lnk_file.droid_file_identifier:
      try:
        self._ParseDistributedTrackingIdentifier(
            parser_mediator, lnk_file.droid_file_identifier, display_name)
      except (TypeError, ValueError) as exception:
        parser_mediator.ProduceExtractionError(
            u'unable to read droid file identifier with error: {0:s}.'.format(
                exception))

    if lnk_file.birth_droid_file_identifier:
      try:
        self._ParseDistributedTrackingIdentifier(
            parser_mediator, lnk_file.birth_droid_file_identifier, display_name)
      except (TypeError, ValueError) as exception:
        parser_mediator.ProduceExtractionError((
            u'unable to read birth droid file identifier with error: '
            u'{0:s}.').format(exception))

    lnk_file.close()


manager.ParsersManager.RegisterParser(WinLnkParser)
