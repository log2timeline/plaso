# -*- coding: utf-8 -*-
"""Plist parser plugin for Mac OS login items plist files."""

import os

from dfdatetime import hfs_time as dfdatetime_hfs_time

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSLoginItemEventData(events.EventData):
  """Mac OS login item event data.

  Attributes:
    hidden (bool): whether this login item is hidden.
    name (str): name.
    target_creation_time (dfdatetime.DateTimeValues): date and time the target
        was created.
    target_path (str): path of the target.
    volume_creation_time (dfdatetime.DateTimeValues): date and time the (target)
        volume was created.
    volume_flags (int): volume flags.
    volume_mount_point (str): location the volume is mounted on the file system.
    volume_name (str): name of the volume containing the target.
  """

  DATA_TYPE = 'macos:login_items:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSLoginItemEventData, self).__init__(data_type=self.DATA_TYPE)
    self.hidden = None
    self.name = None
    self.target_creation_time = None
    self.target_path = None
    self.volume_creation_time = None
    self.volume_flags = None
    self.volume_mount_point = None
    self.volume_name = None


class MacOSLoginItemsPlistPlugin(
    interface.PlistPlugin, dtfabric_helper.DtFabricHelper):
  """Plist parser plugin for Mac OS login items."""

  NAME = 'macos_login_items_plist'
  DATA_FORMAT = 'Mac OS com.apple.loginitems.plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.loginitems.plist')])

  PLIST_KEYS = frozenset(['SessionItems'])

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'alias_data.yaml')

  def _ParseAliasData(self, alias_data, event_data):
    """Parses alias data.

    Args:
      alias_data (bytes): alias data.
      event_data (MacOSLoginItemEventData): event data.

    Raises:
      ParseError: if the value cannot be parsed.
    """
    data_type_map = self._GetDataTypeMap('alias_data_record_header')

    record_header = self._ReadStructureFromByteStream(
        alias_data, 0, data_type_map)
    data_offset = 8

    if record_header.application_information != b'\x00\x00\x00\x00':
      raise errors.ParseError('Unsupported alias application information')

    if record_header.record_size != len(alias_data):
      raise errors.ParseError('Unsupported alias record size')

    # TODO: add format version 2 support, but need test data.
    data_type_map = self._GetDataTypeMap('alias_data_record_v3')

    record_data = self._ReadStructureFromByteStream(
        alias_data[data_offset:], data_offset, data_type_map)
    data_offset += 50

    hfs_timestamp, _ = divmod(record_data.target_creation_time, 65536)
    event_data.target_creation_time = dfdatetime_hfs_time.HFSTime(
        timestamp=hfs_timestamp)

    event_data.volume_flags = record_data.volume_flags

    hfs_timestamp, _ = divmod(record_data.volume_creation_time, 65536)
    event_data.volume_creation_time = dfdatetime_hfs_time.HFSTime(
        timestamp=hfs_timestamp)

    relative_target_path = None

    while data_offset < record_header.record_size:
      data_type_map = self._GetDataTypeMap('alias_data_tagged_value')

      context = dtfabric_data_maps.DataTypeMapContext()

      tagged_value = self._ReadStructureFromByteStream(
          alias_data[data_offset:], data_offset, data_type_map,
          context=context)
      data_offset += context.byte_size

      if tagged_value.value_tag == 0xffff:
        break

      if tagged_value.value_tag == 0x000f:
        event_data.volume_name = tagged_value.string

      elif tagged_value.value_tag == 0x0012:
        relative_target_path = tagged_value.string

      elif tagged_value.value_tag == 0x0013:
        volume_mount_point = tagged_value.string
        if relative_target_path:
          relative_target_path = ''.join([
              volume_mount_point, relative_target_path])

        event_data.volume_mount_point = volume_mount_point

    if relative_target_path:
      event_data.target_path = relative_target_path

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts login item information from the plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    session_items = top_level.get('SessionItems')
    if not session_items:
      return

    for custom_list_item in session_items.get('CustomListItems'):
      alias_data = custom_list_item.get('Alias')
      properties = custom_list_item.get('CustomItemProperties', {})

      event_data = MacOSLoginItemEventData()
      event_data.name = custom_list_item.get('Name')
      event_data.hidden = properties.get(
          'com.apple.LSSharedFileList.ItemIsHidden', False)

      if alias_data is not None:
        self._ParseAliasData(alias_data, event_data)

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSLoginItemsPlistPlugin)
