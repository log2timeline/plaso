# -*- coding: utf-8 -*-
"""Parser for Windows NT shell items."""

import pyfwsi

from dfdatetime import fat_date_time as dfdatetime_fat_date_time

from plaso.containers import shell_item_events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.winnt import shell_folder_ids


class ShellItemsParser(object):
  """Parses for Windows NT shell items."""

  NAME = 'shell_items'

  def __init__(self, origin):
    """Initializes the parser.

    Args:
      origin (str): origin of the event.
    """
    super(ShellItemsParser, self).__init__()
    self._origin = origin
    self._path_segments = []

  def _ParseShellItem(self, parser_mediator, shell_item):
    """Parses a shell item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      shell_item (pyfwsi.item): shell item.
    """
    path_segment = self._ParseShellItemPathSegment(shell_item)
    self._path_segments.append(path_segment)

    event_data = shell_item_events.ShellItemFileEntryEventData()
    event_data.origin = self._origin
    event_data.shell_item_path = self.CopyToPath()

    if isinstance(shell_item, pyfwsi.file_entry):
      event_data.name = shell_item.name

      for extension_block in shell_item.extension_blocks:
        if isinstance(extension_block, pyfwsi.file_entry_extension):
          long_name = extension_block.long_name
          localized_name = extension_block.localized_name
          file_reference = extension_block.file_reference
          if file_reference:
            file_reference = '{0:d}-{1:d}'.format(
                file_reference & 0xffffffffffff, file_reference >> 48)

          event_data.file_reference = file_reference
          event_data.localized_name = localized_name
          event_data.long_name = long_name

          fat_date_time = extension_block.get_creation_time_as_integer()
          if fat_date_time != 0:
            date_time = dfdatetime_fat_date_time.FATDateTime(
                fat_date_time=fat_date_time)
            event = time_events.DateTimeValuesEvent(
                date_time, definitions.TIME_DESCRIPTION_CREATION)
            parser_mediator.ProduceEventWithEventData(event, event_data)

          fat_date_time = extension_block.get_access_time_as_integer()
          if fat_date_time != 0:
            date_time = dfdatetime_fat_date_time.FATDateTime(
                fat_date_time=fat_date_time)
            event = time_events.DateTimeValuesEvent(
                date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
            parser_mediator.ProduceEventWithEventData(event, event_data)

      fat_date_time = shell_item.get_modification_time_as_integer()
      if fat_date_time != 0:
        date_time = dfdatetime_fat_date_time.FATDateTime(
            fat_date_time=fat_date_time)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseShellItemPathSegment(self, shell_item):
    """Parses a shell item path segment.

    Args:
      shell_item (pyfwsi.item): shell item.

    Returns:
      str: shell item path segment.
    """
    path_segment = None

    if isinstance(shell_item, pyfwsi.root_folder):
      description = shell_folder_ids.DESCRIPTIONS.get(
          shell_item.shell_folder_identifier, None)

      if description:
        path_segment = description
      else:
        path_segment = '{{{0:s}}}'.format(shell_item.shell_folder_identifier)

      path_segment = '<{0:s}>'.format(path_segment)

    elif isinstance(shell_item, pyfwsi.volume):
      if shell_item.name:
        path_segment = shell_item.name
      elif shell_item.identifier:
        path_segment = '{{{0:s}}}'.format(shell_item.identifier)

    elif isinstance(shell_item, pyfwsi.file_entry):
      long_name = ''
      for extension_block in shell_item.extension_blocks:
        if isinstance(extension_block, pyfwsi.file_entry_extension):
          long_name = extension_block.long_name

      if long_name:
        path_segment = long_name
      elif shell_item.name:
        path_segment = shell_item.name

    elif isinstance(shell_item, pyfwsi.network_location):
      if shell_item.location:
        path_segment = shell_item.location

    if path_segment is None and shell_item.class_type == 0x00:
      # TODO: check for signature 0x23febbee
      pass

    if path_segment is None:
      path_segment = '<UNKNOWN: 0x{0:02x}>'.format(shell_item.class_type)

    return path_segment

  def CopyToPath(self):
    """Copies the shell items to a path.

    Returns:
      str: converted shell item list path or None.
    """
    number_of_path_segments = len(self._path_segments)
    if number_of_path_segments == 0:
      return None

    strings = [self._path_segments[0]]
    number_of_path_segments -= 1
    for path_segment in self._path_segments[1:]:
      # Remove a trailing \ except for the last path segment.
      if path_segment.endswith('\\') and number_of_path_segments > 1:
        path_segment = path_segment[:-1]

      if ((path_segment.startswith('<') and path_segment.endswith('>')) or
          len(strings) == 1):
        strings.append(' {0:s}'.format(path_segment))
      elif path_segment.startswith('\\'):
        strings.append('{0:s}'.format(path_segment))
      else:
        strings.append('\\{0:s}'.format(path_segment))
      number_of_path_segments -= 1

    return ''.join(strings)

  def GetUpperPathSegment(self):
    """Retrieves the upper shell item path segment.

    Returns:
      str: shell item path segment or "N/A".
    """
    if not self._path_segments:
      return 'N/A'

    return self._path_segments[-1]

  def ParseByteStream(
      self, parser_mediator, byte_stream, parent_path_segments=None,
      codepage='cp1252'):
    """Parses the shell items from the byte stream.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      byte_stream (bytes): shell items data.
      parent_path_segments (Optional[list[str]]): parent shell item path
          segments.
      codepage (Optional[str]): byte stream codepage.
    """
    if parent_path_segments and isinstance(parent_path_segments, list):
      self._path_segments = list(parent_path_segments)
    else:
      self._path_segments = []

    shell_item_list = pyfwsi.item_list()

    parser_mediator.AppendToParserChain(self)
    try:
      shell_item_list.copy_from_byte_stream(
          byte_stream, ascii_codepage=codepage)

      for shell_item in iter(shell_item_list.items):
        self._ParseShellItem(parser_mediator, shell_item)
    finally:
      parser_mediator.PopFromParserChain()
