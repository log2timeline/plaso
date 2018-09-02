# -*- coding: utf-8 -*-
"""Plugin to parse .automaticDestinations-ms OLECF files."""

from __future__ import unicode_literals

import os
import re

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import uuid_time as dfdatetime_uuid_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import olecf
from plaso.parsers import winlnk
from plaso.parsers.olecf_plugins import dtfabric_plugin


class AutomaticDestinationsDestListEntryEventData(events.EventData):
  """.automaticDestinations-ms DestList entry event data.

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

  DATA_TYPE = 'olecf:dest_list:entry'

  def __init__(self):
    """Initializes event data."""
    super(AutomaticDestinationsDestListEntryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.birth_droid_file_identifier = None
    self.birth_droid_volume_identifier = None
    self.droid_file_identifier = None
    self.droid_volume_identifier = None
    self.entry_number = None
    self.hostname = None
    self.offset = None
    self.path = None
    self.pin_status = None


class AutomaticDestinationsOLECFPlugin(dtfabric_plugin.DtFabricBaseOLECFPlugin):
  """Plugin that parses an .automaticDestinations-ms OLECF file."""

  NAME = 'olecf_automatic_destinations'
  DESCRIPTION = 'Parser for *.automaticDestinations-ms OLECF files.'

  REQUIRED_ITEMS = frozenset(['DestList'])

  _DEFINITION_FILE = 'automatic_destinations.yaml'

  _RE_LNK_ITEM_NAME = re.compile(r'^[1-9a-f][0-9a-f]*$')

  # We cannot use the parser registry here since winlnk could be disabled.
  # TODO: see if there is a more elegant solution for this.
  _WINLNK_PARSER = winlnk.WinLnkParser()

  def _ParseDistributedTrackingIdentifier(
      self, parser_mediator, uuid_object, origin):
    """Extracts data from a Distributed Tracking identifier.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      uuid_object (uuid.UUID): UUID of the Distributed Tracking identifier.
      origin (str): origin of the event (event source).

    Returns:
      str: UUID string of the Distributed Tracking identifier.
    """
    if uuid_object.version == 1:
      event_data = windows_events.WindowsDistributedLinkTrackingEventData(
          uuid_object, origin)
      date_time = dfdatetime_uuid_time.UUIDTime(timestamp=uuid_object.time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    return '{{{0!s}}}'.format(uuid_object)

  def ParseDestList(self, parser_mediator, olecf_item):
    """Parses the DestList OLECF item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      olecf_item (pyolecf.item): OLECF item.

    Raises:
      UnableToParseFile: if the DestList cannot be parsed.
    """
    header_map = self._GetDataTypeMap('dest_list_header')

    try:
      header, entry_offset = self._ReadStructureFromFileObject(
          olecf_item, 0, header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.UnableToParseFile(
          'Unable to parse DestList header with error: {0!s}'.format(
              exception))

    if header.format_version == 1:
      entry_map = self._GetDataTypeMap('dest_list_entry_v1')
    elif header.format_version in (3, 4):
      entry_map = self._GetDataTypeMap('dest_list_entry_v3')
    else:
      parser_mediator.ProduceExtractionError(
          'unsupported format version: {0:d}.'.format(header.format_version))
      return

    while entry_offset < olecf_item.size:
      try:
        entry, entry_data_size = self._ReadStructureFromFileObject(
            olecf_item, entry_offset, entry_map)
      except (ValueError, errors.ParseError) as exception:
        raise errors.UnableToParseFile(
            'Unable to parse DestList entry with error: {0!s}'.format(
                exception))

      display_name = 'DestList entry at offset: 0x{0:08x}'.format(entry_offset)

      try:
        droid_volume_identifier = self._ParseDistributedTrackingIdentifier(
            parser_mediator, entry.droid_volume_identifier, display_name)

      except (TypeError, ValueError) as exception:
        droid_volume_identifier = ''
        parser_mediator.ProduceExtractionError(
            'unable to read droid volume identifier with error: {0!s}'.format(
                exception))

      try:
        droid_file_identifier = self._ParseDistributedTrackingIdentifier(
            parser_mediator, entry.droid_file_identifier, display_name)

      except (TypeError, ValueError) as exception:
        droid_file_identifier = ''
        parser_mediator.ProduceExtractionError(
            'unable to read droid file identifier with error: {0!s}'.format(
                exception))

      try:
        birth_droid_volume_identifier = (
            self._ParseDistributedTrackingIdentifier(
                parser_mediator, entry.birth_droid_volume_identifier,
                display_name))

      except (TypeError, ValueError) as exception:
        birth_droid_volume_identifier = ''
        parser_mediator.ProduceExtractionError((
            'unable to read birth droid volume identifier with error: '
            '{0:s}').format(
                exception))

      try:
        birth_droid_file_identifier = self._ParseDistributedTrackingIdentifier(
            parser_mediator, entry.birth_droid_file_identifier, display_name)

      except (TypeError, ValueError) as exception:
        birth_droid_file_identifier = ''
        parser_mediator.ProduceExtractionError((
            'unable to read birth droid file identifier with error: '
            '{0:s}').format(
                exception))

      if entry.last_modification_time == 0:
        date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      else:
        date_time = dfdatetime_filetime.Filetime(
            timestamp=entry.last_modification_time)

      event_data = AutomaticDestinationsDestListEntryEventData()
      event_data.birth_droid_file_identifier = birth_droid_file_identifier
      event_data.birth_droid_volume_identifier = birth_droid_volume_identifier
      event_data.droid_file_identifier = droid_file_identifier
      event_data.droid_volume_identifier = droid_volume_identifier
      event_data.entry_number = entry.entry_number
      event_data.hostname = entry.hostname.rstrip('\x00')
      event_data.offset = entry_offset
      event_data.path = entry.path.rstrip('\x00')
      event_data.pin_status = entry.pin_status

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      entry_offset += entry_data_size

  # pylint 1.9.3 wants a docstring for kwargs, but this is not useful to add.
  # pylint: disable=missing-param-doc
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
      raise ValueError('Root item not set.')

    for item in root_item.sub_items:
      if item.name == 'DestList':
        self.ParseDestList(parser_mediator, item)

      elif self._RE_LNK_ITEM_NAME.match(item.name):
        display_name = parser_mediator.GetDisplayName()
        if display_name:
          display_name = '{0:s} # {1:s}'.format(display_name, item.name)
        else:
          display_name = '# {0:s}'.format(item.name)

        parser_mediator.AppendToParserChain(self._WINLNK_PARSER)
        try:
          item.seek(0, os.SEEK_SET)
          self._WINLNK_PARSER.ParseFileLNKFile(
              parser_mediator, item, display_name)
        finally:
          parser_mediator.PopFromParserChain()

        # TODO: check for trailing data?


olecf.OLECFParser.RegisterPlugin(AutomaticDestinationsOLECFPlugin)
