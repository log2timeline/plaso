# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS login items plist files."""
from datetime import datetime

from dfdatetime import hfs_time as dfdatetime_hfs_time
from plistutils.alias import AliasParser
from plistutils.bookmark import BookmarkParser

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSLoginItemsEventData(events.EventData):
  """MacOS login items event data.

  Attributes:
    name (str): name.
    hidden (bool): whether this login item is hidden.
    cnid_path: a "/" delimited string representing an array of CNIDs.
    volume_name: the name of the volume containing the target.
    target_path: the full filesystem path to the target.
    volume_mount_point: the location the volume is mounted on the filesystem.
    creation_date: creation date of the login item alias data.
    volume_creation_date: creation date of the volume.
    volume_flags: a string containing ", "-separated names of volume flags.
  """

  DATA_TYPE = 'macos:loginitems:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSLoginItemsEventData, self).__init__(data_type=self.DATA_TYPE)
    self.name = None
    self.hidden = None
    self.cnid_path = None
    self.volume_name = None
    self.target_path = None
    self.volume_mount_point = None
    self.creation_date = None
    self.volume_creation_date = None
    self.volume_flags = None


def _ConvertHFSDate(alias_date: datetime) -> dfdatetime_hfs_time.HFSTime:
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
  parser_mediator,
  filename: str,
  idx: int,
  bookmark_data: bytes
):
  """Extracts login item information from bookmark data.

  Args:
    parser_mediator (ParserMediator): mediates interactions between parsers
      and other components, such as storage and dfVFS.
    filename (str): filename of the plist file being processed.
    idx (int): index of the bookmark data in the plist file.
    bookmark_data (bytes): MacOS bookmark struct data.
  """
  bookmarks = BookmarkParser.parse_bookmark(
    filename, idx, '$objects', bookmark_data
  )
  for bookmark in bookmarks:
    event_data = MacOSLoginItemsEventData()
    event_data.name = bookmark.get('display_name')
    event_data.cnid_path = bookmark.get('inode_path')
    event_data.volume_name = bookmark.get('volume_name')
    event_data.target_path = bookmark.get('path')
    event_data.volume_mount_point = bookmark.get('volume_path')
    creation_date = bookmark.get('creation_date')
    if creation_date is not None:
      event_data.creation_date = _ConvertHFSDate(creation_date)
    volume_creation_date = bookmark.get('volume_creation_date')
    if volume_creation_date is not None:
      event_data.volume_creation_date = _ConvertHFSDate(
        volume_creation_date
      )
    event_data.volume_flags = bookmark.get('volume_props')
    parser_mediator.ProduceEventData(event_data)


class MacOS1012LoginItemsPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS login items plist files.
  """

  NAME = 'macos_1012_login_items_plist'
  DATA_FORMAT = 'MacOS Sierra 10.12 and lower LoginItems plist file'

  PLIST_PATH_FILTERS = frozenset([
    interface.PlistPathFilter('com.apple.loginitems.plist'),
  ])
  PLIST_KEYS = frozenset(['SessionItems'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts login item information from the plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    session_items = top_level.get('SessionItems')
    if session_items:
      custom_list_items = session_items.get('CustomListItems')
      for i, custom_list_item in enumerate(custom_list_items):
        event_data = MacOSLoginItemsEventData()
        event_data.name = custom_list_item.get('Name')
        properties = custom_list_item.get('CustomItemProperties', {})
        event_data.hidden = properties.get(
          'com.apple.LSSharedFileList.ItemIsHidden',
          False,
        )
        alias_data = custom_list_item.get('Alias')
        if alias_data is not None:
          try:
            alias = next(AliasParser.parse(
              parser_mediator.GetFilename(), i, alias_data
            ))
            event_data.cnid_path = alias.get('cnid_path')
            event_data.volume_name = alias.get('volume_name')
            event_data.target_path = alias.get('path')
            event_data.volume_mount_point = alias.get('volume_mount_point')
            creation_date = alias.get('creation_date')
            if creation_date is not None:
              event_data.creation_date = _ConvertHFSDate(creation_date)
            volume_creation_date = alias.get('volume_creation_date')
            if volume_creation_date is not None:
              event_data.volume_creation_date = _ConvertHFSDate(
                volume_creation_date
              )
            event_data.volume_flags = alias.get('volume_flags')
          except StopIteration:
            pass
        parser_mediator.ProduceEventData(event_data)


class MacOS1013LoginItemsPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS backgrounditems.btm plist files.
  """

  NAME = 'macos_1013_login_items_plist'
  # From High Sierra to Ventura.
  DATA_FORMAT = 'MacOS 10.13 thru 12.x login items plist file'

  PLIST_PATH_FILTERS = frozenset([
    interface.PlistPathFilter('backgrounditems.btm'),
  ])
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
        _ParseBookmark(parser_mediator, filename, i, obj)


class MacOS13LoginItemsPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS 13 BackgroundItems-v*.btm plist files.
  """

  NAME = 'macos_13_login_items_plist'
  DATA_FORMAT = 'MacOS 13+ login items plist file'

  PLIST_PATH_FILTERS = frozenset([
    interface.PrefixPlistPathFilter('BackgroundItems-v'),
  ])
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
        _ParseBookmark(parser_mediator, filename, i, obj)


plist.PlistParser.RegisterPlugin(MacOS1012LoginItemsPlugin)
plist.PlistParser.RegisterPlugin(MacOS1013LoginItemsPlugin)
plist.PlistParser.RegisterPlugin(MacOS13LoginItemsPlugin)
