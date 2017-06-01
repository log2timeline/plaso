# -*- coding: utf-8 -*-
"""Plugin to parse .automaticDestinations-ms OLECF files."""

import re
import uuid

import construct

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import uuid_time as dfdatetime_uuid_time

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import olecf
from plaso.parsers import winlnk
from plaso.parsers.olecf_plugins import interface


class AutomaticDestinationsDestListEntryEvent(time_events.DateTimeValuesEvent):
  """Convenience class for an .automaticDestinations-ms DestList entry event.

  Attributes:
    birth_droid_file_identifier (str): birth droid file identifier.
    birth_droid_volume_identifier (str): birth droid volume identifier.
    droid_file_identifier (str): droid file identifier.
    droid_volume_identifier (str): droid volume identifier.
    entry_number (int): DestList entry number.
    path (str): path.
    pin_status (int): pin status.
    offset (int): offset of the DestList entry relative to the start of
        the DestList stream.
  """

  DATA_TYPE = u'olecf:dest_list:entry'

  def __init__(
      self, date_time, date_time_description, entry_offset, dest_list_entry,
      droid_volume_identifier, droid_file_identifier,
      birth_droid_volume_identifier, birth_droid_file_identifier):
    """Initializes an event.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date
          and time values.
      entry_offset (int): offset of the DestList entry relative to the start of
          the DestList stream.
      droid_volume_identifier (str): droid volume identifier.
      droid_file_identifier (str): droid file identifier.
      birth_droid_volume_identifier (str): birth droid volume identifier.
      birth_droid_file_identifier (str): birth droid file identifier.
      dest_list_entry (construct.Struct): DestList entry.
    """
    # TODO: move to parser plugin.
    hostname = binary.ByteStreamCopyToString(
        dest_list_entry.hostname, codepage=u'ascii')
    path = binary.UTF16StreamCopyToString(dest_list_entry.path)

    super(AutomaticDestinationsDestListEntryEvent, self).__init__(
        date_time, date_time_description)
    self.birth_droid_file_identifier = birth_droid_file_identifier
    self.birth_droid_volume_identifier = birth_droid_volume_identifier
    self.droid_file_identifier = droid_file_identifier
    self.droid_volume_identifier = droid_volume_identifier
    self.entry_number = dest_list_entry.entry_number
    self.hostname = hostname
    self.offset = entry_offset
    self.path = path
    self.pin_status = dest_list_entry.pin_status


class AutomaticDestinationsOLECFPlugin(interface.OLECFPlugin):
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

  def _ParseDistributedTrackingIdentifier(
      self, parser_mediator, uuid_data, origin):
    """Extracts data from a Distributed Tracking identifier.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      uuid_data (bytes): UUID data of the Distributed Tracking identifier.
      origin (str): origin of the event (event source).

    Returns:
      str: UUID string of the Distributed Tracking identifier.
    """
    uuid_object = uuid.UUID(bytes_le=uuid_data)

    if uuid_object.version == 1:
      event_data = windows_events.WindowsDistributedLinkTrackingEventData(
          uuid_object, origin)
      date_time = dfdatetime_uuid_time.UUIDTime(timestamp=uuid_object.time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    return u'{{{0!s}}}'.format(uuid_object)

  def ParseDestList(self, parser_mediator, olecf_item):
    """Parses the DestList OLECF item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      olecf_item (pyolecf.item): OLECF item.
    """
    try:
      header = self._DEST_LIST_STREAM_HEADER.parse_stream(olecf_item)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse DestList header with error: {0:s}'.format(
              exception))

    if header.format_version not in (1, 3, 4):
      parser_mediator.ProduceExtractionError(
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

      display_name = u'DestList entry at offset: 0x{0:08x}'.format(entry_offset)

      try:
        droid_volume_identifier = self._ParseDistributedTrackingIdentifier(
            parser_mediator, entry.droid_volume_identifier, display_name)

      except (TypeError, ValueError) as exception:
        droid_volume_identifier = u''
        parser_mediator.ProduceExtractionError(
            u'unable to read droid volume identifier with error: {0:s}'.format(
                exception))

      try:
        droid_file_identifier = self._ParseDistributedTrackingIdentifier(
            parser_mediator, entry.droid_file_identifier, display_name)

      except (TypeError, ValueError) as exception:
        droid_file_identifier = u''
        parser_mediator.ProduceExtractionError(
            u'unable to read droid file identifier with error: {0:s}'.format(
                exception))

      try:
        birth_droid_volume_identifier = (
            self._ParseDistributedTrackingIdentifier(
                parser_mediator, entry.birth_droid_volume_identifier,
                display_name))

      except (TypeError, ValueError) as exception:
        birth_droid_volume_identifier = u''
        parser_mediator.ProduceExtractionError((
            u'unable to read birth droid volume identifier with error: '
            u'{0:s}').format(
                exception))

      try:
        birth_droid_file_identifier = self._ParseDistributedTrackingIdentifier(
            parser_mediator, entry.birth_droid_file_identifier, display_name)

      except (TypeError, ValueError) as exception:
        birth_droid_file_identifier = u''
        parser_mediator.ProduceExtractionError((
            u'unable to read birth droid file identifier with error: '
            u'{0:s}').format(
                exception))

      if entry.last_modification_time == 0:
        date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
      else:
        date_time = dfdatetime_filetime.Filetime(
            timestamp=entry.last_modification_time)

      event = AutomaticDestinationsDestListEntryEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION, entry_offset,
          entry, droid_volume_identifier, droid_file_identifier,
          birth_droid_volume_identifier, birth_droid_file_identifier)
      parser_mediator.ProduceEvent(event)

      entry_offset = olecf_item.get_offset()

  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Parses an OLECF file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      root_item (Optional[pyolecf.item]): root item of the OLECF file.

    Raises:
      ValueError: If the root_item is not set.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(AutomaticDestinationsOLECFPlugin, self).Process(
        parser_mediator, **kwargs)

    if not root_item:
      raise ValueError(u'Root item not set.')

    for item in root_item.sub_items:
      if item.name == u'DestList':
        self.ParseDestList(parser_mediator, item)

      elif self._RE_LNK_ITEM_NAME.match(item.name):
        display_name = parser_mediator.GetDisplayName()
        if display_name:
          display_name = u'{0:s} # {1:s}'.format(display_name, item.name)
        else:
          display_name = u'# {0:s}'.format(item.name)

        self._WINLNK_PARSER.Parse(
            parser_mediator, item, display_name=display_name)

        # TODO: check for trailing data?


olecf.OLECFParser.RegisterPlugin(AutomaticDestinationsOLECFPlugin)
