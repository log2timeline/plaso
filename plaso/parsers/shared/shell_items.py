# -*- coding: utf-8 -*-
"""Parser for Windows NT shell items."""

import pyfwsi

from plaso.events import shell_item_events
from plaso.lib import eventdata
from plaso.winnt import shell_folder_ids


if pyfwsi.get_version() < '20140714':
  raise ImportWarning(
      u'Shell item support functions require at least pyfwsi 20140714.')


class ShellItemsParser(object):
  """Parses for Windows NT shell items."""

  NAME = 'shell_items'

  def __init__(self, origin):
    """Initializes the parser.

    Args:
      origin: A string containing the origin of the event (event source).
    """
    super(ShellItemsParser, self).__init__()
    self._origin = origin
    self._path_segments = []

  def _ParseShellItem(
      self, parser_mediator, shell_item):
    """Parses a shell item.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      shell_item: the shell item (instance of pyfwsi.item).
    """
    path_segment = None

    if isinstance(shell_item, pyfwsi.root_folder):
      description = shell_folder_ids.DESCRIPTIONS.get(
          shell_item.shell_folder_identifier, None)

      if description:
        path_segment = description
      else:
        path_segment = u'{{{0:s}}}'.format(shell_item.shell_folder_identifier)

    elif isinstance(shell_item, pyfwsi.volume):
      if shell_item.name:
        path_segment = shell_item.name
      elif shell_item.identifier:
        path_segment = u'{{{0:s}}}'.format(shell_item.identifier)

    elif isinstance(shell_item, pyfwsi.file_entry):
      long_name = u''
      localized_name = u''
      file_reference = u''
      for extension_block in shell_item.extension_blocks:
        if isinstance(extension_block, pyfwsi.file_entry_extension):
          long_name = extension_block.long_name
          localized_name = extension_block.localized_name
          file_reference = extension_block.file_reference
          if file_reference:
            file_reference = u'{0:d}-{1:d}'.format(
                file_reference & 0xffffffffffff, file_reference >> 48)

          fat_date_time = extension_block.get_creation_time_as_integer()
          if fat_date_time:
            event_object = shell_item_events.ShellItemFileEntryEvent(
                fat_date_time, eventdata.EventTimestamp.CREATION_TIME,
                shell_item.name, long_name, localized_name, file_reference,
                self._origin)
            parser_mediator.ProduceEvent(event_object)

          fat_date_time = extension_block.get_access_time_as_integer()
          if fat_date_time:
            event_object = shell_item_events.ShellItemFileEntryEvent(
                fat_date_time, eventdata.EventTimestamp.ACCESS_TIME,
                shell_item.name, long_name, localized_name, file_reference,
                self._origin)
            parser_mediator.ProduceEvent(event_object)

      fat_date_time = shell_item.get_modification_time_as_integer()
      if fat_date_time:
        event_object = shell_item_events.ShellItemFileEntryEvent(
            fat_date_time, eventdata.EventTimestamp.MODIFICATION_TIME,
            shell_item.name, long_name, localized_name, file_reference,
            self._origin)
        parser_mediator.ProduceEvent(event_object)

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
      path_segment = u'UNKNOWN: 0x{0:02x}'.format(shell_item.class_type)

    self._path_segments.append(path_segment)

  def CopyToPath(self):
    """Copies the shell items to a path.

    Returns:
      A Unicode string containing the converted shell item list path or None.
    """
    if not self._path_segments:
      return

    return u', '.join(self._path_segments)

  def Parse(self, parser_mediator, byte_stream, codepage='cp1252'):
    """Parses the shell items from the byte stream.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      byte_stream: a string holding the shell items data.
      codepage: Optional byte stream codepage. The default is cp1252.
    """
    self._path_segments = []
    shell_item_list = pyfwsi.item_list()
    shell_item_list.copy_from_byte_stream(byte_stream, ascii_codepage=codepage)

    for shell_item in shell_item_list.items:
      self._ParseShellItem(parser_mediator, shell_item)

  def UpdateChainAndParse(
      self, parser_mediator, byte_stream, codepage='cp1252'):
    """Wrapper for Parse() to synchronize the parser chain.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      byte_stream: a string holding the shell items data.
      codepage: Optional byte stream codepage. The default is cp1252.
    """
    parser_mediator.AppendToParserChain(self)
    try:
      self.Parse(parser_mediator, byte_stream, codepage)
    finally:
      parser_mediator.PopFromParserChain()
