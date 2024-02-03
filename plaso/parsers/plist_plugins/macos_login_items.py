# -*- coding: utf-8 -*-
"""Plist parser plugin for Mac OS login items plist files."""

import os

from datetime import datetime

from dfdatetime import hfs_time as dfdatetime_hfs_time

from dtfabric import errors as dtfabric_errors
from dtfabric.runtime import data_maps as dtfabric_data_maps

# from plistutils.bookmark import BookmarkParser

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSLoginItemEventData(events.EventData):
  """Mac OS login item event data.

  Attributes:
    cnid_path (str): a "/" delimited string representing an array of CNIDs.
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

  DATA_TYPE = 'macos:login_item:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSLoginItemEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cnid_path = None
    self.hidden = None
    self.name = None
    self.target_creation_time = None
    self.target_path = None
    self.volume_creation_time = None
    self.volume_flags = None
    self.volume_mount_point = None
    self.volume_name = None


class MacOSLoginItemsAliasDataPlistPlugin(
    interface.PlistPlugin, dtfabric_helper.DtFabricHelper):
  """Plist parser plugin for Mac OS login items with AliasData."""

  NAME = 'macos_login_items_plist_with_alias_data'
  DATA_FORMAT = 'Mac OS com.apple.loginitems.plist file with AliasData'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.loginitems.plist')])

  PLIST_KEYS = frozenset(['SessionItems'])

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'alias_data.yaml')

  def _ParseAliasData(self, alias_data, event_data):
    """Parses an AliasData value.

    Args:
      alias_data (bytes): AliasData value.
      event_data (MacOSLoginItemEventData): event data.

    Raises:
      ParseError: if the value cannot be parsed.
    """
    data_type_map = self._GetDataTypeMap('alias_data_record_header')

    record_header = self._ReadStructureFromByteStream(
        alias_data, 0, data_type_map)
    data_offset = 8

    if record_header.application_information != b'\x00\x00\x00\x00':
      raise errors.ParseError('Unsupported AliasData application information')

    if record_header.record_size != len(alias_data):
      raise errors.ParseError('Unsupported AliasData record size')

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

      if tagged_value.value_tag == 0x0001:
        # TODO: determine if this value useful to extract.
        event_data.cnid_path = '/'.join([
            f'{cnid:d}' for cnid in tagged_value.integers])

      elif tagged_value.value_tag == 0x000f:
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

    return record_data

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


class MacOSLoginItemsPlistPlugin(interface.PlistPlugin):
  """Base plist parser plugin for Mac OS login items wth bookmark data."""

  # pylint: disable=abstract-method

  def _ConvertHFSDate(self, alias_date):
    hfs_epoch = dfdatetime_hfs_time.HFSTimeEpoch()
    hfs_epoch_datetime = datetime(
      year=hfs_epoch.year,
      month=hfs_epoch.month,
      day=hfs_epoch.day_of_month,
    )
    hfs_epoch_timedelta = alias_date - hfs_epoch_datetime

    return dfdatetime_hfs_time.HFSTime(
      timestamp=hfs_epoch_timedelta.total_seconds()
    )

  def _ParseBookmark(
      self, parser_mediator, filename, bookmark_index, bookmark_data):
    """Extracts login item information from bookmark data.

      Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfVFS.
      filename (str): filename of the plist file being processed.
      bookmark_index (int): index of the bookmark data in the plist file.
      bookmark_data (bytes): Mac OS bookmark struct data.
    """
    bookmarks = BookmarkParser.parse_bookmark(
        filename, bookmark_index, '$objects', bookmark_data)

    for bookmark in bookmarks:
      event_data = MacOSLoginItemEventData()
      event_data.name = bookmark.get('display_name')
      event_data.cnid_path = bookmark.get('inode_path')
      event_data.volume_name = bookmark.get('volume_name')
      event_data.target_path = bookmark.get('path')
      event_data.volume_mount_point = bookmark.get('volume_path')

      creation_date = bookmark.get('creation_date')
      if creation_date is not None:
        event_data.target_creation_time = self._ConvertHFSDate(creation_date)

      volume_creation_date = bookmark.get('volume_creation_date')
      if volume_creation_date is not None:
        event_data.volume_creation_time = self._ConvertHFSDate(
          volume_creation_date)

      event_data.volume_flags = bookmark.get('volume_props')

      parser_mediator.ProduceEventData(event_data)


class MacOS1013LoginItemsPlugin(MacOSLoginItemsPlistPlugin):
  """Plist parser plugin for Mac OS backgrounditems.btm files."""

  NAME = 'macos_1013_login_items_plist'
  # From High Sierra to Ventura.
  DATA_FORMAT = 'Mac OS 10.13 thru 12.x login items plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('backgrounditems.btm')])

  PLIST_KEYS = frozenset(['$objects'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts login item information from the plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    for i, obj in enumerate(top_level['$objects']):
      if isinstance(obj, bytes):
        filename = parser_mediator.GetFilename()
        self._ParseBookmark(parser_mediator, filename, i, obj)


class MacOS13LoginItemsPlugin(MacOSLoginItemsPlistPlugin):
  """Plist parser plugin for Mac OS BackgroundItems-v4.btm files."""

  NAME = 'macos_13_login_items_plist'
  DATA_FORMAT = 'Mac OS 13+ login items plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PrefixPlistPathFilter('BackgroundItems-v')])

  PLIST_KEYS = frozenset(['$objects'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts login item information from the plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    for i, obj in enumerate(top_level['$objects']):
      if isinstance(obj, bytes):
        filename = parser_mediator.GetFilename()
        self._ParseBookmark(parser_mediator, filename, i, obj)


plist.PlistParser.RegisterPlugins([
    MacOSLoginItemsAliasDataPlistPlugin, MacOS1013LoginItemsPlugin,
    MacOS13LoginItemsPlugin])
