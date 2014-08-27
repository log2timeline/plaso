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
"""Plugin to parse .automaticDestinations-ms OLECF files."""

import logging
import re

import construct

from plaso.events import time_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import winlnk
from plaso.parsers.olecf_plugins import interface


class AutomaticDestinationsDestListEntryEvent(time_events.FiletimeEvent):
  """Convenience class for an .automaticDestinations-ms DestList entry event."""

  DATA_TYPE = 'olecf:dest_list:entry'

  def __init__(
      self, timestamp, timestamp_description, entry_offset, dest_list_entry):
    """Initializes the event object.

    Args:
      timestamp: The FILETIME value for the timestamp.
      timestamp_description: The usage string for the timestamp value.
      entry_offset: The offset of the DestList entry relative to the start of
                    the DestList stream.
      dest_list_entry: The DestList entry (instance of construct.Struct).
    """
    super(AutomaticDestinationsDestListEntryEvent, self).__init__(
        timestamp, timestamp_description)

    self.offset = entry_offset
    self.entry_number = dest_list_entry.entry_number

    self.hostname = binary.ByteStreamCopyToString(
        dest_list_entry.hostname, codepage='ascii')
    self.path = binary.Ut16StreamCopyToString(dest_list_entry.path)
    self.pin_status = dest_list_entry.pin_status

    self.droid_volume_identifier = binary.ByteStreamCopyToGuid(
        dest_list_entry.droid_volume_identifier)
    self.droid_file_identifier = binary.ByteStreamCopyToGuid(
        dest_list_entry.droid_file_identifier)
    self.birth_droid_volume_identifier = binary.ByteStreamCopyToGuid(
        dest_list_entry.birth_droid_volume_identifier)
    self.birth_droid_file_identifier = binary.ByteStreamCopyToGuid(
        dest_list_entry.birth_droid_file_identifier)


class AutomaticDestinationsOlecfPlugin(interface.OlecfPlugin):
  """Plugin that parses an .automaticDestinations-ms OLECF file."""

  NAME = 'olecf_automatic_destinations'

  REQUIRED_ITEMS = frozenset([u'DestList'])

  _RE_LNK_ITEM_NAME = re.compile(r'^[1-9a-f][0-9a-f]*$')

  # We cannot use the parser registry here since winlnk could be disabled.
  # TODO: see if there is a more elagant solution for this.
  _WINLNK_PARSER = winlnk.WinLnkParser()

  _DEST_LIST_STREAM_HEADER = construct.Struct(
      'dest_list_stream_header',
      construct.ULInt32('unknown1'),
      construct.ULInt32('number_of_entries'),
      construct.ULInt32('number_of_pinned_entries'),
      construct.LFloat32('unknown2'),
      construct.ULInt32('last_entry_number'),
      construct.Padding(4),
      construct.ULInt32('last_revision_number'),
      construct.Padding(4))

  _DEST_LIST_STREAM_HEADER_SIZE = _DEST_LIST_STREAM_HEADER.sizeof()

  # Using construct's utf-16 encoding here will create strings with their
  # end-of-string characters exposed. Instead the strings are read as
  # binary strings and converted using ReadUtf16().
  _DEST_LIST_STREAM_ENTRY = construct.Struct(
      'dest_list_stream_entry',
      construct.ULInt64('unknown1'),
      construct.Array(16, construct.Byte('droid_volume_identifier')),
      construct.Array(16, construct.Byte('droid_file_identifier')),
      construct.Array(16, construct.Byte('birth_droid_volume_identifier')),
      construct.Array(16, construct.Byte('birth_droid_file_identifier')),
      construct.String('hostname', 16),
      construct.ULInt32('entry_number'),
      construct.ULInt32('unknown2'),
      construct.LFloat32('unknown3'),
      construct.ULInt64('last_modification_time'),
      construct.ULInt32('pin_status'),
      construct.ULInt16('path_size'),
      construct.String('path', lambda ctx: ctx.path_size * 2))

  def ParseDestList(self, parser_context, olecf_item):
    """Parses the DestList OLECF item.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      olecf_item: An OLECF item (instance of pyolecf.item).
    """
    try:
      header = self._DEST_LIST_STREAM_HEADER.parse_stream(olecf_item)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse DestList header with error: {0:s}'.format(
              exception))

    if header.unknown1 != 1:
      # TODO: add format debugging notes to parser context.
      logging.debug(u'[{0:s}] unknown1 value: {1:d}.'.format(
          self.NAME, header.unknown1))

    entry_offset = olecf_item.get_offset()
    while entry_offset < olecf_item.size:
      try:
        entry = self._DEST_LIST_STREAM_ENTRY.parse_stream(olecf_item)
      except (IOError, construct.FieldError) as exception:
        raise errors.UnableToParseFile(
            u'Unable to parse DestList entry with error: {0:s}'.format(
                exception))

      if not entry:
        break

      event_object = AutomaticDestinationsDestListEntryEvent(
          entry.last_modification_time,
          eventdata.EventTimestamp.MODIFICATION_TIME, entry_offset, entry)
      parser_context.ProduceEvent(event_object, plugin_name=self.NAME)

      entry_offset = olecf_item.get_offset()

  def ParseItems(
      self, parser_context, file_entry=None, root_item=None, **unused_kwargs):
    """Parses OLECF items.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      root_item: Optional root item of the OLECF file. The default is None.

    Raises:
      ValueError: If the root_item is not set.
    """
    if root_item is None:
      raise ValueError(u'Root item not set.')

    for item in root_item.sub_items:
      if item.name  == u'DestList':
        self.ParseDestList(parser_context, item)

      elif self._RE_LNK_ITEM_NAME.match(item.name):
        if file_entry:
          display_name = u'{0:s} # {1:s}'.format(
              parser_context.GetDisplayName(file_entry), item.name)
        else:
          display_name = u'# {0:s}'.format(item.name)

        self._WINLNK_PARSER.ParseFileObject(
            parser_context, item, display_name=display_name)
