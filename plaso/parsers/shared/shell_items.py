#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

  def _BuildParserChain(self, parser_chain=None):
    """Return the parser chain with the addition of the current parser.

    Args:
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.

    Returns:
      The parser chain, with the addition of the current parser.
    """
    if not parser_chain:
      return self.NAME

    return u'/'.join([parser_chain, self.NAME])


  def _ParseShellItem(
      self, parser_context, shell_item, file_entry=None, parser_chain=None):
    """Parses a shell item.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      shell_item: the shell item (instance of pyfwsi.item).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
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
            parser_context.ProduceEvent(
                event_object, file_entry=file_entry,
                parser_chain=parser_chain)

          fat_date_time = extension_block.get_access_time_as_integer()
          if fat_date_time:
            event_object = shell_item_events.ShellItemFileEntryEvent(
                fat_date_time, eventdata.EventTimestamp.ACCESS_TIME,
                shell_item.name, long_name, localized_name, file_reference,
                self._origin)
            parser_context.ProduceEvent(
                event_object, file_entry=file_entry,
                parser_chain=parser_chain)

      fat_date_time = shell_item.get_modification_time_as_integer()
      if fat_date_time:
        event_object = shell_item_events.ShellItemFileEntryEvent(
            fat_date_time, eventdata.EventTimestamp.MODIFICATION_TIME,
            shell_item.name, long_name, localized_name, file_reference,
            self._origin)
        parser_context.ProduceEvent(
            event_object, file_entry=file_entry,
            parser_chain=parser_chain)

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

  def Parse(
      self, parser_context, byte_stream, codepage='cp1252',
      file_entry=None, parser_chain=None):
    """Parses the shell items from the byte stream.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      byte_stream: a string holding the shell items data.
      codepage: Optional byte stream codepage. The default is cp1252.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
    """
    self._path_segments = []
    shell_item_list = pyfwsi.item_list()
    shell_item_list.copy_from_byte_stream(byte_stream, ascii_codepage=codepage)
    # Add ourselves to the parser chain, so it is used for subsequent object
    # creation.
    parser_chain = self._BuildParserChain(parser_chain)

    for shell_item in shell_item_list.items:
      self._ParseShellItem(
          parser_context, shell_item, file_entry=file_entry,
          parser_chain=parser_chain)
