"""Parser for Windows NT shell items."""

import pyfwsi

from dfdatetime import fat_date_time as dfdatetime_fat_date_time

from plaso.containers import windows_events
from plaso.helpers.windows import shell_folders
from plaso.lib import definitions


class ShellItemsParser:
  """Parses for Windows NT shell items."""

  NAME = 'shell_items'

  _PATH_ESCAPE_CHARACTERS = {'\\': '\\\\'}
  _PATH_ESCAPE_CHARACTERS.update(definitions.NON_PRINTABLE_CHARACTERS)

  def __init__(self, origin):
    """Initializes the parser.

    Args:
      origin (str): origin of the event.
    """
    super().__init__()
    self._origin = origin
    self._path_escape_characters = str.maketrans(self._PATH_ESCAPE_CHARACTERS)
    self._path_segments = []

  def _GetDateTime(self, fat_date_time):
    """Retrieves the date and time from a FAT date time.

    Args:
      fat_date_time (int): FAT date time.

    Returns:
      dfdatetime.DateTimeValues: date and time or None if not set.
    """
    if not fat_date_time:
      return None

    return dfdatetime_fat_date_time.FATDateTime(fat_date_time=fat_date_time)

  def _GetSanitizedPathString(self, path):
    """Retrieves a sanitize path string.

    Args:
      path (str): path.

    Returns:
      str: sanitized path string.
    """
    if not path:
      return None

    return path.translate(self._path_escape_characters)

  def _ParseShellItem(self, parser_mediator, shell_item):
    """Parses a shell item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      shell_item (pyfwsi.item): shell item.
    """
    path_segment = self._ParseShellItemPathSegment(shell_item)
    self._path_segments.append(path_segment)

    # TODO: generate event_data for non file_entry shell items.

    if isinstance(shell_item, pyfwsi.file_entry):
      event_data = windows_events.WindowsShellItemFileEntryEventData()
      event_data.modification_time = self._GetDateTime(
          shell_item.get_modification_time_as_integer())
      event_data.name = self._GetSanitizedPathString(shell_item.name)
      event_data.origin = self._origin
      event_data.shell_item_path = self.CopyToPath()

      number_of_event_data = 0
      for extension_block in shell_item.extension_blocks:
        if isinstance(extension_block, pyfwsi.file_entry_extension):
          file_reference = extension_block.file_reference
          if file_reference:
            mft_entry_number = file_reference & 0xffffffffffff
            sequence_number = file_reference >> 48
            file_reference = f'{mft_entry_number:d}-{sequence_number:d}'

          event_data.access_time = self._GetDateTime(
              extension_block.get_access_time_as_integer())
          event_data.creation_time = self._GetDateTime(
              extension_block.get_creation_time_as_integer())
          event_data.file_reference = file_reference
          event_data.localized_name = extension_block.localized_name
          event_data.long_name = self._GetSanitizedPathString(
              extension_block.long_name)

          # TODO: change to generate an event_data for each extension block.
          if (event_data.access_time or event_data.creation_time or
              event_data.modification_time):
            parser_mediator.ProduceEventData(event_data)

            number_of_event_data += 1

      # TODO: change to generate an event_data for each shell item.
      if not number_of_event_data and event_data.modification_time:
        parser_mediator.ProduceEventData(event_data)

  def _ParseShellItemPathSegment(self, shell_item):
    """Parses a shell item path segment.

    Args:
      shell_item (pyfwsi.item): shell item.

    Returns:
      str: shell item path segment.
    """
    path_segment = None

    if isinstance(shell_item, pyfwsi.control_panel_category):
      # TODO: map identifier to human readable string.
      path_segment = f'<Control panel category: {shell_item.identifier:d}>'

    elif isinstance(shell_item, pyfwsi.control_panel_item):
      # TODO: map identifier to human readable string.
      path_segment = f'<Control panel item: {shell_item.identifier:s}>'

    elif isinstance(shell_item, pyfwsi.file_entry):
      long_name = ''
      for extension_block in shell_item.extension_blocks:
        if isinstance(extension_block, pyfwsi.file_entry_extension):
          long_name = self._GetSanitizedPathString(extension_block.long_name)

      if long_name:
        path_segment = long_name
      elif shell_item.name:
        path_segment = self._GetSanitizedPathString(shell_item.name)

    elif isinstance(shell_item, pyfwsi.network_location):
      if shell_item.location:
        path_segment = shell_item.location

    elif isinstance(shell_item, pyfwsi.root_folder):
      description = shell_folders.WindowsShellFoldersHelper.GetDescription(
          shell_item.shell_folder_identifier)

      if description:
        path_segment = description
      else:
        path_segment = f'{{{shell_item.shell_folder_identifier:s}}}'

      path_segment = f'<{path_segment}>'

    elif isinstance(shell_item, pyfwsi.users_property_view):
      path_segment = '<Users property view>'

    elif isinstance(shell_item, pyfwsi.volume):
      if shell_item.name:
        path_segment = self._GetSanitizedPathString(shell_item.name)
      elif shell_item.identifier:
        path_segment = f'{{{shell_item.identifier:s}}}'

    if path_segment is None:
      path_segment = f'<UNKNOWN: 0x{shell_item.class_type:02x}>'

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
      if path_segment.endswith('\\\\') and number_of_path_segments > 1:
        path_segment = path_segment[:-2]

      if ((path_segment.startswith('<') and path_segment.endswith('>')) or
          len(strings) == 1):
        strings.append(f' {path_segment:s}')
      elif path_segment.startswith('\\'):
        strings.append(f'{path_segment:s}')
      else:
        strings.append(f'\\\\{path_segment:s}')
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
          and other components, such as storage and dfVFS.
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

    parser_mediator.AppendToParserChain(self.NAME)
    try:
      shell_item_list.copy_from_byte_stream(
          byte_stream, ascii_codepage=codepage)

      for shell_item in iter(shell_item_list.items):
        self._ParseShellItem(parser_mediator, shell_item)
    finally:
      parser_mediator.PopFromParserChain()
