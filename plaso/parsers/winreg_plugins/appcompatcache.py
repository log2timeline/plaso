# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the Application Compatibility Cache key."""

import os

from dfdatetime import filetime as dfdatetime_filetime

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class AppCompatCacheEventData(events.EventData):
  """Application Compatibility Cache event data.

  Attributes:
    entry_index (int): cache entry index number for the record.
    file_entry_modification_time (dfdatetime.DateTimeValues): last modification
        date and time of the corresponding file entry.
    key_path (str): Windows Registry key path.
    last_update_time (dfdatetime.DateTimeValues): last update date and time of
        the Application Compatibility Cache entry.
    offset (int): offset of the Application Compatibility Cache entry relative
        to the start of the Windows Registry value data, from which the event
        data was extracted.
    path (str): full path to the executable.
  """

  DATA_TYPE = 'windows:registry:appcompatcache'

  def __init__(self):
    """Initializes event data."""
    super(AppCompatCacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entry_index = None
    self.file_entry_modification_time = None
    self.key_path = None
    self.last_update_time = None
    self.offset = None
    self.path = None


class AppCompatCacheHeader(object):
  """Application Compatibility Cache header."""

  def __init__(self):
    """Initializes the header object."""
    super(AppCompatCacheHeader, self).__init__()
    self.number_of_cached_entries = 0
    self.header_size = 0


class AppCompatCacheCachedEntry(object):
  """Application Compatibility Cache cached entry."""

  def __init__(self):
    """Initializes the cached entry object."""
    super(AppCompatCacheCachedEntry, self).__init__()
    self.cached_entry_size = 0
    self.data = None
    self.file_size = None
    self.insertion_flags = None
    self.last_modification_time = None
    self.last_update_time = None
    self.shim_flags = None
    self.path = None


class AppCompatCacheWindowsRegistryPlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper):
  """Application Compatibility Cache data Windows Registry plugin."""

  NAME = 'appcompatcache'
  DATA_FORMAT = 'Application Compatibility Cache Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          'Session Manager\\AppCompatibility'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          'Session Manager\\AppCompatCache')])

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'appcompatcache.yaml')

  _FORMAT_TYPE_2000 = 1
  _FORMAT_TYPE_XP = 2
  _FORMAT_TYPE_2003 = 3
  _FORMAT_TYPE_VISTA = 4
  _FORMAT_TYPE_7 = 5
  _FORMAT_TYPE_8 = 6
  _FORMAT_TYPE_10 = 7

  _HEADER_SIGNATURES = {
      # AppCompatCache format signature used in Windows XP.
      0xdeadbeef: _FORMAT_TYPE_XP,
      # AppCompatCache format signature used in Windows 2003, Vista and 2008.
      0xbadc0ffe: _FORMAT_TYPE_2003,
      # AppCompatCache format signature used in Windows 7 and 2008 R2.
      0xbadc0fee: _FORMAT_TYPE_7,
      # AppCompatCache format signature used in Windows 8.0 and 8.1.
      0x00000080: _FORMAT_TYPE_8,
      # AppCompatCache format signatures used in Windows 10
      0x00000030: _FORMAT_TYPE_10,
      0x00000034: _FORMAT_TYPE_10}

  _HEADER_DATA_TYPE_MAP_NAMES = {
      _FORMAT_TYPE_XP: 'appcompatcache_header_xp_32bit',
      _FORMAT_TYPE_2003: 'appcompatcache_header_2003',
      _FORMAT_TYPE_VISTA: 'appcompatcache_header_vista',
      _FORMAT_TYPE_7: 'appcompatcache_header_7',
      _FORMAT_TYPE_8: 'appcompatcache_header_8',
      _FORMAT_TYPE_10: 'appcompatcache_header_10'}

  _SUPPORTED_FORMAT_TYPES = frozenset(_HEADER_DATA_TYPE_MAP_NAMES.keys())

  # AppCompatCache format used in Windows 8.0.
  _CACHED_ENTRY_SIGNATURE_8_0 = b'00ts'

  # AppCompatCache format used in Windows 8.1.
  _CACHED_ENTRY_SIGNATURE_8_1 = b'10ts'

  def __init__(self):
    """Initializes a Application Compatibility Cache Registry plugin."""
    super(AppCompatCacheWindowsRegistryPlugin, self).__init__()
    self._cached_entry_data_type_map = None

  def _CheckSignature(self, value_data):
    """Parses and validates the signature.

    Args:
      value_data (bytes): value data.

    Returns:
      int: format type or None if format could not be determined.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    signature_map = self._GetDataTypeMap('uint32le')

    try:
      signature = self._ReadStructureFromByteStream(
          value_data, 0, signature_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse signature value with error: {0!s}'.format(
              exception))

    format_type = self._HEADER_SIGNATURES.get(signature, None)

    if format_type == self._FORMAT_TYPE_2003:
      # TODO: determine which format version is used (2003 or Vista).
      return self._FORMAT_TYPE_2003

    if format_type == self._FORMAT_TYPE_8:
      cached_entry_signature = value_data[signature:signature + 4]
      if cached_entry_signature in (
          self._CACHED_ENTRY_SIGNATURE_8_0, self._CACHED_ENTRY_SIGNATURE_8_1):
        return self._FORMAT_TYPE_8

    elif format_type == self._FORMAT_TYPE_10:
      # Windows 10 uses the same cache entry signature as Windows 8.1
      cached_entry_signature = value_data[signature:signature + 4]
      if cached_entry_signature == self._CACHED_ENTRY_SIGNATURE_8_1:
        return self._FORMAT_TYPE_10

    return format_type

  def _GetCachedEntryDataTypeMap(
      self, format_type, value_data, cached_entry_offset):
    """Determines the cached entry data type map.

    Args:
      format_type (int): format type.
      value_data (bytes): value data.
      cached_entry_offset (int): offset of the first cached entry data
          relative to the start of the value data.

    Returns:
      dtfabric.DataTypeMap: data type map which contains a data type definition,
          such as a structure, that can be mapped onto binary data or None
          if the data type map is not defined.

    Raises:
      ParseError: if the cached entry data type map cannot be determined.
    """
    if format_type not in self._SUPPORTED_FORMAT_TYPES:
      raise errors.ParseError('Unsupported format type: {0:d}'.format(
          format_type))

    data_type_map_name = ''

    if format_type == self._FORMAT_TYPE_XP:
      data_type_map_name = 'appcompatcache_cached_entry_xp_32bit'

    elif format_type in (self._FORMAT_TYPE_8, self._FORMAT_TYPE_10):
      data_type_map_name = 'appcompatcache_cached_entry_header_8'

    else:
      cached_entry = self._ParseCommon2003CachedEntry(
          value_data, cached_entry_offset)

      # Assume the entry is 64-bit if the 32-bit path offset is 0 and
      # the 64-bit path offset is set.
      if (cached_entry.path_offset_32bit == 0 and
          cached_entry.path_offset_64bit != 0):
        number_of_bits = '64'
      else:
        number_of_bits = '32'

      if format_type == self._FORMAT_TYPE_2003:
        data_type_map_name = (
            'appcompatcache_cached_entry_2003_{0:s}bit'.format(number_of_bits))
      elif format_type == self._FORMAT_TYPE_VISTA:
        data_type_map_name = (
            'appcompatcache_cached_entry_vista_{0:s}bit'.format(number_of_bits))
      elif format_type == self._FORMAT_TYPE_7:
        data_type_map_name = (
            'appcompatcache_cached_entry_7_{0:s}bit'.format(number_of_bits))

    return self._GetDataTypeMap(data_type_map_name)

  def _ParseCommon2003CachedEntry(self, value_data, cached_entry_offset):
    """Parses the cached entry structure common for Windows 2003, Vista and 7.

    Args:
      value_data (bytes): value data.
      cached_entry_offset (int): offset of the first cached entry data
          relative to the start of the value data.

    Returns:
      appcompatcache_cached_entry_2003_common: cached entry structure common
          for Windows 2003, Windows Vista and Windows 7.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    data_type_map = self._GetDataTypeMap(
        'appcompatcache_cached_entry_2003_common')

    try:
      cached_entry = self._ReadStructureFromByteStream(
          value_data[cached_entry_offset:], cached_entry_offset, data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse cached entry value with error: {0!s}'.format(
              exception))

    if cached_entry.path_size > cached_entry.maximum_path_size:
      raise errors.ParseError('Path size value out of bounds.')

    path_end_of_string_size = (
        cached_entry.maximum_path_size - cached_entry.path_size)
    if cached_entry.path_size == 0 or path_end_of_string_size != 2:
      raise errors.ParseError('Unsupported path size values.')

    return cached_entry

  def _ParseCachedEntryXP(self, value_data, cached_entry_offset):
    """Parses a Windows XP cached entry.

    Args:
      value_data (bytes): value data.
      cached_entry_offset (int): offset of the first cached entry data
          relative to the start of the value data.

    Returns:
      AppCompatCacheCachedEntry: cached entry.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    context = dtfabric_data_maps.DataTypeMapContext()

    try:
      cached_entry = self._ReadStructureFromByteStream(
          value_data[cached_entry_offset:], cached_entry_offset,
          self._cached_entry_data_type_map, context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse cached entry value with error: {0!s}'.format(
              exception))

    # TODO: have dtFabric handle string conversion.
    string_size = 0
    for string_index in range(0, 528, 2):
      if (cached_entry.path[string_index] == 0 and
          cached_entry.path[string_index + 1] == 0):
        break
      string_size += 2

    try:
      path = bytearray(cached_entry.path[0:string_size]).decode('utf-16-le')
    except UnicodeDecodeError:
      raise errors.ParseError('Unable to decode cached entry path to string')

    cached_entry_object = AppCompatCacheCachedEntry()
    cached_entry_object.cached_entry_size = context.byte_size
    cached_entry_object.file_size = cached_entry.file_size
    cached_entry_object.last_modification_time = (
        cached_entry.last_modification_time)
    cached_entry_object.last_update_time = cached_entry.last_update_time
    cached_entry_object.path = path

    return cached_entry_object

  def _ParseCachedEntry2003(self, value_data, cached_entry_offset):
    """Parses a Windows 2003 cached entry.

    Args:
      value_data (bytes): value data.
      cached_entry_offset (int): offset of the first cached entry data
          relative to the start of the value data.

    Returns:
      AppCompatCacheCachedEntry: cached entry.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    context = dtfabric_data_maps.DataTypeMapContext()

    try:
      cached_entry = self._ReadStructureFromByteStream(
          value_data[cached_entry_offset:], cached_entry_offset,
          self._cached_entry_data_type_map, context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse cached entry value with error: {0!s}'.format(
              exception))

    path_size = cached_entry.path_size
    maximum_path_size = cached_entry.maximum_path_size
    path_offset = cached_entry.path_offset

    if path_offset > 0 and path_size > 0:
      path_size += path_offset
      maximum_path_size += path_offset

      try:
        path = value_data[path_offset:path_size].decode('utf-16-le')
      except UnicodeDecodeError:
        raise errors.ParseError('Unable to decode cached entry path to string')

    cached_entry_object = AppCompatCacheCachedEntry()
    cached_entry_object.cached_entry_size = context.byte_size
    cached_entry_object.file_size = getattr(cached_entry, 'file_size', None)
    cached_entry_object.last_modification_time = (
        cached_entry.last_modification_time)
    cached_entry_object.path = path

    return cached_entry_object

  def _ParseCachedEntryVista(self, value_data, cached_entry_offset):
    """Parses a Windows Vista cached entry.

    Args:
      value_data (bytes): value data.
      cached_entry_offset (int): offset of the first cached entry data
          relative to the start of the value data.

    Returns:
      AppCompatCacheCachedEntry: cached entry.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    context = dtfabric_data_maps.DataTypeMapContext()

    try:
      cached_entry = self._ReadStructureFromByteStream(
          value_data[cached_entry_offset:], cached_entry_offset,
          self._cached_entry_data_type_map, context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse cached entry value with error: {0!s}'.format(
              exception))

    path_size = cached_entry.path_size
    maximum_path_size = cached_entry.maximum_path_size
    path_offset = cached_entry.path_offset

    if path_offset > 0 and path_size > 0:
      path_size += path_offset
      maximum_path_size += path_offset

      try:
        path = value_data[path_offset:path_size].decode('utf-16-le')
      except UnicodeDecodeError:
        raise errors.ParseError('Unable to decode cached entry path to string')

    cached_entry_object = AppCompatCacheCachedEntry()
    cached_entry_object.cached_entry_size = context.byte_size
    cached_entry_object.insertion_flags = cached_entry.insertion_flags
    cached_entry_object.last_modification_time = (
        cached_entry.last_modification_time)
    cached_entry_object.path = path
    cached_entry_object.shim_flags = cached_entry.shim_flags

    return cached_entry_object

  def _ParseCachedEntry7(self, value_data, cached_entry_offset):
    """Parses a Windows 7 cached entry.

    Args:
      value_data (bytes): value data.
      cached_entry_offset (int): offset of the first cached entry data
          relative to the start of the value data.

    Returns:
      AppCompatCacheCachedEntry: cached entry.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    context = dtfabric_data_maps.DataTypeMapContext()

    try:
      cached_entry = self._ReadStructureFromByteStream(
          value_data[cached_entry_offset:], cached_entry_offset,
          self._cached_entry_data_type_map, context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse cached entry value with error: {0!s}'.format(
              exception))

    path_size = cached_entry.path_size
    maximum_path_size = cached_entry.maximum_path_size
    path_offset = cached_entry.path_offset

    if path_offset > 0 and path_size > 0:
      path_size += path_offset
      maximum_path_size += path_offset

      try:
        path = value_data[path_offset:path_size].decode('utf-16-le')
      except UnicodeDecodeError:
        raise errors.ParseError('Unable to decode cached entry path to string')

    data_offset = cached_entry.data_offset
    data_size = cached_entry.data_size

    cached_entry_object = AppCompatCacheCachedEntry()
    cached_entry_object.cached_entry_size = context.byte_size
    cached_entry_object.insertion_flags = cached_entry.insertion_flags
    cached_entry_object.last_modification_time = (
        cached_entry.last_modification_time)
    cached_entry_object.path = path
    cached_entry_object.shim_flags = cached_entry.shim_flags

    if data_size > 0:
      cached_entry_object.data = value_data[data_offset:data_offset + data_size]

    return cached_entry_object

  def _ParseCachedEntry8(self, value_data, cached_entry_offset):
    """Parses a Windows 8.0 or 8.1 cached entry.

    Args:
      value_data (bytes): value data.
      cached_entry_offset (int): offset of the first cached entry data
          relative to the start of the value data.

    Returns:
      AppCompatCacheCachedEntry: cached entry.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    try:
      cached_entry = self._ReadStructureFromByteStream(
          value_data[cached_entry_offset:], cached_entry_offset,
          self._cached_entry_data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse cached entry value with error: {0!s}'.format(
              exception))

    if cached_entry.signature not in (
        self._CACHED_ENTRY_SIGNATURE_8_0, self._CACHED_ENTRY_SIGNATURE_8_1):
      raise errors.ParseError('Unsupported cache entry signature')

    cached_entry_data = value_data[cached_entry_offset:]

    if cached_entry.signature == self._CACHED_ENTRY_SIGNATURE_8_0:
      data_type_map_name = 'appcompatcache_cached_entry_body_8_0'
    elif cached_entry.signature == self._CACHED_ENTRY_SIGNATURE_8_1:
      data_type_map_name = 'appcompatcache_cached_entry_body_8_1'

    data_type_map = self._GetDataTypeMap(data_type_map_name)
    context = dtfabric_data_maps.DataTypeMapContext()

    try:
      cached_entry_body = self._ReadStructureFromByteStream(
          cached_entry_data[12:], cached_entry_offset + 12,
          data_type_map, context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse cached entry body with error: {0!s}'.format(
              exception))

    data_offset = context.byte_size
    data_size = cached_entry_body.data_size

    cached_entry_object = AppCompatCacheCachedEntry()
    cached_entry_object.cached_entry_size = (
        12 + cached_entry.cached_entry_data_size)
    cached_entry_object.insertion_flags = cached_entry_body.insertion_flags
    cached_entry_object.last_modification_time = (
        cached_entry_body.last_modification_time)
    cached_entry_object.path = cached_entry_body.path
    cached_entry_object.shim_flags = cached_entry_body.shim_flags

    if data_size > 0:
      cached_entry_object.data = cached_entry_data[
          data_offset:data_offset + data_size]

    return cached_entry_object

  def _ParseCachedEntry10(self, value_data, cached_entry_offset):
    """Parses a Windows 10 cached entry.

    Args:
      value_data (bytes): value data.
      cached_entry_offset (int): offset of the first cached entry data
          relative to the start of the value data.

    Returns:
      AppCompatCacheCachedEntry: cached entry.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    try:
      cached_entry = self._ReadStructureFromByteStream(
          value_data[cached_entry_offset:], cached_entry_offset,
          self._cached_entry_data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse cached entry value with error: {0!s}'.format(
              exception))

    if cached_entry.signature not in (
        self._CACHED_ENTRY_SIGNATURE_8_0, self._CACHED_ENTRY_SIGNATURE_8_1):
      raise errors.ParseError('Unsupported cache entry signature')

    cached_entry_data = value_data[cached_entry_offset:]

    data_type_map = self._GetDataTypeMap('appcompatcache_cached_entry_body_10')
    context = dtfabric_data_maps.DataTypeMapContext()

    try:
      cached_entry_body = self._ReadStructureFromByteStream(
          cached_entry_data[12:], cached_entry_offset + 12,
          data_type_map, context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse cached entry body with error: {0!s}'.format(
              exception))

    data_offset = cached_entry_offset + context.byte_size
    data_size = cached_entry_body.data_size

    cached_entry_object = AppCompatCacheCachedEntry()
    cached_entry_object.cached_entry_size = (
        12 + cached_entry.cached_entry_data_size)
    cached_entry_object.last_modification_time = (
        cached_entry_body.last_modification_time)
    cached_entry_object.path = cached_entry_body.path

    if data_size > 0:
      cached_entry_object.data = cached_entry_data[
          data_offset:data_offset + data_size]

    return cached_entry_object

  def _ParseHeader(self, format_type, value_data):
    """Parses the header.

    Args:
      format_type (int): format type.
      value_data (bytes): value data.

    Returns:
      AppCompatCacheHeader: header.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    data_type_map_name = self._HEADER_DATA_TYPE_MAP_NAMES.get(format_type, None)
    if not data_type_map_name:
      raise errors.ParseError(
          'Unsupported format type: {0:d}'.format(format_type))

    data_type_map = self._GetDataTypeMap(data_type_map_name)
    context = dtfabric_data_maps.DataTypeMapContext()

    try:
      header = self._ReadStructureFromByteStream(
          value_data, 0, data_type_map, context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse header value with error: {0!s}'.format(
              exception))

    header_data_size = context.byte_size
    if format_type == self._FORMAT_TYPE_10:
      header_data_size = header.signature

    cache_header = AppCompatCacheHeader()
    cache_header.header_size = header_data_size
    cache_header.number_of_cached_entries = getattr(
        header, 'number_of_cached_entries', 0)

    return cache_header

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    value = registry_key.GetValueByName('AppCompatCache')
    if not value:
      return

    value_data = value.data
    value_data_size = len(value.data)

    format_type = self._CheckSignature(value_data)
    if not format_type:
      parser_mediator.ProduceExtractionWarning(
          'Unsupported signature in AppCompatCache key: {0:s}'.format(
              registry_key.path))
      return

    header_object = self._ParseHeader(format_type, value_data)

    # On Windows Vista and 2008 when the cache is empty it will
    # only consist of the header.
    if value_data_size <= header_object.header_size:
      return

    cached_entry_offset = header_object.header_size

    self._cached_entry_data_type_map = self._GetCachedEntryDataTypeMap(
        format_type, value_data, cached_entry_offset)
    if not self._cached_entry_data_type_map:
      raise errors.ParseError('Unable to determine cached entry data type.')

    parse_cached_entry_function = None
    if format_type == self._FORMAT_TYPE_XP:
      parse_cached_entry_function = self._ParseCachedEntryXP
    elif format_type == self._FORMAT_TYPE_2003:
      parse_cached_entry_function = self._ParseCachedEntry2003
    elif format_type == self._FORMAT_TYPE_VISTA:
      parse_cached_entry_function = self._ParseCachedEntryVista
    elif format_type == self._FORMAT_TYPE_7:
      parse_cached_entry_function = self._ParseCachedEntry7
    elif format_type == self._FORMAT_TYPE_8:
      parse_cached_entry_function = self._ParseCachedEntry8
    elif format_type == self._FORMAT_TYPE_10:
      parse_cached_entry_function = self._ParseCachedEntry10

    cached_entry_index = 0
    while cached_entry_offset < value_data_size:
      cached_entry_object = parse_cached_entry_function(
          value_data, cached_entry_offset)

      event_data = AppCompatCacheEventData()
      event_data.entry_index = cached_entry_index + 1
      event_data.key_path = registry_key.path
      event_data.offset = cached_entry_offset
      event_data.path = cached_entry_object.path

      if cached_entry_object.last_modification_time:
        event_data.file_entry_modification_time = dfdatetime_filetime.Filetime(
            timestamp=cached_entry_object.last_modification_time)

      if cached_entry_object.last_update_time:
        event_data.last_update_time = dfdatetime_filetime.Filetime(
            timestamp=cached_entry_object.last_update_time)

      parser_mediator.ProduceEventData(event_data)

      cached_entry_offset += cached_entry_object.cached_entry_size
      cached_entry_index += 1

      if (header_object.number_of_cached_entries != 0 and
          cached_entry_index >= header_object.number_of_cached_entries):
        break


winreg_parser.WinRegistryParser.RegisterPlugin(
    AppCompatCacheWindowsRegistryPlugin)
