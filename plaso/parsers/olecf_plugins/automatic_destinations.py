# -*- coding: utf-8 -*-
"""Plugin to parse .automaticDestinations-ms OLECF files."""

import re
import uuid

import construct

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import olecf
from plaso.parsers import winlnk
from plaso.parsers.olecf_plugins import interface


class AutomaticDestinationsDestListEntryEvent(time_events.FiletimeEvent):
  """Convenience class for an .automaticDestinations-ms DestList entry event."""

  DATA_TYPE = u'olecf:dest_list:entry'

  def __init__(
      self, timestamp, timestamp_description, entry_offset, dest_list_entry,
      droid_volume_identifier, droid_file_identifier,
      birth_droid_volume_identifier, birth_droid_file_identifier):
    """Initializes the event object.

    Args:
      timestamp: The FILETIME value for the timestamp.
      timestamp_description: The usage string for the timestamp value.
      entry_offset: The offset of the DestList entry relative to the start of
                    the DestList stream.
      droid_volume_identifier: a string containing the droid volume identifier.
      droid_file_identifier: a string containing the droid file identifier.
      birth_droid_volume_identifier: a string containing the birth droid volume
                                     identifier.
      birth_droid_file_identifier: a string containing the birth droid file
                                   identifier.
      dest_list_entry: The DestList entry (instance of construct.Struct).
    """
    super(AutomaticDestinationsDestListEntryEvent, self).__init__(
        timestamp, timestamp_description)

    self.offset = entry_offset
    self.entry_number = dest_list_entry.entry_number

    self.hostname = binary.ByteStreamCopyToString(
        dest_list_entry.hostname, codepage=u'ascii')
    self.path = binary.UTF16StreamCopyToString(dest_list_entry.path)
    self.pin_status = dest_list_entry.pin_status

    self.droid_volume_identifier = droid_volume_identifier
    self.droid_file_identifier = droid_file_identifier
    self.birth_droid_volume_identifier = birth_droid_volume_identifier
    self.birth_droid_file_identifier = birth_droid_file_identifier


class AutomaticDestinationsOlecfPlugin(interface.OlecfPlugin):
  """Plugin that parses an .automaticDestinations-ms OLECF file."""

  NAME = u'olecf_automatic_destinations'
  DESCRIPTION = u'Parser for *.automaticDestinations-ms OLECF files.'

  REQUIRED_ITEMS = frozenset([u'DestList'])

  _RE_LNK_ITEM_NAME = re.compile(r'^[1-9a-f][0-9a-f]*$')

  # We cannot use the parser registry here since winlnk could be disabled.
  # TODO: see if there is a more elegant solution for this.
  _WINLNK_PARSER = winlnk.WinLnkParser()

  _DEST_LIST_STREAM_HEADER = construct.Struct(
      u'dest_list_stream_header',
      construct.ULInt32(u'format_version'),
      construct.ULInt32(u'number_of_entries'),
      construct.ULInt32(u'number_of_pinned_entries'),
      construct.Padding(4),
      construct.ULInt32(u'last_entry_number'),
      construct.Padding(4),
      construct.ULInt32(u'last_revision_number'),
      construct.Padding(4))

  _DEST_LIST_STREAM_HEADER_SIZE = _DEST_LIST_STREAM_HEADER.sizeof()

  # Using Construct's utf-16 encoding here will create strings with their
  # end-of-string characters exposed. Instead the strings are read as
  # binary strings and converted using ReadUTF16().
  _DEST_LIST_STREAM_ENTRY_V1 = construct.Struct(
      u'dest_list_stream_entry_v1',
      construct.Padding(8),
      construct.Bytes(u'droid_volume_identifier', 16),
      construct.Bytes(u'droid_file_identifier', 16),
      construct.Bytes(u'birth_droid_volume_identifier', 16),
      construct.Bytes(u'birth_droid_file_identifier', 16),
      construct.String(u'hostname', 16),
      construct.ULInt32(u'entry_number'),
      construct.Padding(8),
      construct.ULInt64(u'last_modification_time'),
      construct.ULInt32(u'pin_status'),
      construct.ULInt16(u'path_size'),
      construct.String(u'path', lambda ctx: ctx.path_size * 2))

  _DEST_LIST_STREAM_ENTRY_V3 = construct.Struct(
      u'dest_list_stream_entry_v3',
      construct.Padding(8),
      construct.Bytes(u'droid_volume_identifier', 16),
      construct.Bytes(u'droid_file_identifier', 16),
      construct.Bytes(u'birth_droid_volume_identifier', 16),
      construct.Bytes(u'birth_droid_file_identifier', 16),
      construct.String(u'hostname', 16),
      construct.ULInt32(u'entry_number'),
      construct.Padding(8),
      construct.ULInt64(u'last_modification_time'),
      construct.ULInt32(u'pin_status'),
      construct.Padding(16),
      construct.ULInt16(u'path_size'),
      construct.String(u'path', lambda ctx: ctx.path_size * 2),
      construct.Padding(4))

  def ParseDestList(self, parser_mediator, olecf_item):
    """Parses the DestList OLECF item.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      olecf_item: An OLECF item (instance of pyolecf.item).
    """
    try:
      header = self._DEST_LIST_STREAM_HEADER.parse_stream(olecf_item)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse DestList header with error: {0:s}'.format(
              exception))

    if header.format_version not in (1, 3, 4):
      parser_mediator.ProduceParseError(
          u'unsupported format version: {0:d}.'.format(header.format_version))

    if header.format_version == 1:
      dest_list_stream_entry = self._DEST_LIST_STREAM_ENTRY_V1
    elif header.format_version in (3, 4):
      dest_list_stream_entry = self._DEST_LIST_STREAM_ENTRY_V3

    entry_offset = olecf_item.get_offset()
    while entry_offset < olecf_item.size:
      try:
        entry = dest_list_stream_entry.parse_stream(olecf_item)
      except (IOError, construct.FieldError) as exception:
        raise errors.UnableToParseFile(
            u'Unable to parse DestList entry with error: {0:s}'.format(
                exception))

      if not entry:
        break

      display_name = u'Dest list entry at offset: 0x{0:08x}'.format(
          entry_offset)

      try:
        uuid_object = uuid.UUID(bytes_le=entry.droid_volume_identifier)
        droid_volume_identifier = u'{{{0!s}}}'.format(uuid_object)

        if uuid_object.version == 1:
          event_object = (
              windows_events.WindowsDistributedLinkTrackingCreationEvent(
                  uuid_object, display_name))
          parser_mediator.ProduceEvent(event_object)

      except (TypeError, ValueError) as exception:
        droid_volume_identifier = u''
        parser_mediator.ProduceParseError(
            u'unable to read droid volume identifier with error: {0:s}'.format(
                exception))

      try:
        uuid_object = uuid.UUID(bytes_le=entry.droid_file_identifier)
        droid_file_identifier = u'{{{0!s}}}'.format(uuid_object)

        if uuid_object.version == 1:
          event_object = (
              windows_events.WindowsDistributedLinkTrackingCreationEvent(
                  uuid_object, display_name))
          parser_mediator.ProduceEvent(event_object)

      except (TypeError, ValueError) as exception:
        droid_file_identifier = u''
        parser_mediator.ProduceParseError(
            u'unable to read droid file identifier with error: {0:s}'.format(
                exception))

      try:
        uuid_object = uuid.UUID(bytes_le=entry.birth_droid_volume_identifier)
        birth_droid_volume_identifier = u'{{{0!s}}}'.format(uuid_object)

        if uuid_object.version == 1:
          event_object = (
              windows_events.WindowsDistributedLinkTrackingCreationEvent(
                  uuid_object, display_name))
          parser_mediator.ProduceEvent(event_object)

      except (TypeError, ValueError) as exception:
        birth_droid_volume_identifier = u''
        parser_mediator.ProduceParseError((
            u'unable to read birth droid volume identifier with error: '
            u'{0:s}').format(
                exception))

      try:
        uuid_object = uuid.UUID(bytes_le=entry.birth_droid_file_identifier)
        birth_droid_file_identifier = u'{{{0!s}}}'.format(uuid_object)

        if uuid_object.version == 1:
          event_object = (
              windows_events.WindowsDistributedLinkTrackingCreationEvent(
                  uuid_object, display_name))
          parser_mediator.ProduceEvent(event_object)

      except (TypeError, ValueError) as exception:
        birth_droid_file_identifier = u''
        parser_mediator.ProduceParseError((
            u'unable to read birth droid file identifier with error: '
            u'{0:s}').format(
                exception))

      event_object = AutomaticDestinationsDestListEntryEvent(
          entry.last_modification_time,
          eventdata.EventTimestamp.MODIFICATION_TIME, entry_offset, entry,
          droid_volume_identifier, droid_file_identifier,
          birth_droid_volume_identifier, birth_droid_file_identifier)
      parser_mediator.ProduceEvent(event_object)

      entry_offset = olecf_item.get_offset()

  def ParseItems(
      self, parser_mediator, file_entry=None, root_item=None, **unused_kwargs):
    """Parses OLECF items.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
      root_item: Optional root item of the OLECF file.

    Raises:
      ValueError: If the root_item is not set.
    """
    if root_item is None:
      raise ValueError(u'Root item not set.')

    for item in root_item.sub_items:
      if item.name == u'DestList':
        self.ParseDestList(parser_mediator, item)

      elif self._RE_LNK_ITEM_NAME.match(item.name):
        if file_entry:
          display_name = u'{0:s} # {1:s}'.format(
              parser_mediator.GetDisplayName(), item.name)
        else:
          display_name = u'# {0:s}'.format(item.name)

        self._WINLNK_PARSER.Parse(
            parser_mediator, item, display_name=display_name)

        # TODO: check for trailing data?


olecf.OleCfParser.RegisterPlugin(AutomaticDestinationsOlecfPlugin)
