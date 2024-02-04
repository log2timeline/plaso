# -*- coding: utf-8 -*-
"""Plist parser plugin for Mac OS background items plist files."""

import os

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSBackgroundItemEventData(events.EventData):
  """Mac OS background item event data.

  Attributes:
    cnid_path (str): a "/" delimited string representing an array of CNIDs.
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

  DATA_TYPE = 'macos:background_items:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSBackgroundItemEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cnid_path = None
    self.name = None
    self.target_creation_time = None
    self.target_path = None
    self.volume_creation_time = None
    self.volume_flags = None
    self.volume_mount_point = None
    self.volume_name = None


class MacOSBackgroundItemsPlistPlugin(
    interface.PlistPlugin, dtfabric_helper.DtFabricHelper):
  """Plist parser plugin for Mac OS background items."""

  NAME = 'macos_background_items_plist'
  DATA_FORMAT = (
      'Mac OS backgrounditems.btm or BackgroundItems-v plist file')

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('backgrounditems.btm'),
      interface.PrefixPlistPathFilter('BackgroundItems-v')])

  PLIST_KEYS = frozenset(['$objects'])

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'bookmark_data.yaml')

  def _ParseBookmarkData(self, bookmark_data, event_data):
    """Parses bookmark data.

    Args:
      bookmark_data (bytes): bookmark data.
      event_data (MacOSLoginItemEventData): event data.

    Raises:
      ParseError: if the value cannot be parsed.
    """
    data_type_map = self._GetDataTypeMap('bookmark_data_header')

    header = self._ReadStructureFromByteStream(
        bookmark_data, 0, data_type_map)

    if header.size != len(bookmark_data):
      raise errors.ParseError('Unsupported bookmark size')

    if header.data_area_offset != 48:
      raise errors.ParseError('Unsupported bookmark data area offset')

    data_type_map = self._GetDataTypeMap('uint32le')

    data_area_size = self._ReadStructureFromByteStream(
        bookmark_data[header.data_area_offset:], header.data_area_offset,
        data_type_map)

    data_type_map = self._GetDataTypeMap('bookmark_data_toc')

    toc_offset = header.data_area_offset + data_area_size

    table_of_contents = self._ReadStructureFromByteStream(
        bookmark_data[toc_offset:], toc_offset, data_type_map)

    if table_of_contents.next_toc_offset != 0:
      raise errors.ParseError('Unsupported next TOC offset')

    relative_target_path = None

    for tagged_value in table_of_contents.tagged_values:
      data_type_map = self._GetDataTypeMap('bookmark_data_record')

      data_record_offset = (
          header.data_area_offset + tagged_value.value_data_record_offset)

      data_record = self._ReadStructureFromByteStream(
          bookmark_data[data_record_offset:], data_record_offset, data_type_map)

      if tagged_value.value_tag == 0x00001004:
        strings_array = self._ParseStringsArray(
            bookmark_data, header.data_area_offset, data_record.integers)

        relative_target_path = '/'.join(strings_array)

      elif tagged_value.value_tag == 0x00001005:
        integers_array = self._ParseIntegersArray(
            bookmark_data, header.data_area_offset, data_record.integers)

        # TODO: determine if this value useful to extract.
        cnid_path = '/'.join([
            f'{cnid:d}' for cnid in integers_array])
        event_data.cnid_path = f'/{cnid_path:s}'

      elif tagged_value.value_tag == 0x00001040:
        data_type_map = self._GetDataTypeMap('float64be')
        cocoa_timestamp = self._ReadStructureFromByteStream(
            data_record.data, 0, data_type_map)

        event_data.target_creation_time = dfdatetime_cocoa_time.CocoaTime(
            timestamp=cocoa_timestamp)

      elif tagged_value.value_tag == 0x00002002:
        volume_mount_point = data_record.string
        if relative_target_path:
          relative_target_path = ''.join([
              volume_mount_point, relative_target_path])

        event_data.volume_mount_point = volume_mount_point

      elif tagged_value.value_tag == 0x00002010:
        event_data.volume_name = data_record.string

      elif tagged_value.value_tag == 0x00002013:
        data_type_map = self._GetDataTypeMap('float64be')
        cocoa_timestamp = self._ReadStructureFromByteStream(
            data_record.data, 0, data_type_map)

        event_data.volume_creation_time = dfdatetime_cocoa_time.CocoaTime(
            timestamp=cocoa_timestamp)

      elif tagged_value.value_tag == 0x00002020:
        data_type_map = self._GetDataTypeMap('bookmark_data_property_flags')
        property_flags = self._ReadStructureFromByteStream(
            data_record.data, 0, data_type_map)

        event_data.volume_flags = (
            property_flags.flags & property_flags.valid_flags_bitmask)

      elif tagged_value.value_tag == 0x0000f017:
        event_data.name = data_record.string

    if relative_target_path:
      event_data.target_path = relative_target_path

  def _ParseIntegersArray(
      self, bookmark_data, data_area_offset, data_record_offsets):
    """Parses an integers array.

    Args:
      bookmark_data (bytes): bookmark data.
      data_area_offset (int): offset of the data area relative to the start of
          the file.
      data_record_offsets (list[int]): offsets of the entry data records.

    Returns:
      list[int]: integers.
    """
    data_type_map = self._GetDataTypeMap('bookmark_data_record')

    integers_array = []

    for data_record_offset in data_record_offsets:
      data_record_offset += data_area_offset
      data_record = self._ReadStructureFromByteStream(
          bookmark_data[data_record_offset:], data_record_offset,
          data_type_map)

      integers_array.append(data_record.integer)

    return integers_array

  def _ParseStringsArray(
      self, bookmark_data, data_area_offset, data_record_offsets):
    """Parses a strings array.

    Args:
      bookmark_data (bytes): bookmark data.
      data_area_offset (int): offset of the data area relative to the start of
          the file.
      data_record_offsets (list[int]): offsets of the entry data records.

    Returns:
      list[str]: strings.
    """
    data_type_map = self._GetDataTypeMap('bookmark_data_record')

    strings_array = []

    for data_record_offset in data_record_offsets:
      data_record_offset += data_area_offset
      data_record = self._ReadStructureFromByteStream(
          bookmark_data[data_record_offset:], data_record_offset,
          data_type_map)

      strings_array.append(data_record.string)

    return strings_array

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts background item information from the plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    for list_element in top_level['$objects']:
      if isinstance(list_element, bytes):
        event_data = MacOSBackgroundItemEventData()

        self._ParseBookmarkData(list_element, event_data)

        parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSBackgroundItemsPlistPlugin)
