# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) file parser."""

import base64
import binascii
import decimal
import ipaddress
import os
import re
import stat

import plistlib

import lz4.block

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.helpers import sqlite
from plaso.helpers.macos import darwin
from plaso.helpers.macos import dns
from plaso.helpers.macos import location
from plaso.helpers.macos import opendirectory
from plaso.helpers.macos import tcp
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers.shared.unified_logging import dsc
from plaso.parsers.shared.unified_logging import timesync
from plaso.parsers.shared.unified_logging import uuidtext


# ARM Processor Timebase Adjustment
ARM_TIMEBASE_NUMERATOR = 125
ARM_TIMEBASE_DENOMINATOR = 3

# Flags
CURRENT_AID = 0x1
UNIQUE_PID = 0x10
PRIVATE_STRING_RANGE = 0x100
HAS_MESSAGE_IN_UUIDTEXT = 0x0002
HAS_ALTERNATE_UUID = 0x0008
HAS_SUBSYSTEM = 0x0200
HAS_TTL = 0x0400
HAS_DATA_REF = 0x0800
HAS_CONTEXT_DATA = 0x1000
HAS_SIGNPOST_NAME = 0x8000

# Activity Types
FIREHOSE_LOG_ACTIVITY_TYPE_ACTIVITY = 0x2
FIREHOSE_LOG_ACTIVITY_TYPE_TRACE = 0x3
FIREHOSE_LOG_ACTIVITY_TYPE_NONACTIVITY = 0x4
FIREHOSE_LOG_ACTIVITY_TYPE_SIGNPOST = 0x6
FIREHOSE_LOG_ACTIVITY_TYPE_LOSS = 0x7

# Item Types
FIREHOSE_ITEM_DYNAMIC_PRECISION_TYPE = 0x0
FIREHOSE_ITEM_NUMBER_TYPES = [0x0, 0x2]
FIREHOSE_ITEM_STRING_PRIVATE = 0x1
FIREHOSE_ITEM_PRIVATE_STRING_TYPES = [
    0x21, 0x25, 0x31, 0x35, 0x41]
FIREHOSE_ITEM_STRING_TYPES = [
    0x20, 0x22, 0x30, 0x32, 0x40, 0x42, 0xf2]
FIREHOSE_ITEM_STRING_ARBITRARY_DATA_TYPES = [
    0x30, 0x31, 0x32]
FIREHOSE_ITEM_STRING_BASE64_TYPE = 0xf2
FIREHOSE_ITEM_PRECISION_TYPES = [0x10, 0x12]
FIREHOSE_ITEM_SENSITIVE = 0x45

# Log Types
LOG_TYPES = {
    0x01: 'Info',
    0x02: 'Debug',
    0x03: 'Useraction',
    0x10: 'Error',
    0x11: 'Fault',
    0x40: 'Thread Signpost Event',
    0x41: 'Thread Signpost Start',
    0x42: 'Thread Signpost End',
    0x80: 'Process Signpost Event',
    0x81: 'Process Signpost Start',
    0x82: 'Process Signpost End',
    0xc0: 'System Signpost Event',
    0xc1: 'System Signpost Start',
    0xc2: 'System Signpost End'}

# MBR Details Types
USER_TYPES = [0x24, 0xA0, 0xA4]
UID_TYPES = [0x23, 0xA3]
GROUP_TYPES = [0x44]
GID_TYPES = [0xC3]


def GetBootUuidTimeSync(records, uuid):
  """Retrieves the timesync for a specific boot identifier.

  Args:
    records (List[timesync_boot_record]): List of Timesync records.
    uuid (uuid): boot identifier.

  Returns:
    timesync_boot_record or None if not available.
  """
  for ts in records:
    if ts.boot_uuid == uuid:
      ts.adjustment = 1
      # ARM processors.
      if (
          ts.timebase_numerator == ARM_TIMEBASE_NUMERATOR
          and ts.timebase_denominator == ARM_TIMEBASE_DENOMINATOR
      ):
        ts.adjustment = ARM_TIMEBASE_NUMERATOR / ARM_TIMEBASE_DENOMINATOR
      return ts
  logger.error("Could not find boot uuid {} in Timesync!".format(uuid))
  return None


def FindClosestTimesyncItemInList(
    sync_records, continuous_time, return_first=False):
  """Returns the closest timesync item from the provided list without going over

  Args:
    sync_records (List[timesync_sync_record]): List of timesync boot records.
    continuous_time (int): The timestamp we're looking for.
    return_first (Optional[bool]): Whether to return the first largest record.

  Returns:
    timesync_boot_record or None if not available.
  """
  if not sync_records:
    return None

  i = 1
  closest_tsi = None
  for item in sync_records:
    if item.kernel_continuous_timestamp > continuous_time:
      if return_first and i == 1:
        closest_tsi = item
      break
    i += 1
    closest_tsi = item

  return closest_tsi


class AULEventData(events.EventData):
  """Apple Unified Logging (AUL) event data.

  Attributes:
    activity_id (str): activity identifier.
    body (str): the log message.
    boot_uuid (str): unique boot identifier.
    category (str): event category.
    creation_time (dfdatetime.DateTimeValues): file entry creation date
        and time.
    euid (int): effective user identifier (UID)
    level (str): level of criticality of the event.
    library (str): originating library path.
    library_uuid (str): Unique library identifier.
    pid (int): process identifier (PID).
    process (str): originating process path.
    process_uuid (str): unique process identifier.
    subsystem (str): subsystem that produced the logging event.
    thread_identifier (int): thread identifier.
    ttl (int): log time to live (TTL).
  """
  DATA_TYPE = 'macos:unified_logging:event'

  def __init__(self):
    """Initialise event data."""
    super(AULEventData, self).__init__(data_type=self.DATA_TYPE)
    self.activity_id = None
    self.body = None
    self.boot_uuid = None
    self.category = None
    self.creation_time = None
    self.euid = None
    self.level = None
    self.library = None
    self.library_uuid = None
    self.pid = None
    self.process = None
    self.process_uuid = None
    self.subsystem = None
    self.thread_identifier = None
    self.ttl = None


class AULFormatterFlags(object):
  """Helper class for message formatter flags.

  Attributes:
  """

  # TODO: add missing attributes in docstring.

  def __init__(self):
    """Initialises a FormatterFlags object."""
    super(AULFormatterFlags, self).__init__()
    self.absolute = False
    self.data_ref_id = 0
    self.large_offset_data = 0
    self.large_shared_cache = 0
    self.offset = 0
    self.shared_cache = False
    self.uuid_file_index = -1
    self.uuid_relative = False


class AULOversizeData(object):
  """Apple Unified Logging (AUL) oversize data.

  Attributes:
    data_ref_index (str): index of the data reference.
    first_proc_id (str): First process identifier.
    second_proc_id (str): Second process identifier.
    strings (List[str]): oversized strings.
  """

  def __init__(self, first_proc_id, second_proc_id, data_ref_index):
    """Initialises oversized data.

    Args:
      first_proc_id (str): First process identifier.
      second_proc_id (str): Second process identifier.
      data_ref_index (str): index of the data reference.
    """
    super(AULOversizeData, self).__init__()
    self.data_ref_index = data_ref_index
    self.first_proc_id = first_proc_id
    self.second_proc_id = second_proc_id
    self.strings = []


class AULParser(interface.FileEntryParser, dtfabric_helper.DtFabricHelper):
  """Parser for Apple Unified Logging (AUL) tracev3 files."""

  NAME = 'aul_log'
  DATA_FORMAT = 'Apple Unified Logging (AUL) tracev3 file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'shared', 'unified_logging',
      'unified_logging.yaml')

  _CATALOG_LZ4_COMPRESSION = 0x100

  # Chunk Tags
  _CHUNK_TAG_HEADER = 0x1000
  _CHUNK_TAG_FIREHOSE = 0x6001
  _CHUNK_TAG_OVERSIZE = 0x6002
  _CHUNK_TAG_STATEDUMP = 0x6003
  _CHUNK_TAG_SIMPLEDUMP = 0x6004
  _CHUNK_TAG_CATALOG = 0x600b
  _CHUNK_TAG_CHUNKSET = 0x600d

  _NON_ACTIVITY_SENINTEL = 0x80000000

  _USER_ACTION_ACTIVITY_TYPE = 0x3

  # Flag constants
  _FORMAT_FLAGS_BITMASK = 0x0e

  # An uuidtext file contains the format string (main_exe).
  _FORMAT_FLAG_HAS_FMT_IN_UUID = 0x02

  # A DSC file contains the format string.
  _FORMAT_FLAG_HAS_SHARED_CACHE = 0x04

  # The log uses an alternative index number that points to the uuidtext
  # file name in the Catalog which contains the format string.
  _FORMAT_FLAG_HAS_ABSOLUTE = 0x08

  # The uuidtext file name is in the log data (instead of the Catalog).
  _FORMAT_FLAG_HAS_UUID_RELATIVE = 0x0a

  _FORMAT_FLAG_HAS_LARGE_SHARED_CACHE = 0x0c

  # Offset to format string is larger than normal.
  _FORMAT_FLAG_HAS_LARGE_OFFSET = 0x20

  format_strings_re = re.compile(
      r'%(\{[^\}]{1,64}\})?([0-9.'
      r' *\-+#\']{0,6})([hljztLq]{0,2})([@dDiuUxXoOfeEgGcCsSpaAFPm])'
  )

  # StateDump data types
  _STATEDUMP_DATA_TYPE_PLIST = 1
  _STATEDUMP_DATA_TYPE_PROTOBUF = 2
  _STATEDUMP_DATA_TYPE_CUSTOM = 3

  def __init__(self):
    """Initializes an Apple Unified Logging tracev3 file parser."""
    super(AULParser, self).__init__()
    self._boot_uuid_ts = None
    self._cached_catalog_files = {}
    self._cached_dsc_files = {}
    self._cached_uuidtext_files = {}
    self._catalog = None
    self._catalog_process_entries = {}
    self._dsc_parser = dsc.DSCFileParser()
    self._header = None
    self._oversize_data = []
    self._timesync_parser = None
    self._tracev3_file_entry = None
    self._uuidtext_file_entry = None
    self._uuidtext_parser = uuidtext.UUIDTextFileParser()

  def _ExtractAbsoluteStrings(
      self, original_offset, uuid_file_index, proc_info,
      message_string_reference):
    """Extracts absolute strings from an uuidtext file.

    Args:
      original_offset (int): Original offset into file
      uuid_file_index (int): Which UUID file to extract from
      proc_info (tracev3_catalog_process_information_entry): Process Info entry
      message_string_reference (int): Offset into file of message string

    Returns:
      A uuid_file or a string.

    Raises:
      ParseError: if the data cannot be parsed.
    """
    logger.debug('Extracting absolute strings from uuidtext file')
    if original_offset & 0x80000000:
      return '%s'

    absolute_uuids = [
        x for x in proc_info.uuids if x.absolute_ref == uuid_file_index and
        message_string_reference >= x.absolute_offset and
        message_string_reference - x.absolute_offset < x.size
    ]
    if len(absolute_uuids) != 1:
      return '<compose failure [missing precomposed log]>'
    uuid_file = self._catalog.files[absolute_uuids[0].catalog_uuid_index]
    return uuid_file

  def _ExtractAltUUID(self, uuid):
    """Extracts the requested alternate UUID file.

    Args:
      uuid (str): Requested UUID.

    Returns:
      UUIDText object or None.

    Raises:
      ParseError: if the requested UUID file was not found.
    """
    uuid_file = [
        f for f in self._cached_catalog_files.values()
        if f.uuid == uuid.hex.upper()]
    if len(uuid_file) != 1:
      logger.error('Couldn\'t find UUID file for {0:s}'.format(
          uuid.hex))
      return None
    return uuid_file[0]

  def _ExtractFormatStrings(self, offset, uuid_file):
    """Extracts a format string from a UUID file.

    Args:
      offset (int): The offset into the file to grab the string.
      uuid_file (UUIDText): The UUID file to search.

    Returns:
      str: The format string.
    """
    logger.debug('Extracting format string from UUID file')
    return uuid_file.ReadFormatString(offset)

  def _ExtractSharedStrings(self, original_offset, extra_offset, dsc_file):
    """Extracts a format string from a DSC file.

    Args:
      original_offset (int): The original offset into the file.
      extra_offset (int): The calculated offset into the file.
      dsc_file (DSCFile): The DSC file to search.

    Returns:
      Tuple[str, DSCRange]: The format string and the range it was from.
    """
    logger.debug('Extracting format string from shared cache file (DSC)')

    if original_offset & 0x80000000:
      return ('%s', dsc.DSCRange())

    format_string = 'Invalid shared cache code pointer offset'
    dsc_range = dsc_file.ReadFormatString(extra_offset)
    if dsc_range:
      format_string = self._ReadStructureFromByteStream(
          dsc_range.string[extra_offset - dsc_range.range_offset:], 0,
          self._GetDataTypeMap('cstring'))
    else:
      dsc_range = dsc.DSCRange()

    logger.debug('Fmt string: {0:s}'.format(format_string))
    return (format_string, dsc_range)

  def _GetCatalogSubSystemStringMap(self, catalog):
    """Retrieves a map of the catalog sub system strings and offsets.

    Args:
      catalog (tracev3_catalog): catalog.

    Returns:
      dict[int, str]: catalog sub system string per offset.
    """
    strings_map = {}

    map_offset = 0
    for string in catalog.sub_system_strings:
      strings_map[map_offset] = string
      map_offset += len(string) + 1

    return strings_map

  def _GetDSCFile(self, parser_mediator, uuid):
    """Retrieves a specific shared-cache strings (DSC) file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      uuid (str): the UUID.

    Returns:
      DSCFile: a shared-cache strings (DSC) file or None if not available.
    """
    dsc_file = self._cached_dsc_files.get(uuid, None)
    if not dsc_file:
      dsc_file = self._ReadDSCFile(parser_mediator, uuid)
      self._cached_dsc_files[uuid] = dsc_file

    return dsc_file

  def _GetUUIDTextFile(self, parser_mediator, uuid):
    """Retrieves a specific uuidtext file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      uuid (str): the UUID.

    Returns:
      UUIDTextFile: an uuidtext file or None if not available.
    """
    uuidtext_file = self._cached_uuidtext_files.get(uuid, None)
    if not uuidtext_file:
      uuidtext_file = self._ReadUUIDTextFile(parser_mediator, uuid)
      self._cached_uuidtext_files[uuid] = uuidtext_file

    return uuidtext_file

  def _FormatFlags(self, flags, data, offset):
    """Parses the format flags.

    Args:
      flags (int): Flags bitfield.
      data (bytes): The raw message data.
      offset (int): The starting offset into the data.

    Returns:
      AULFormatterFlags: formatter flags.

    Raises:
      ParseError: if the format flags cannot be parsed.
    """
    ret = AULFormatterFlags()
    uint16_data_type_map = self._GetDataTypeMap('uint16le')

    formatter_type = flags & self._FORMAT_FLAGS_BITMASK

    if formatter_type == self._FORMAT_FLAG_HAS_FMT_IN_UUID:
      pass

    elif formatter_type == self._FORMAT_FLAG_HAS_SHARED_CACHE:
      ret.shared_cache = True
      if flags & self._FORMAT_FLAG_HAS_LARGE_OFFSET:
        ret.large_offset_data = self._ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
        offset += 2

    elif formatter_type == self._FORMAT_FLAG_HAS_ABSOLUTE:
      ret.absolute = True
      ret.uuid_file_index = self._ReadStructureFromByteStream(
        data[offset:], offset, uint16_data_type_map)
      offset += 2

    elif formatter_type == self._FORMAT_FLAG_HAS_UUID_RELATIVE:
      data_type_map = self._GetDataTypeMap('uuid_be')
      ret.uuid_relative = self._ReadStructureFromByteStream(
          data[offset:], offset, data_type_map)
      offset += 16

    elif formatter_type == self._FORMAT_FLAG_HAS_LARGE_SHARED_CACHE:
      if flags & self._FORMAT_FLAG_HAS_LARGE_OFFSET:
        ret.large_offset_data = self._ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
        offset += 2

      ret.large_shared_cache = self._ReadStructureFromByteStream(
        data[offset:], offset, uint16_data_type_map)
      offset += 2

    else:
      raise errors.ParseError(
          'Unsupported formatter type: 0x{0:04x}'.format(formatter_type))

    ret.offset = offset
    return ret

  def _FormatString(self, format_string, data):
    """Substitutes data items into the format string.

    Args:
      format_string (str): The supplied format string.
      data (list[tuple[int, int, bytes]]): List of data items

    Returns:
      str: format string.

    Raises:
      ParseError: if the format string or data could not be parsed.
    """
    if len(format_string) == 0:
      if len(data) == 0:
        return ''
      return data[0][2]

    uuid_data_type_map = self._GetDataTypeMap('uuid_be')
    int8_data_type_map = self._GetDataTypeMap('char')
    uint8_data_type_map = self._GetDataTypeMap('uint8')
    int16_data_type_map = self._GetDataTypeMap('int16')
    uint16_data_type_map = self._GetDataTypeMap('uint16')
    int32_data_type_map = self._GetDataTypeMap('int32')
    uint32_data_type_map = self._GetDataTypeMap('uint32')
    float32_data_type_map = self._GetDataTypeMap('float32')
    int64_data_type_map = self._GetDataTypeMap('int64')
    uint64_data_type_map = self._GetDataTypeMap('uint64')
    float64_data_type_map = self._GetDataTypeMap('float64')

    # Set up for floating point
    ctx = decimal.Context()
    ctx.prec = 20

    output = ''
    i = 0
    last_start_index = 0
    for match in self.format_strings_re.finditer(
        format_string.replace('%%', '~~')):
      data_map = None

      output += format_string[last_start_index:match.start()].replace('%%', '%')
      last_start_index = match.end()
      if match.group().startswith('% '):
        continue

      if i >= len(data):
        output += '<decode: missing data>'
        continue

      data_item = data[i]
      if (
          data_item[0] == FIREHOSE_ITEM_DYNAMIC_PRECISION_TYPE
          and '%*' in match.group()
      ):
        i += 1
        data_item = data[i]

      custom_specifier = match.group(1) or ''
      # == Custom specifier types not yet seen (unimplemented) ==
      #  darwin.signal   %{darwin.signal}d        [sigsegv: Segmentation Fault]
      #  timeval         %{timeval}.*P            2016-01-12 19:41:37.774236
      #  timespec        %{timespec}.*P           2016-01-12 19:41:37.238238282
      #  bytes           %{bytes}d                4.72 kB
      #  iec-bytes       %{iec-bytes}d            4.61 KiB
      #  bitrate         %{bitrate}d              123 kbps
      #  iec-bitrate     %{iec-bitrate}d          118 Kib6s

      flags_width_precision = match.group(2).replace('\'', '')
      specifier = match.group(4)
      data_type = data_item[0]
      data_size = data_item[1]
      raw_data = data_item[2]

      # Weird hack for "%{public}" which isn't a legal format string
      if flags_width_precision == ' ':
        last_start_index -= 2

      if 'mask.hash' in custom_specifier and data_type == 0xF2:
        if isinstance(raw_data, bytes):
          raw_data = raw_data.decode('utf-8').rstrip('\x00')
        output += raw_data
        i += 1
        continue

      if (
          (
              data_type
              in FIREHOSE_ITEM_PRIVATE_STRING_TYPES
              + FIREHOSE_ITEM_STRING_ARBITRARY_DATA_TYPES
              + [FIREHOSE_ITEM_STRING_PRIVATE]
          )
          and len(raw_data) == 0
          and (
              data_size == 0
              or (
                  data_type == FIREHOSE_ITEM_STRING_PRIVATE
                  and data_size == 0x8000
              )
          )
      ) or (
          data_type == FIREHOSE_ITEM_SENSITIVE
          and custom_specifier == '{sensitive}'
      ):
        output += '<private>'
        i += 1
        continue

      if (specifier
          not in ('p', 'P', 's', 'S')) and '*' in flags_width_precision:
        logger.error('* not supported for p/P/s/S')
        output += 'Unsupported specifier'
        i += 1
        continue

      if (
          data_type in FIREHOSE_ITEM_STRING_ARBITRARY_DATA_TYPES
          and specifier != 'P'
      ):
        logger.error('Non-P specifier not supported for arbitrary data types')
        output += 'Unsupported specifier'
        i += 1
        continue

      if specifier in ('d', 'D', 'i', 'u', 'U', 'x', 'X', 'o', 'O', 'm'):
        number = 0
        if (
            data_size == 0
            and data_type != FIREHOSE_ITEM_STRING_PRIVATE
        ):
          output += 'Invalid specifier'
          logger.error(
              'Size 0 in int fmt {0:s} // data {1!s}'.format(
                  format_string, data_item))
          i += 1
          continue

        if (
            data_type == FIREHOSE_ITEM_STRING_PRIVATE and not raw_data
        ):
          output += '0'  # A private number
        else:
          if specifier in ('d', 'D', 'i'):
            specifier = 'd'
            if data_size == 1:
              data_map = int8_data_type_map
            elif data_size == 2:
              data_map = int16_data_type_map
            elif data_size == 4:
              data_map = int32_data_type_map
            elif data_size == 8:
              data_map = int64_data_type_map
            else:
              output += 'Invalid specifier'
              logger.error(
                  'Unknown data_size for signed int: {0:d} // fmt {1:s}'.format(
                      data_size, format_string))
              i += 1
              continue
          else:
            if data_size == 1:
              data_map = uint8_data_type_map
            elif data_size == 2:
              data_map = uint16_data_type_map
            elif data_size == 4:
              data_map = uint32_data_type_map
            elif data_size == 8:
              data_map = uint64_data_type_map
            else:
              output += 'Invalid specifier'
              logger.error(
                  'Unknown data_size for unsigned int: {0:d} // fmt {1:s}'
                  .format(data_size, format_string))
              i += 1
              continue
            if specifier in ('u', 'U'):
              specifier = 'd'
            elif specifier == 'O':
              specifier = 'o'
          width_and_precision = flags_width_precision.split('.')
          if len(width_and_precision) == 2:
            flags_width_precision = '0' + width_and_precision[0]
          if flags_width_precision.startswith('-'):
            flags_width_precision = '<' + flags_width_precision[1:]
          if flags_width_precision == '.':
            flags_width_precision = '.0'

          # Strip width for hex
          if specifier in ['x', 'X'] and '#' in flags_width_precision:
            flags_width_precision = '#'
          format_code = '{:' + flags_width_precision + specifier + '}'
          number = self._ReadStructureFromByteStream(raw_data, 0, data_map)

          if 'BOOL' in custom_specifier:
            if bool(number):
              output += 'YES'
            else:
              output += 'NO'
          elif 'bool' in custom_specifier:
            output += str(bool(number)).lower()
          elif 'time_t' in custom_specifier:
            # Timestamp in seconds ?
            output += dfdatetime_posix_time.PosixTime(
                timestamp=number).CopyToDateTimeString()
          elif 'darwin.errno' in custom_specifier or specifier == 'm':
            output += '[{0:d}: {1:s}]'.format(
              number, darwin.DarwinErrorHelper.GetError(number))
          elif '{darwin.mode}' in custom_specifier:
            output += '{0:s} ({1:s})'.format(
              oct(number).replace('o', ''), stat.filemode(number))
          elif 'odtypes:ODError' in custom_specifier:
            output += opendirectory.OpenDirectoryErrorsHelper.GetError(number)
          elif 'odtypes:mbridtype' in custom_specifier:
            output += opendirectory.OpenDirectoryMBRIdHelper.GetType(number)
          elif 'location:CLClientAuthorizationStatus' in custom_specifier:
            output += location.ClientAuthStatusHelper.GetCode(number)
          elif 'location:IOMessage' in custom_specifier:
            output += location.LocationTrackerIOHelper.GetMessage(number)
          elif 'location:CLDaemonStatus_Type::Reachability' in custom_specifier:
            output += location.DaemonStatusHelper.GetCode(number)
          elif 'location:CLSubHarvesterIdentifier' in custom_specifier:
            output += location.SubharvesterIDHelper.GetCode(number)
          elif 'mdns:addrmv' in custom_specifier:
            if number == 1:
              output += 'add'
            else:
              output += 'rmv'
          elif 'mdns:rrtype' in custom_specifier:
            output += dns.DNS.GetRecordType(number)
          elif 'mdns:yesno' in custom_specifier:
            if number == 0:
              output += 'no'
            else:
              output += 'yes'
          elif 'mdns:protocol' in custom_specifier:
            output += dns.DNS.GetProtocolType(number)
          elif 'mdns:dns.idflags' in custom_specifier:
            flags = self._ReadStructureFromByteStream(
                raw_data, 0, uint16_data_type_map
            )
            dns_id = self._ReadStructureFromByteStream(
                raw_data[2:], 2, uint16_data_type_map
            )
            flag_string = dns.DNS.ParseFlags(flags)
            output += 'id: {0:s} ({1:d}), flags: 0x{2:04x} ({3:s})'.format(
              hex(dns_id).upper(), dns_id, flags, flag_string)
          elif 'mdns:dns.counts' in custom_specifier:
            questions = self._ReadStructureFromByteStream(
              raw_data[6:], 6, uint16_data_type_map)
            answers = self._ReadStructureFromByteStream(
              raw_data[4:], 4, uint16_data_type_map)
            authority_records = self._ReadStructureFromByteStream(
              raw_data[2:], 2, uint16_data_type_map)
            additional_records = self._ReadStructureFromByteStream(
              raw_data, 0, uint16_data_type_map)
            output += 'counts: {0:d}/{1:d}/{2:d}/{3:d}'.format(
              questions, answers,
              authority_records, additional_records)
          elif 'mdns:acceptable' in custom_specifier:
            if number == 0:
              output += 'unacceptable'
            else:
              output += 'acceptable'
          elif '{mdns:nreason}' in custom_specifier:
            output += dns.DNS.GetReasons(number)
          elif '{mdns:gaiopts}' in custom_specifier:
            if number == 0x8:
              output += '0x8 {use-failover}'
            elif number == 0xC:
              output += '0xC {in-app-browser, use-failover}'
            else:
              logger.warning(
                'Unknown DNS option: {0:d}'.format(number))
              output += hex(number)
          elif '{network:tcp_flags}' in custom_specifier:
            output += tcp.TCP.ParseFlags(number)
          elif '{network:tcp_state}' in custom_specifier:
            output += tcp.TCP.ParseState(number)
          else:
            try:
              output += format_code.format(number)
            except ValueError:
              pass
      elif specifier in ('f', 'e', 'E', 'g', 'G', 'a', 'A', 'F'):
        number = 0
        if (
            data_size == 0
            and data_type != FIREHOSE_ITEM_STRING_PRIVATE
        ):
          logger.error(
              'Size 0 in float fmt {0:s} // data {1!s}'.format(
                  format_string, data_item))
          output += 'Invalid specifier'
          i += 1
          continue
        if (
            data_type == FIREHOSE_ITEM_STRING_PRIVATE and not raw_data
        ):
          output += '0'  # A private number
        else:
          if data_size == 4:
            data_map = float32_data_type_map
          elif data_size == 8:
            data_map = float64_data_type_map
          else:
            logger.error(
                'Unknown data_size for float int: {0:d} // fmt {1:s}'.format(
                    data_size, format_string))
            output += 'Invalid specifier'
            i += 1
            continue
          try:
            number = self._ReadStructureFromByteStream(raw_data, 0, data_map)
          except ValueError:
            pass
          if flags_width_precision:
            if flags_width_precision == '.':
              flags_width_precision = '.0'
            format_code = '{:' + flags_width_precision + specifier + '}'
            output += format_code.format(number)
          else:
            output += format(ctx.create_decimal(repr(number)), 'f')
      elif specifier in ('c', 'C', 's', 'S', '@'):
        specifier = 's'
        chars = ''
        if data_size == 0:
          if data_type in FIREHOSE_ITEM_STRING_TYPES:
            chars = '(null)'
          elif data_type & FIREHOSE_ITEM_STRING_PRIVATE:
            chars = '<private>'
        else:
          chars = raw_data
          if isinstance(chars, bytes):
            chars = chars.decode('utf-8').rstrip('\x00')
          if '*' in flags_width_precision:
            flags_width_precision = ''
          if flags_width_precision == '.':
            flags_width_precision = ''
          if flags_width_precision.isdigit():
            flags_width_precision = '>' + flags_width_precision
          if flags_width_precision.startswith('-'):
            flags_width_precision = '<' + flags_width_precision[1:]
          format_code = '{:' + flags_width_precision + specifier + '}'
          chars = format_code.format(chars)
        output += chars
      elif specifier == 'P':
        if not custom_specifier:
          logger.error('Pointer with no custom specifier')
          output += 'Invalid specifier'
          i += 1
          continue
        if data_size == 0:
          continue
        if 'uuid_t' in custom_specifier:
          if (
              data_type in FIREHOSE_ITEM_PRIVATE_STRING_TYPES
              and not raw_data
          ):
            chars = '<private>'
          else:
            uuid = self._ReadStructureFromByteStream(raw_data, 0,
                                                     uuid_data_type_map)
            chars = str(uuid).upper()
        elif 'odtypes:mbr_details' in custom_specifier:
          if raw_data[0] in USER_TYPES + GROUP_TYPES:
            user_group_type = self._ReadStructureFromByteStream(
                raw_data[1:], 1, self._GetDataTypeMap('mbr_user_group_type'))
            mbr_type = 'group'
            if raw_data[0] in USER_TYPES:
              mbr_type = 'user'
            chars = '{0:s}: {1:s}@{2:s}'.format(
                mbr_type,
                user_group_type.name,
                (user_group_type.domain or '<not found>'),
            )
          elif raw_data[0] in UID_TYPES + GID_TYPES:
            uid_gid_type = self._ReadStructureFromByteStream(
                raw_data[1:], 1, self._GetDataTypeMap('mbr_uid_gid_type'))
            mbr_type = 'group'
            if raw_data[0] in UID_TYPES:
              mbr_type = 'user'
            chars = '{0:s}: {1:d}@{2:s}'.format(
                mbr_type,
                uid_gid_type.uid,
                (uid_gid_type.domain or '<not found>'),
            )
          else:
            logger.error(
                'Unknown MBR Details Header Byte: 0x{0:X}'.format(raw_data[0]))
            output += 'Invalid specifier'
            i += 1
            continue
        elif 'odtypes:nt_sid_t' in custom_specifier:
          sid = self._ReadStructureFromByteStream(
              raw_data, 1, self._GetDataTypeMap('nt_sid'))
          chars = 'S-{0:d}-{1:d}-{2:s}'.format(
              sid.rev, sid.authority,
              '-'.join([str(sa) for sa in sid.sub_authorities]))
        elif 'network:sockaddr' in custom_specifier:
          sockaddr = self._ReadStructureFromByteStream(
              raw_data, 1, self._GetDataTypeMap('sockaddr'))
          # IPv6
          if sockaddr.family == 0x1E:
            if raw_data[8:24] == b'\x00' * 16:
              chars = 'IN6ADDR_ANY'
            else:
              try:
                chars = ipaddress.ip_address(sockaddr.ipv6_ip.ip).compressed
              except ValueError:
                pass
          # IPv4
          elif sockaddr.family == 0x02:
            chars = self._FormatPackedIPv4Address(
                sockaddr.ipv4_address.segments)
            if sockaddr.ipv4_port:
              chars += ':{0:d}'.format(sockaddr.ipv4_port)
          else:
            logger.error('Unknown Sockaddr Family: {}'.format(sockaddr.family))
            output += 'Invalid specifier'
            i += 1
            continue
        elif 'network:in_addr' in custom_specifier:
          ip_addr = self._ReadStructureFromByteStream(
              raw_data, 0, self._GetDataTypeMap('ipv4_address'))
          chars = self._FormatPackedIPv4Address(ip_addr.segments)
        elif 'network:in6_addr' in custom_specifier:
          chars = ipaddress.ip_address(raw_data).compressed
        elif 'location:SqliteResult' in custom_specifier:
          code = sqlite.SQLiteResultCodeHelper.GetResult(
              self._ReadStructureFromByteStream(raw_data, 0,
                                                uint32_data_type_map))
          if code:
            chars += '"{0:s}"'.format(code)
          else:
            logger.error('Unknown SQLite Code: {0:X}'.format(raw_data[0]))
            output += 'Invalid specifier'
            i += 1
            continue
        elif 'location:_CLLocationManagerStateTrackerState' in custom_specifier:
          (
              state_tracker_structure,
              extra_state_tracker_structure,
          ) = location.LocationManagerStateTrackerParser().Parse(
              data_size, raw_data
          )
          chars = str({
              **state_tracker_structure,
              **extra_state_tracker_structure
          })
        elif 'location:_CLClientManagerStateTrackerState' in custom_specifier:
          chars = str(
              location.LocationClientStateTrackerParser().Parse(raw_data)
          )
        elif 'mdns:dnshdr' in custom_specifier:
          dns_parser = dns.DNS()
          chars = dns_parser.ParseDNSHeader(raw_data)
        elif 'mdns:rd.svcb' in custom_specifier:
          dns_parser = dns.DNS()
          chars = dns_parser.ParseDNSSVCB(raw_data)
        elif 'mdnsresponder:domain_name' in custom_specifier:
          chars = ''.join([
              '.' if not chr(s).isprintable() else chr(s)
              for s in raw_data.replace(b'\n', b'').replace(b'\t', b'').replace(
                  b'\r', b'')
          ])
        elif 'mdnsresponder:ip_addr' in custom_specifier:
          ip_type = self._ReadStructureFromByteStream(raw_data[0:], 0,
            uint32_data_type_map)
          if ip_type == 4:
            ip_addr = self._ReadStructureFromByteStream(
              raw_data[4:], 4, self._GetDataTypeMap('ipv4_address'))
            chars = self._FormatPackedIPv4Address(ip_addr.segments)
          elif ip_type == 6:
            chars = ipaddress.ip_address(raw_data[4:]).compressed
          else:
            logger.error(
              'Unknown IP Type: {}'.format(ip_type))
            output += 'Invalid specifier'
            i += 1
            continue
        elif 'mdnsresponder:mac_addr' in custom_specifier:
          chars = ':'.join('%02x' % b for b in raw_data)
        # Nothing else to go on, so print it in hex
        elif custom_specifier in ('{public}', '{private}'):
          chars = raw_data
          if flags_width_precision.startswith('.'):
            chars = raw_data[:int(flags_width_precision[1:])]
          chars = binascii.hexlify(chars, ' ').decode('utf-8').upper()
        else:
          logger.error(
            'Unknown data specifier: {}'.format(custom_specifier))
          output += 'Invalid specifier'
          i += 1
          continue
        output += chars
      elif specifier == 'p':
        if data_size == 0:
          if data_type & FIREHOSE_ITEM_STRING_PRIVATE:
            output += '<private>'
          else:
            logger.error(
                'Size 0 in pointer fmt {0:s} // data {1!s}'.format(
                    format_string, data_item))
            output += 'Invalid specifier'
            i += 1
            continue
        else:
          if data_size == 2:
            data_map = uint16_data_type_map
          elif data_size == 4:
            data_map = uint32_data_type_map
          elif data_size == 8:
            data_map = uint64_data_type_map
          else:
            logger.error(
                'Unknown data_size for pointer: {0:d} // fmt {1:s}'.format(
                    data_size, format_string))
            output += 'Invalid specifier'
            i += 1
            continue
          try:
            number = self._ReadStructureFromByteStream(raw_data, 0, data_map)
          except ValueError:
            pass
          if flags_width_precision:
            logger.error('Width/Precision not supported for *p specifiers')
      else:
        output += 'Unknown Specifier'

      i += 1

    if last_start_index < len(format_string):
      output += format_string[last_start_index:].replace('%%', '%')

    return output

  def _ReadCatalog(self, parser_mediator, file_object, file_offset):
    """Reads a catalog.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the catalog data relative to the start of the
          file.

    Returns:
      tracev3_catalog: catalog.

    Raises:
      ParseError: if the catalog chunk cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_catalog')

    catalog, offset_bytes = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    logger.debug(
        'Catalog data: NumProcs {0:d} // NumSubChunks {1:d} //'
        ' EarliestFirehoseTS {2:d}'.format(
            catalog.number_of_process_information_entries,
            catalog.number_of_sub_chunks,
            catalog.earliest_firehose_timestamp,
        )
    )
    logger.debug('Num UUIDS: {0:d} // Num SubSystemStrings {1:d}'.format(
        len(catalog.uuids), len(catalog.sub_system_strings)))

    catalog.files = []

    for uuid in catalog.uuids:
      found = None
      found_in_cache = False
      filename = uuid.hex.upper()
      logger.debug('Encountered UUID {0:s} in Catalog.'.format(filename))
      if filename == '00000000000000000000000000000000':
        catalog.files.append(None)
        continue

      found = self._cached_catalog_files.get(filename, None)
      if found:
        found_in_cache = True
        logger.debug('Found in cache')

      if not found:
        found = self._GetDSCFile(parser_mediator, filename)

      if not found:
        found = self._GetUUIDTextFile(parser_mediator, filename)
        if not found:
          logger.error(
              'Neither UUID nor DSC file found for UUID: {0:s}'.format(
                  uuid.hex))
          catalog.files.append(None)
          continue

        if not found_in_cache:
          self._cached_catalog_files[found.uuid] = found
        catalog.files.append(found)

      else:
        if not found_in_cache:
          self._cached_catalog_files[found.uuid] = found
        catalog.files.append(found)

    data_type_map = self._GetDataTypeMap(
        'tracev3_catalog_process_information_entry')

    catalog_strings_map = self._GetCatalogSubSystemStringMap(catalog)

    self._catalog_process_entries = {}

    for _ in range(catalog.number_of_process_information_entries):
      process_entry, new_bytes = self._ReadStructureFromFileObject(
          file_object, file_offset + offset_bytes, data_type_map)

      offset_bytes += new_bytes

      try:
        process_entry.main_uuid = catalog.uuids[process_entry.main_uuid_index]
      except IndexError:
        pass

      try:
        process_entry.dsc_uuid = catalog.uuids[process_entry.catalog_dsc_index]
      except IndexError:
        pass

      logger.debug('Process Entry data: PID {0:d} // EUID {1:d}'.format(
          process_entry.pid, process_entry.euid))

      process_entry.items = {}
      for subsystem in process_entry.subsystems:
        subsystem_string = catalog_strings_map.get(
            subsystem.subsystem_offset, None)
        category_string = catalog_strings_map.get(
            subsystem.category_offset, None)

        process_entry.items[subsystem.identifier] = (
            subsystem_string, category_string)

        logger.debug(
            'Process Entry coalesce: Subsystem {0:s} // Category {1:s}'.format(
                subsystem_string, category_string))

      proc_id = '{0:d}@{1:d}'.format(
          process_entry.first_number_proc_id,
          process_entry.second_number_proc_id)
      if proc_id in self._catalog_process_entries:
        raise errors.ParseError('proc_id: {0:s} already set'.format(proc_id))

      self._catalog_process_entries[proc_id] = process_entry

    data_type_map = self._GetDataTypeMap('tracev3_catalog_subchunk')
    catalog.subchunks = []

    for _ in range(catalog.number_of_sub_chunks):
      subchunk, new_bytes = self._ReadStructureFromFileObject(
          file_object, file_offset + offset_bytes, data_type_map)
      logger.debug('Catalog Subchunk data: Size {0:d}'.format(
          subchunk.uncompressed_size))
      catalog.subchunks.append(subchunk)
      offset_bytes += new_bytes

    return catalog

  def _ReadChunkHeader(self, file_object, file_offset):
    """Reads a chunk header.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the chunk header relative to the start of the
        file.

    Returns:
      tracev3_chunk_header: a chunk header.

    Raises:
      ParseError: if the chunk header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_chunk_header')

    chunk_header, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    return chunk_header

  def _ReadChunkSet(
      self, parser_mediator, file_object, file_offset, chunk_header,
      chunkset_index):
    """Reads a chunk set.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the chunk set data relative to the start of
        the file.
      chunk_header (tracev3_chunk_header): the chunk header of the chunk set.
      chunkset_index (int): number of the chunk within the catalog.

    Raises:
      ParseError: if the chunk set cannot be read.
    """
    compression_algorithm = (
        self._catalog.subchunks[chunkset_index].compression_algorithm)
    if compression_algorithm != self._CATALOG_LZ4_COMPRESSION:
      raise errors.ParseError(
          'Unsupported compression algorithm: {0:s} for chunk: {1:d}'.format(
              compression_algorithm, chunkset_index))

    chunk_data = file_object.read(chunk_header.chunk_data_size)

    data_type_map = self._GetDataTypeMap('tracev3_lz4_block_header')

    lz4_block_header, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    end_of_compressed_data_offset = 12 + lz4_block_header.compressed_data_size

    if lz4_block_header.signature == b'bv41':
      uncompressed_data = lz4.block.decompress(
          chunk_data[12:end_of_compressed_data_offset],
          uncompressed_size=lz4_block_header.uncompressed_data_size)

    elif lz4_block_header.signature == b'bv4-':
      uncompressed_data = chunk_data[12:end_of_compressed_data_offset]

    else:
      raise errors.ParseError('Unsupported start of compressed data marker')

    end_of_compressed_data_identifier = chunk_data[
        end_of_compressed_data_offset:end_of_compressed_data_offset + 4]

    if end_of_compressed_data_identifier != b'bv4$':
      raise errors.ParseError('Unsupported end of compressed data marker')

    data_type_map = self._GetDataTypeMap('tracev3_chunk_header')

    data_offset = 0
    while data_offset < lz4_block_header.uncompressed_data_size:
      chunkset_chunk_header = self._ReadStructureFromByteStream(
          uncompressed_data[data_offset:], data_offset, data_type_map)

      data_offset += 16
      data_end_offset = data_offset + chunkset_chunk_header.chunk_data_size
      chunkset_chunk_data = uncompressed_data[data_offset:data_end_offset]

      if chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_FIREHOSE:
        self._ReadFirehoseChunkData(
            parser_mediator, chunkset_chunk_data, data_offset)

      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_OVERSIZE:
        oversized_data = self._ParseOversizeChunkData(
            chunkset_chunk_data, data_offset)
        self._oversize_data.append(oversized_data)

      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_STATEDUMP:
        self._ReadStateDumpChunkData(
            parser_mediator, chunkset_chunk_data, data_offset)

      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_SIMPLEDUMP:
        self._ReadSimpleDumpChunkData(
            parser_mediator, chunkset_chunk_data, data_offset)

      else:
        raise errors.ParseError('Unsupported chunk tag: 0x{0:04x}'.format(
            chunkset_chunk_header.chunk_tag))

      data_offset = data_end_offset

      # Not actually an alignment but \x00 padding
      count = 0
      new_data_offset = data_offset
      try:
        while uncompressed_data[new_data_offset] == 0:
          new_data_offset += 1
          count += 1
      except IndexError:
        pass

      data_offset = new_data_offset

  def _ReadDSCFile(self, parser_mediator, uuid):
    """Reads a specific shared-cache strings (DSC) file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      uuid (str): the UUID.

    Returns:
      DSCFile: a shared-cache strings (DSC) file or None if not available.
    """
    file_entry = self._uuidtext_file_entry.GetSubFileEntryByName('dsc')
    if file_entry:
      file_entry = file_entry.GetSubFileEntryByName(uuid)

    dsc_file = None
    if file_entry:
      try:
        file_object = file_entry.GetFileObject()
        dsc_file = self._dsc_parser.ParseFileObject(file_object)
        dsc_file.uuid = uuid
      except (IOError, errors.ParseError) as exception:
        message = (
            'Unable to parse DSC file: {0:s} with error: '
            '{1!s}').format(uuid, exception)
        logger.warning(message)
        parser_mediator.ProduceExtractionWarning(message)

    return dsc_file

  def _ReadFirehoseChunkData(self, parser_mediator, chunk_data, data_offset):
    """Reads firehose chunk data.

    Args:
      chunk_data (bytes): firehose chunk data.
      data_offset (int): offset of the firehose chunk relative to the start of
          the chunk set.

    Raises:
      ParseError: if the firehose chunk cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_firehose_header')

    firehose_header = self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map)

    proc_id = '{0:d}@{1:d}'.format(
        firehose_header.first_number_proc_id,
        firehose_header.second_number_proc_id)

    proc_info = self._catalog_process_entries.get(proc_id, None)
    if not proc_info:
      logger.error('Could not find Process Info block for ID: %d', proc_id)
      return

    private_strings = None
    private_data_len = 0
    if firehose_header.private_data_virtual_offset != 4096:
      logger.debug('Parsing Private Firehose Data')
      private_data_len = 4096 - firehose_header.private_data_virtual_offset
      private_strings = (firehose_header.private_data_virtual_offset,
                         chunk_data[-private_data_len:])

    date_time_string = self._TimestampFromContTime(
        self._boot_uuid_ts.sync_records, firehose_header.base_continuous_time)
    logger.debug('Firehose Header Timestamp: {0:s}'.format(date_time_string))

    tracepoint_map = self._GetDataTypeMap('tracev3_firehose_tracepoint')
    chunk_data_offset = 32
    #while chunk_data_offset < chunk_data_size-private_data_len:
    while chunk_data_offset <= firehose_header.public_data_size - 16:
      firehose_tracepoint = self._ReadStructureFromByteStream(
          chunk_data[chunk_data_offset:], data_offset + chunk_data_offset,
          tracepoint_map)
      logger.debug(
          'Firehose Tracepoint data: ActivityType {0:d} // Flags {1:d} //'
          ' ThreadID {2:d} // Datasize {3:d}'.format(
              firehose_tracepoint.log_activity_type,
              firehose_tracepoint.flags,
              firehose_tracepoint.thread_identifier,
              firehose_tracepoint.data_size,
          )
      )

      ct = firehose_header.base_continuous_time + (
          firehose_tracepoint.continuous_time_lower |
          (firehose_tracepoint.continuous_time_upper << 32))
      wt = 0
      kct = 0
      if firehose_header.base_continuous_time == 0:
        wt = self._boot_uuid_ts.boot_time
      ts = FindClosestTimesyncItemInList(
          self._boot_uuid_ts.sync_records, ct, wt == 0)
      if ts:
        wt = ts.wall_time
        kct = ts.kernel_continuous_timestamp
      time = (
          wt
          + (ct * self._boot_uuid_ts.adjustment)
          - (kct * self._boot_uuid_ts.adjustment)
      )
      self._ParseTracepointData(
          parser_mediator, firehose_tracepoint, proc_info, time,
          private_strings)

      chunk_data_offset += 24 + firehose_tracepoint.data_size
      _, alignment = divmod(chunk_data_offset, 8)
      if alignment > 0:
        alignment = 8 - alignment

      chunk_data_offset += alignment

  def _ReadHeaderChunk(self, file_object, file_offset):
    """Reads a tracev3 header chunk.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the catalog data relative to the start of the
        file.

    Raises:
      ParseError: if the header chunk cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_header_chunk')

    self._header, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    systeminfo_subchunk = self._header.systeminfo_subchunk
    generation_subchunk = self._header.generation_subchunk

    logger.debug('Header data: CT {0:d} // Bias {1:d}'.format(
        self._header.continuous_time, self._header.bias_in_minutes))
    logger.debug('SI Info: BVS: {0:s} // HMS: {1:s}'.format(
        systeminfo_subchunk.systeminfo_subchunk_data.build_version_string,
        systeminfo_subchunk.systeminfo_subchunk_data.hardware_model_string))

    logger.debug('Boot UUID: {0:s}'.format(
        generation_subchunk.generation_subchunk_data.boot_uuid.hex))
    logger.debug('TZ Info: {0:s}'.format(
        self._header.timezone_subchunk.timezone_subchunk_data.path_to_tzfile))

    self._boot_uuid_ts = GetBootUuidTimeSync(
        self._timesync_parser.records,
        generation_subchunk.generation_subchunk_data.boot_uuid)

    date_time_string = self._TimestampFromContTime(
        self._boot_uuid_ts.sync_records,
        self._header.continuous_time_subchunk.continuous_time_data)
    logger.debug('Tracev3 Header Timestamp: {0:s}'.format(date_time_string))

  def _ReadItems(self, data_meta, data, offset):
    """Use the metadata and raw data to retrieve the data items."""
    log_data = []
    deferred_data_items = []
    index = 0
    for _ in range(data_meta.num_items):
      data_item = self._ReadStructureFromByteStream(
          data[offset:], offset,
          self._GetDataTypeMap('tracev3_firehose_tracepoint_data_item'))
      offset += 2 + data_item.item_size
      logger.debug(
          'Item data: Type {0:d} // Size {1:d}'.format(
              data_item.item_type, data_item.item_size
          )
      )
      if data_item.item_type in FIREHOSE_ITEM_NUMBER_TYPES:
        log_data.append(
            (data_item.item_type, data_item.item_size, data_item.item))
        index += 1

      elif (
          data_item.item_type
          in FIREHOSE_ITEM_PRIVATE_STRING_TYPES
          + FIREHOSE_ITEM_STRING_TYPES
          + [FIREHOSE_ITEM_STRING_PRIVATE]
      ):
        offset -= data_item.item_size
        string_message = self._ReadStructureFromByteStream(
            data[offset:], offset,
            self._GetDataTypeMap(
                'tracev3_firehose_tracepoint_data_item_string_type'))
        offset += data_item.item_size
        deferred_data_items.append((data_item.item_type, string_message.offset,
                                    string_message.message_data_size, index))
        index += 1

      elif data_item.item_type in FIREHOSE_ITEM_PRECISION_TYPES:
        pass

      elif data_item.item_type == FIREHOSE_ITEM_SENSITIVE:
        log_data.append(
            (data_item.item_type, data_item.item_size, data_item.item))
        index += 1

      else:
        raise errors.ParseError(
            'Unsupported item type: {0:s}'.format(data_item.item_type))

    return log_data, deferred_data_items, offset

  def _ReadSimpleDumpChunkData(self, parser_mediator, chunk_data, data_offset):
    """Parses the SimpleDump Chunk and adds a DateTimeEvent.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      chunk_data (bytes): oversize chunk data.
      data_offset (int): offset of the oversize chunk relative to the start
          of the chunk set.

    Raises:
      ParseError: if the records cannot be parsed.
    """
    logger.debug('Reading SimpleDump')
    data_type_map = self._GetDataTypeMap('tracev3_simpledump_chunk')

    simpledump_structure = self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map)
    logger.debug(
        ('SimpleDump data: ProcID 1 {0:d} // ProcID 2 {1:d} // '
         'CT {2:d} // ThreadID {3:d}').format(
             simpledump_structure.first_number_proc_id,
             simpledump_structure.second_number_proc_id,
             simpledump_structure.continuous_time,
             simpledump_structure.thread_identifier))
    logger.debug('Substring: {0:s} // Message string: {1:s}'.format(
        simpledump_structure.subsystem_string,
        simpledump_structure.message_string
    ))

    event_data = AULEventData()
    generation_subchunk = self._header.generation_subchunk
    generation_subchunk_data = generation_subchunk.generation_subchunk_data
    event_data.boot_uuid = generation_subchunk_data.boot_uuid.hex.upper()
    event_data.level = 'SimpleDump'

    event_data.thread_identifier = simpledump_structure.thread_identifier
    event_data.pid = simpledump_structure.first_number_proc_id
    event_data.subsystem = simpledump_structure.subsystem_string
    event_data.library_uuid = simpledump_structure.sender_uuid.hex.upper()
    event_data.process_uuid = simpledump_structure.dsc_uuid.hex
    event_data.body = simpledump_structure.message_string
    logger.debug('Log line: {0!s}'.format(event_data.body))

    ct = simpledump_structure.continuous_time
    ts = FindClosestTimesyncItemInList(
        self._boot_uuid_ts.sync_records, ct, return_first=True)
    wt = ts.wall_time if ts else 0
    kct = ts.kernel_continuous_timestamp if ts else 0
    time = (
        wt
        + (ct * self._boot_uuid_ts.adjustment)
        - (kct * self._boot_uuid_ts.adjustment)
    )

    event_data.creation_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
        timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)

  def _ReadStateDumpChunkData(self, parser_mediator, chunk_data, data_offset):
    """Parses the StateDump Chunk and adds a DateTimeEvent.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      chunk_data (bytes): oversize chunk data.
      data_offset (int): offset of the oversize chunk relative to the start
        of the chunk set.

    Raises:
      ParseError: if the records cannot be parsed.
    """
    logger.debug('Reading StateDump')
    data_type_map = self._GetDataTypeMap('tracev3_statedump_chunk')

    statedump_structure = self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map)
    logger.debug(
        ('StateDump data: ProcID 1 {0:d} // ProcID 2 {1:d} // '
         'TTL {2:d} // CT {3:d} // String Name {4:s}').format(
             statedump_structure.first_number_proc_id,
             statedump_structure.second_number_proc_id,
             statedump_structure.ttl, statedump_structure.continuous_time,
             statedump_structure.string_name))

    try:
      statedump_structure.string1 = self._ReadStructureFromByteStream(
        statedump_structure.string1, 0, self._GetDataTypeMap('cstring'))
    except errors.ParseError:
      statedump_structure.string1 = ''

    try:
      statedump_structure.string2 = self._ReadStructureFromByteStream(
        statedump_structure.string2, 0, self._GetDataTypeMap('cstring'))
    except errors.ParseError:
      statedump_structure.string2 = ''

    proc_id = '{0:d}@{1:d}'.format(
        statedump_structure.first_number_proc_id,
        statedump_structure.second_number_proc_id)

    proc_info = self._catalog_process_entries.get(proc_id, None)
    if not proc_info:
      logger.error(
          'Could not find Process Info block for ID: {0:d}'.format(proc_id))
      return

    event_data = AULEventData()
    try:
      uuid_file = self._catalog.files[proc_info.main_uuid_index]
      event_data.process_uuid = uuid_file.uuid
      event_data.process = uuid_file.library_path
    except (IndexError, AttributeError):
      pass
    generation_subchunk = self._header.generation_subchunk
    generation_subchunk_data = generation_subchunk.generation_subchunk_data
    event_data.boot_uuid = generation_subchunk_data.boot_uuid.hex.upper()
    event_data.level = 'StateDump'

    ct = statedump_structure.continuous_time
    ts = FindClosestTimesyncItemInList(
      self._boot_uuid_ts.sync_records, ct, return_first=True)
    wt = ts.wall_time if ts else 0
    kct = ts.kernel_continuous_timestamp if ts else 0
    time = (
        wt
        + (ct * self._boot_uuid_ts.adjustment)
        - (kct * self._boot_uuid_ts.adjustment)
    )

    if statedump_structure.data_type == self._STATEDUMP_DATA_TYPE_PLIST:
      try:
        event_data.body = str(plistlib.loads(statedump_structure.data))
      except plistlib.InvalidFileException:
        logger.warning('StateDump PList not valid')
        return
    elif statedump_structure.data_type == self._STATEDUMP_DATA_TYPE_PROTOBUF:
      event_data.body = 'StateDump Protocol Buffer'
      logger.error('StateDump Protobuf not supported')
    elif statedump_structure.data_type == self._STATEDUMP_DATA_TYPE_CUSTOM:
      if statedump_structure.string1 == 'location':
        state_tracker_structure = {}
        extra_state_tracker_structure = {}

        if statedump_structure.string_name == 'CLDaemonStatusStateTracker':
          state_tracker_structure = self._ReadStructureFromByteStream(
              statedump_structure.data, 0,
              self._GetDataTypeMap('location_tracker_daemon_data')).__dict__

          if state_tracker_structure['reachability'] == 0x2:
            state_tracker_structure['reachability'] = 'kReachabilityLarge'
          else:
            state_tracker_structure['reachability'] = 'Unknown'

          if state_tracker_structure['charger_type'] == 0x0:
            state_tracker_structure['charger_type'] = 'kChargerTypeUnknown'
          else:
            state_tracker_structure['charger_type'] = 'Unknown'
        elif statedump_structure.string_name == 'CLClientManagerStateTracker':
          state_tracker_structure = (
              location.LocationClientStateTrackerParser().Parse(
                  statedump_structure.data
              )
          )
        elif statedump_structure.string_name == 'CLLocationManagerStateTracker':
          (
              state_tracker_structure,
              extra_state_tracker_structure,
          ) = location.LocationManagerStateTrackerParser().Parse(
              statedump_structure.data_size, statedump_structure.data
          )
        else:
          raise errors.ParseError(
            'Unknown location StateDump Custom object not supported')

        event_data.body = str({
            **state_tracker_structure,
            **extra_state_tracker_structure
        })
      else:
        logger.error('Non-location StateDump Custom object not supported')
        event_data.body = 'Unsupported StateDump object: {0:s}'.format(
            statedump_structure.string_name)
    else:
      logger.error('Unknown StateDump data type {0:d}'.format(
          statedump_structure.data_type))
      return

    event_data.activity_id = hex(statedump_structure.activity_id)
    event_data.pid = statedump_structure.first_number_proc_id

    event_data.creation_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
        timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)

  def _ReadUUIDTextFile(self, parser_mediator, uuid):
    """Reads a specific uuidtext file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      uuid (str): the UUID.

    Returns:
      UUIDTextFile: an uuidtext file or None if not available.
    """
    file_entry = self._uuidtext_file_entry.GetSubFileEntryByName(uuid[0:2])
    if file_entry:
      file_entry = file_entry.GetSubFileEntryByName(uuid[2:])

    uuidtext_file = None
    if file_entry:
      try:
        file_object = file_entry.GetFileObject()
        uuidtext_file = self._uuidtext_parser.ParseFileObject(file_object)
        uuidtext_file.uuid = uuid

      except (IOError, errors.ParseError) as exception:
        message = 'Unable to parse UUID file: {0:s} with error: {1!s}'.format(
            uuid, exception)
        parser_mediator.ProduceExtractionWarning(message)

    return uuidtext_file

  def _ParseActivityChunk(
      self, parser_mediator, tracepoint, proc_info, time):
    """Parses an activity chunk.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      tracepoint (tracev3_firehose_tracepoint): Firehose tracepoint chunk.
      proc_info (tracev3_catalog_process_information_entry): Process Info entry.
      time (int): Log timestamp.

    Raises:
      ParseError: if the non-activity chunk cannot be parsed.
    """
    logger.debug('Parsing activity')

    log_data = []
    offset = 0
    data = tracepoint.data
    flags = tracepoint.flags

    fmt = None
    private_string = None
    activity_id = None
    dsc_range = dsc.DSCRange()

    event_data = AULEventData()
    generation_subchunk = self._header.generation_subchunk
    generation_subchunk_data = generation_subchunk.generation_subchunk_data
    event_data.boot_uuid = generation_subchunk_data.boot_uuid.hex.upper()

    try:
      dsc_file = self._catalog.files[proc_info.catalog_dsc_index]
    except IndexError:
      dsc_file = None

    try:
      uuid_file = self._catalog.files[proc_info.main_uuid_index]
      event_data.process_uuid = uuid_file.uuid
      event_data.process = uuid_file.library_path
    except (AttributeError, IndexError):
      uuid_file = None

    uint32_data_type_map = self._GetDataTypeMap('uint32le')
    uint64_data_type_map = self._GetDataTypeMap('uint64le')

    if tracepoint.log_type != self._USER_ACTION_ACTIVITY_TYPE:
      activity_id = self._ReadStructureFromByteStream(
          data, offset, uint32_data_type_map)
      offset += 4
      sentinel = self._ReadStructureFromByteStream(
          data[offset:], offset, uint32_data_type_map)
      offset += 4

    if flags & UNIQUE_PID:
      unique_pid = self._ReadStructureFromByteStream(
          data[offset:], offset, uint64_data_type_map)
      offset += 8
      logger.debug('Signpost has unique_pid: {0:d}'.format(unique_pid))

    if flags & CURRENT_AID:
      logger.debug('Activity has current_aid')
      activity_id = self._ReadStructureFromByteStream(
          data, offset, uint32_data_type_map)
      offset += 4
      sentinel = self._ReadStructureFromByteStream(
          data[offset:], offset, uint32_data_type_map)
      offset += 4

    if flags & HAS_SUBSYSTEM:
      logger.debug('Activity has has_other_current_aid')
      activity_id = self._ReadStructureFromByteStream(
          data, offset, uint32_data_type_map)
      offset += 4
      sentinel = self._ReadStructureFromByteStream(
          data[offset:], offset, uint32_data_type_map)
      offset += 4

    # Note that sentinel currently is not used.
    _ = sentinel

    message_string_reference = self._ReadStructureFromByteStream(
        data[offset:], offset, uint32_data_type_map)
    offset += 4
    logger.debug('Unknown PCID: {0:d}'.format(message_string_reference))

    formatter_flags = self._FormatFlags(flags, data, offset)
    offset = formatter_flags.offset

    if flags & PRIVATE_STRING_RANGE:
      logger.error('Activity with Private String Range unsupported')
      return

    # If there's data...
    if tracepoint.data_size - offset >= 6:
      data_type_map = self._GetDataTypeMap('tracev3_firehose_tracepoint_data')
      data_meta = self._ReadStructureFromByteStream(
          data[offset:], offset, data_type_map)
      offset += 2

      logger.debug(
          'After activity data: Unknown {0:d} // Number of Items {1:d}'.format(
              data_meta.unknown1, data_meta.num_items))
      try:
        (log_data, deferred_data_items, offset) = self._ReadItems(
            data_meta, data, offset)
      except errors.ParseError as exception:
        logger.error('Unable to parse data items: {0!s}'.format(exception))
        return

      if flags & HAS_CONTEXT_DATA != 0:
        logger.error('Backtrace data in Activity log chunk unsupported')
        return

      if flags & HAS_DATA_REF:
        logger.error('Activity log chunk with Data Ref unsupported')
        return

      for item in deferred_data_items:
        if item[2] == 0:
          result = ''
        elif item[0] in FIREHOSE_ITEM_PRIVATE_STRING_TYPES:
          if not private_string:
            logger.error('Trying to read from empty Private String')
            return
          try:
            data_type_map = self._GetDataTypeMap('cstring')
            result = self._ReadStructureFromByteStream(
                private_string[item[1]:], 0, data_type_map)
            logger.debug('End result: {0:s}'.format(result))
          except errors.ParseError:
            result = ''  # Private
        else:
          if item[0] in FIREHOSE_ITEM_STRING_ARBITRARY_DATA_TYPES:
            result = data[offset + item[1]:offset + item[1] + item[2]]

          elif item[0] == FIREHOSE_ITEM_STRING_BASE64_TYPE:
            result = base64.encodebytes(
                data[offset + item[1]:offset + item[1] + item[2]]).strip()

          else:
            data_type_map = self._GetDataTypeMap('cstring')
            result = self._ReadStructureFromByteStream(
                data[offset + item[1]:], 0, data_type_map)
            logger.debug('End result: {0:s}'.format(result))

        log_data.insert(item[3], (item[0], item[2], result))

    if formatter_flags.shared_cache or formatter_flags.large_shared_cache != 0:
      extra_offset_value_result = tracepoint.format_string_location
      if formatter_flags.large_offset_data != 0:
        if (
            formatter_flags.large_offset_data
            != formatter_flags.large_shared_cache / 2
            and not formatter_flags.shared_cache
        ):
          # Recovery ?
          formatter_flags.large_offset_data = int(
              formatter_flags.large_shared_cache / 2
          )
          extra_offset_value = '{0:X}{1:08x}'.format(
              formatter_flags.large_offset_data,
              tracepoint.format_string_location,
          )
        elif formatter_flags.shared_cache:
          formatter_flags.large_offset_data = 8
          extra_offset_value = '{0:X}{1:07x}'.format(
              formatter_flags.large_offset_data,
              tracepoint.format_string_location,
          )
        else:
          extra_offset_value = '{0:X}{1:08x}'.format(
              formatter_flags.large_offset_data,
              tracepoint.format_string_location,
          )
        extra_offset_value_result = int(extra_offset_value, 16)
      (fmt, dsc_range) = self._ExtractSharedStrings(
          tracepoint.format_string_location, extra_offset_value_result,
          dsc_file)
    else:
      if formatter_flags.absolute:
        logger.error(
            'Absolute Activity not yet implemented')
        return
      if formatter_flags.uuid_relative:
        uuid_file = self._ExtractAltUUID(formatter_flags.uuid_relative)
        fmt = uuid_file.ReadFormatString(tracepoint.format_string_location)
      else:
        fmt = self._ExtractFormatStrings(
            tracepoint.format_string_location, uuid_file)

    event_data.level = LOG_TYPES.get(tracepoint.log_type, 'Default')

    # Info is 'Create' when it's an Activity
    if tracepoint.log_type == 0x1:
      event_data.level = 'Create'

    if activity_id:
      event_data.activity_id = hex(activity_id)
    event_data.thread_identifier = tracepoint.thread_identifier
    event_data.pid = proc_info.pid
    event_data.euid = proc_info.euid

    if dsc_range.uuid_index:
      dsc_uuid = dsc_file.uuids[dsc_range.uuid_index]
      dsc_range.path = dsc_uuid.path
      dsc_range.uuid = dsc_uuid.sender_identifier

    if dsc_range.path or uuid_file:
      event_data.library = (
          dsc_range.path if dsc_range.path else uuid_file.library_path
      )
    if dsc_range.uuid or uuid_file:
      event_data.library_uuid = (
          dsc_range.uuid.hex.upper()
          if dsc_range.uuid
          else uuid_file.uuid.upper()
      )
    event_data.body = self._FormatString(fmt, log_data)

    event_data.creation_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
        timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)

  def _ParseLoss(self, parser_mediator, tracepoint, proc_info, time):
    """Processes a Loss chunk.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      tracepoint (tracev3_firehose_tracepoint): Firehose tracepoint chunk.
      proc_info (tracev3_catalog_process_information_entry): Process Info entry.
      time (int): Log timestamp.

    Raises:
      ParseError: if the non-activity chunk cannot be parsed.
    """
    logger.debug('Reading Loss')
    data_type_map = self._GetDataTypeMap('tracev3_firehose_loss')

    loss_structure = self._ReadStructureFromByteStream(
        tracepoint.data, 0, data_type_map)
    logger.debug(
        'Loss data: Start Time {0:d} // End time {1:d} // Count {2:d}'.format(
            loss_structure.start_time, loss_structure.end_time,
            loss_structure.count))

    event_data = AULEventData()
    generation_subchunk = self._header.generation_subchunk
    generation_subchunk_data = generation_subchunk.generation_subchunk_data
    event_data.boot_uuid = generation_subchunk_data.boot_uuid.hex.upper()
    event_data.pid = proc_info.pid
    event_data.euid = proc_info.euid
    event_data.level = 'Loss'
    event_data.thread_identifier = tracepoint.thread_identifier
    event_data.body = 'Lost {0:d} log messages'.format(loss_structure.count)

    event_data.creation_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
        timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)

  def _ParseNonActivityChunk(
      self, parser_mediator, tracepoint, proc_info, time, private_strings):
    """Parses a non-activity chunk.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      tracepoint (tracev3_firehose_tracepoint): firehose tracepoint chunk.
      proc_info (tracev3_catalog_process_information_entry): process information
          entry.
      time (int): log timestamp.
      private_strings (tuple[int, bytes]): offset and data of the private
          strings, or None.

    Raises:
      ParseError: if the non-activity chunk cannot be parsed.
    """
    logger.debug('Parsing non-activity chunk.')

    log_data = []
    offset = 0
    data = tracepoint.data
    flags = tracepoint.flags

    activity_id = None
    data_ref_id = 0
    fmt = None
    private_string = None
    ttl_value = None

    event_data = AULEventData()
    generation_subchunk = self._header.generation_subchunk
    generation_subchunk_data = generation_subchunk.generation_subchunk_data
    event_data.boot_uuid = generation_subchunk_data.boot_uuid.hex.upper()

    try:
      dsc_file = self._catalog.files[proc_info.catalog_dsc_index]
    except (AttributeError, IndexError):
      dsc_file = None

    try:
      uuid_file = self._catalog.files[proc_info.main_uuid_index]
      event_data.process_uuid = uuid_file.uuid
      event_data.process = uuid_file.library_path
    except (AttributeError, IndexError):
      uuid_file = None

    uint8_data_type_map = self._GetDataTypeMap('uint8')
    uint16_data_type_map = self._GetDataTypeMap('uint16le')
    uint32_data_type_map = self._GetDataTypeMap('uint32le')

    if flags & CURRENT_AID:
      logger.debug('Non-activity has current_aid')

      activity_id = self._ReadStructureFromByteStream(
          data, offset, uint32_data_type_map)
      offset += 4

      sentinel = self._ReadStructureFromByteStream(
          data[offset:], offset, uint32_data_type_map)
      offset += 4

      if sentinel != self._NON_ACTIVITY_SENINTEL:
        logger.error('Incorrect sentinel value for non-activity')
        return

    if flags & PRIVATE_STRING_RANGE:
      logger.debug(
          'Non-activity has private_string_range (has_private_data flag)')

      private_strings_offset = self._ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 2
      private_strings_size = self._ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 2

    message_string_reference = self._ReadStructureFromByteStream(
        data[offset:], offset, uint32_data_type_map)
    offset += 4
    logger.debug('Unknown PCID: {0:d}'.format(message_string_reference))

    formatter_flags = self._FormatFlags(flags, data, offset)
    offset = formatter_flags.offset

    subsystem_value = ''
    if flags & HAS_SUBSYSTEM:
      subsystem_value = self._ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 2
      logger.debug('Non-activity has subsystem: {0:d}'.format(subsystem_value))

    if flags & HAS_TTL:
      ttl_value = self._ReadStructureFromByteStream(
          data[offset:], offset, uint8_data_type_map)
      offset += 1
      logger.debug('Non-activity has TTL: {0:d}'.format(ttl_value))

    if flags & HAS_DATA_REF:
      data_ref_id = self._ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 1
      logger.debug('Non-activity with data reference: {0:d}'.format(
          data_ref_id))

    if flags & HAS_SIGNPOST_NAME:
      logger.error('Non-activity signpost not supported')
      return

    if flags & HAS_MESSAGE_IN_UUIDTEXT:
      logger.debug('Non-activity has message in UUID Text file')
      if (flags & HAS_ALTERNATE_UUID and flags & HAS_SIGNPOST_NAME):
        logger.error(
            'Non-activity with Alternate UUID and Signpost not supported')
        return
      if not uuid_file:
        logger.error(
            'Unable to continue without matching UUID file')
        return
      if flags & HAS_SIGNPOST_NAME:
        logger.error('Non-activity signpost not supported (2)')
        return

    if flags & PRIVATE_STRING_RANGE:
      if private_strings:
        string_start = private_strings_offset - private_strings[0]
        if string_start > len(private_strings[1] or string_start < 0):
          logger.error('Error with private string offset')
          return
        private_string = private_strings[1][string_start:string_start +
                                            private_strings_size]
      else:
        logger.error('Private strings wanted but not supplied')
        return

    if tracepoint.log_activity_type == FIREHOSE_LOG_ACTIVITY_TYPE_LOSS:
      logger.error('Loss Type not supported')
      return

    data_type_map = self._GetDataTypeMap('tracev3_firehose_tracepoint_data')
    data_meta = self._ReadStructureFromByteStream(
        data[offset:], offset, data_type_map)
    offset += 2

    logger.debug(
        'After activity data: Unknown {0:d} // Number of Items {1:d}'.format(
            data_meta.unknown1, data_meta.num_items))
    try:
      (log_data, deferred_data_items, offset) = self._ReadItems(
          data_meta, data, offset)
    except errors.ParseError as exception:
      logger.error('Unable to parse data items: {0!s}'.format(exception))
      return

    backtrace_strings = []
    if flags & HAS_CONTEXT_DATA != 0 and len(data[offset:]) >= 6:
      logger.debug('Backtrace data in Firehose log chunk')
      backtrace_strings = ['Backtrace:\n']

      data_type_map = self._GetDataTypeMap('tracev3_backtrace')
      backtrace_data = self._ReadStructureFromByteStream(
          data[offset:], offset, data_type_map)
      for count, idx in enumerate(backtrace_data.indices):
        try:
          backtrace_strings.append('{0:s} +0x{1:d}\n'.format(
              backtrace_data.uuids[idx].hex.upper(),
              backtrace_data.offsets[count]))
        except IndexError:
          pass
    elif len(data[offset:]) > 3:
      if data[offset:offset + 3] == r'\x01\x00\x18':
        logger.error(
            'Backtrace signature without context not yet implemented')
        return

    #TODO(fryy): Turn item tuple into an object with names
    for item in deferred_data_items:
      if item is None:
        continue
      if item[2] == 0:
        result = ""
      elif item[0] in FIREHOSE_ITEM_PRIVATE_STRING_TYPES:
        if not private_string:
          logger.error('Trying to read from empty Private String')
          return
        if item[0] in FIREHOSE_ITEM_STRING_ARBITRARY_DATA_TYPES:
          result = private_string[item[1]:item[1] + item[2]]
        else:
          data_type_map = self._GetDataTypeMap('cstring')
          result = self._ReadStructureFromByteStream(
              private_string[item[1]:], 0, data_type_map)
          logger.debug('End result: {0:s}'.format(result))

      elif item[0] == FIREHOSE_ITEM_STRING_PRIVATE:
        # TODO: flip logic to reduce unnecessary indentation
        if not private_string:
          # A <private> string
          if item[2] == 0x8000:
            result = ""
          else:
            logger.error('Trying to read from empty Private String')
            return

        else:
          result = private_string[item[1]:item[1] + item[2]]
      else:
        if item[0] in FIREHOSE_ITEM_STRING_ARBITRARY_DATA_TYPES:
          result = data[offset + item[1]:offset + item[1] + item[2]]

        elif item[0] == FIREHOSE_ITEM_STRING_BASE64_TYPE:
          result = base64.encodebytes(data[offset + item[1]:offset + item[1] +
                                           item[2]]).strip()
        else:
          data_type_map = self._GetDataTypeMap('cstring')

          try:
            result = self._ReadStructureFromByteStream(
                data[offset + item[1]:], 0, data_type_map)
          except errors.ParseError:
            result = data[offset + item[1]:].decode('utf-8')

          logger.debug('End result: {0:s}'.format(result))

      log_data.insert(item[3], (item[0], item[2], result))

    if tracepoint.log_activity_type == FIREHOSE_LOG_ACTIVITY_TYPE_LOSS:
      logger.error('Loss Type not supported')
      return

    dsc_range = dsc.DSCRange()
    extra_offset_value_result = tracepoint.format_string_location
    if formatter_flags.shared_cache or formatter_flags.large_shared_cache != 0:
      if formatter_flags.large_offset_data != 0:
        if (
            formatter_flags.large_offset_data
            != formatter_flags.large_shared_cache / 2
            and not formatter_flags.shared_cache
        ):
          formatter_flags.large_offset_data = (
              formatter_flags.large_shared_cache / 2
          )
          extra_offset_value = '{0:X}{1:08x}'.format(
              formatter_flags.large_offset_data,
              tracepoint.format_string_location)
        elif formatter_flags.shared_cache:
          formatter_flags.large_offset_data = 8
          extra_offset_value = '{0:X}{1:07x}'.format(
              formatter_flags.large_offset_data,
              tracepoint.format_string_location)
        else:
          extra_offset_value = '{0:X}{1:08x}'.format(
              formatter_flags.large_offset_data,
              tracepoint.format_string_location)
        extra_offset_value_result = int(extra_offset_value, 16)
      (fmt, dsc_range) = self._ExtractSharedStrings(
          tracepoint.format_string_location, extra_offset_value_result,
          dsc_file)
    else:
      if formatter_flags.absolute:
        uuid_file = self._ExtractAbsoluteStrings(
            tracepoint.format_string_location, formatter_flags.uuid_file_index,
            proc_info, message_string_reference)
        if uuid_file and uuid_file != '%s':
          fmt = uuid_file.ReadFormatString(tracepoint.format_string_location)
        else:
          fmt = uuid_file
          uuid_file = None
      elif formatter_flags.uuid_relative:
        uuid_file = self._ExtractAltUUID(formatter_flags.uuid_relative)
        if uuid_file:
          fmt = uuid_file.ReadFormatString(tracepoint.format_string_location)
        else:
          fmt = uuid_file
          uuid_file = None
      else:
        fmt = self._ExtractFormatStrings(
            tracepoint.format_string_location, uuid_file)

    found = False
    if data_ref_id != 0:
      for oversize_data in self._oversize_data:
        if (oversize_data.first_proc_id == proc_info.first_number_proc_id and
            oversize_data.second_proc_id == proc_info.second_number_proc_id and
            oversize_data.data_ref_index == data_ref_id):
          log_data = oversize_data.strings
          found = True
          break

      if not found:
        logger.warning((
            'Did not find any oversize log entries from Data Ref ID: {0:d}, '
            'First Proc ID: {1:d}, and Second Proc ID: {2:d}').format(
                data_ref_id, proc_info.first_number_proc_id,
                proc_info.second_number_proc_id))

    if fmt:
      event_data.body = ''.join(backtrace_strings) + self._FormatString(
          fmt, log_data)
    elif not fmt and not log_data:
      return  # Nothing to do ??
    else:
      if uuid_file:
        uuid = uuid_file.uuid
      else:
        uuid = 'UNKNOWN'
      event_data.body = 'Error: Invalid offset {0:d} for UUID {1:s}'.format(
          tracepoint.format_string_location, uuid)

    event_data.thread_identifier = tracepoint.thread_identifier
    event_data.level = LOG_TYPES.get(tracepoint.log_type, 'Default')
    if activity_id:
      event_data.activity_id = hex(activity_id)
    if ttl_value:
      event_data.ttl = ttl_value
    event_data.pid = proc_info.pid
    event_data.euid = proc_info.euid
    event_data.subsystem = (proc_info.items.get(subsystem_value, ('', '')))[0]
    event_data.category = (proc_info.items.get(subsystem_value, ('', '')))[1]

    if dsc_range.uuid_index:
      dsc_uuid = dsc_file.uuids[dsc_range.uuid_index]
      dsc_range.path = dsc_uuid.path
      dsc_range.uuid = dsc_uuid.sender_identifier

    if dsc_range.path or uuid_file:
      event_data.library = (
          dsc_range.path if dsc_range.path else uuid_file.library_path
      )
    if dsc_range.uuid or uuid_file:
      event_data.library_uuid = (
          dsc_range.uuid.hex.upper()
          if dsc_range.uuid
          else uuid_file.uuid.upper()
      )

    event_data.creation_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
        timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)

  def _ParseOversizeChunkData(self, chunk_data, data_offset):
    """Processes the Oversized data chunk.

    Args:
      chunk_data (bytes): oversize chunk data.
      data_offset (int): offset of the oversize chunk relative to the start
        of the chunk set.

    Returns:
      AULOversizeData: oversized data or None if the oversize chunk cannot be
          parsed.

    Raises:
      ParseError: if the oversize chunk cannot be parsed.
    """
    logger.debug('Reading Oversize')
    data_type_map = self._GetDataTypeMap('tracev3_oversize_chunk')

    oversize = self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map)
    logger.debug((
        'Firehose Header data: ProcID 1 {0:d} // ProcID 2 {1:d} // '
        'Ref Index {2:d} // CT {3:d} (Oversize)').format(
            oversize.first_number_proc_id, oversize.second_number_proc_id,
            oversize.data_ref_index, oversize.continuous_time))

    offset = 0
    data_meta = self._ReadStructureFromByteStream(
        oversize.data,
        offset,
        self._GetDataTypeMap('tracev3_firehose_tracepoint_data'))
    offset += 2

    logger.debug(
        'After activity data: Unknown {0:d} // Number of Items {1:d}'.format(
            data_meta.unknown1, data_meta.num_items))
    try:
      (oversize_strings, deferred_data_items, offset) = self._ReadItems(
          data_meta, oversize.data, offset)
    except errors.ParseError as exception:
      logger.error('Unable to parse data items: {0!s}'.format(exception))
      return None

    # Check for backtrace
    if oversize.data[offset:offset+3] == [0x01, 0x00, 0x18]:
      logger.error('Backtrace found in Oversize chunk')
      return None

    data_type_map = self._GetDataTypeMap('cstring')

    private_items = []
    rolling_offset = offset
    for index, item in enumerate(deferred_data_items):
      if item[2] == 0:
        oversize_strings.append((item[0], item[2], ""))
        continue

      if item[0] in FIREHOSE_ITEM_PRIVATE_STRING_TYPES:
        logger.debug('Private Oversize')
        private_items.append((item, index))
        oversize_strings.insert(index, (item[0], item[2], '<private>'))
        continue

      string = self._ReadStructureFromByteStream(
          oversize.data[offset + item[1]:], 0, data_type_map)

      oversize_strings.append((item[0], item[2], string))
      rolling_offset += item[2]

    offset = rolling_offset
    for item, index in private_items:
      string = self._ReadStructureFromByteStream(
          oversize.data[offset + item[1]:], 0, data_type_map)

      oversize_strings[index] = (item[0], item[2], string)

    oversize = AULOversizeData(
        oversize.first_number_proc_id,
        oversize.second_number_proc_id,
        oversize.data_ref_index)
    oversize.strings = oversize_strings
    logger.debug('Oversize Data: {0!s}'.format(oversize_strings))
    return oversize

  def _ParseSignpostChunk(
      self, parser_mediator, tracepoint, proc_info, time, private_strings):
    """Processes a Signpost chunk.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      tracepoint (tracev3_firehose_tracepoint): Firehose tracepoint chunk.
      proc_info (tracev3_catalog_process_information_entry): Process Info entry.
      time (int): Log timestamp.
      private_strings (tuple[int, bytes]): Offset and data of the private
        strings, or None.

    Raises:
      ParseError: if the non-activity chunk cannot be parsed.
    """
    logger.debug('Parsing Signpost')

    log_data = []
    offset = 0
    data = tracepoint.data
    flags = tracepoint.flags

    data_ref_id = 0
    fmt = None
    private_string = None
    ttl_value = None

    event_data = AULEventData()
    generation_subchunk = self._header.generation_subchunk
    generation_subchunk_data = generation_subchunk.generation_subchunk_data
    event_data.boot_uuid = generation_subchunk_data.boot_uuid.hex.upper()
    event_data.pid = proc_info.pid
    event_data.euid = proc_info.euid

    try:
      dsc_file = self._catalog.files[proc_info.catalog_dsc_index]
    except IndexError:
      dsc_file = None

    try:
      uuid_file = self._catalog.files[proc_info.main_uuid_index]
      event_data.process_uuid = uuid_file.uuid
      event_data.process = uuid_file.library_path
    except IndexError:
      uuid_file = None

    uint8_data_type_map = self._GetDataTypeMap('uint8')
    uint16_data_type_map = self._GetDataTypeMap('uint16')
    uint32_data_type_map = self._GetDataTypeMap('uint32')
    uint64_data_type_map = self._GetDataTypeMap('uint64')

    if flags & CURRENT_AID:
      logger.debug('Signpost has current_aid')
      activity_id = self._ReadStructureFromByteStream(
          data, offset, uint32_data_type_map)
      offset += 4

      sentinel = self._ReadStructureFromByteStream(
          data[offset:], offset, uint32_data_type_map)
      offset += 4

      # Note that activity_id and sentinel are currently unused.
      _ = activity_id
      _ = sentinel

    if flags & PRIVATE_STRING_RANGE:
      logger.debug('Signpost has private_string_range (has_private_data flag)')

      private_strings_offset = self._ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 2
      private_strings_size = self._ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 2

    message_string_reference = self._ReadStructureFromByteStream(
        data[offset:], offset, uint32_data_type_map)
    offset += 4
    logger.debug('Unknown PCID: {0:d}'.format(message_string_reference))

    formatter_flags = self._FormatFlags(flags, data, offset)
    offset = formatter_flags.offset

    subsystem_value = ''
    if flags & HAS_SUBSYSTEM:
      subsystem_value = self._ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 2
      logger.debug('Signpost has subsystem: {0:d}'.format(subsystem_value))

    signpost_id = self._ReadStructureFromByteStream(
        data[offset:], offset, uint64_data_type_map)
    offset += 8

    if flags & HAS_TTL:
      ttl_value = self._ReadStructureFromByteStream(
          data[offset:], offset, uint8_data_type_map)
      offset += 1
      logger.debug('Signpost has TTL: {0:d}'.format(ttl_value))

    if flags & HAS_DATA_REF:
      data_ref_id = self._ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 1
      logger.debug('Signpost with data reference: {0:d}'.format(data_ref_id))

    if flags & HAS_SIGNPOST_NAME:
      signpost_name = self._ReadStructureFromByteStream(
          data[offset:], offset, uint32_data_type_map)
      offset += 4
      if formatter_flags.large_shared_cache != 0:
        offset += 2

    if flags & PRIVATE_STRING_RANGE:
      if private_strings:
        string_start = private_strings_offset - private_strings[0]
        if string_start > len(private_strings[1] or string_start < 0):
          logger.error('Error with private string offset')
          return
        private_string = private_strings[1][string_start:string_start +
                                            private_strings_size]
      else:
        logger.error('Private strings wanted but not supplied')
        return

    data_type_map = self._GetDataTypeMap('tracev3_firehose_tracepoint_data')
    data_meta = self._ReadStructureFromByteStream(
        data[offset:], offset, data_type_map)
    offset += 2

    logger.debug(
        'After activity data: Unknown {0:d} // Number of Items {1:d}'.format(
            data_meta.unknown1, data_meta.num_items))
    try:
      (log_data, deferred_data_items,
      offset) = self._ReadItems(data_meta, data, offset)
    except errors.ParseError as exception:
      logger.error('Unable to parse data items: {0!s}'.format(exception))
      return

    if flags & HAS_CONTEXT_DATA != 0:
      logger.error('Backtrace data in Signpost log chunk')
      return

    for item in deferred_data_items:
      if item[2] == 0:
        result = ''
      elif item[0] in FIREHOSE_ITEM_PRIVATE_STRING_TYPES:
        if not private_string:
          logger.error('Trying to read from empty Private String')
          return
        try:
          data_type_map = self._GetDataTypeMap('cstring')
          result = self._ReadStructureFromByteStream(
              private_string[item[1]:], 0, data_type_map)
          logger.debug('End result: {0:s}'.format(result))
        except errors.ParseError:
          result = ''  # Private
      else:
        if item[0] in FIREHOSE_ITEM_STRING_ARBITRARY_DATA_TYPES:
          result = data[offset + item[1]:offset + item[1] + item[2]]
        elif item[0] == FIREHOSE_ITEM_STRING_BASE64_TYPE:
          result = base64.encodebytes(data[offset + item[1]:offset + item[1] +
                                           item[2]]).strip()
        else:
          data_type_map = self._GetDataTypeMap('cstring')
          result = self._ReadStructureFromByteStream(
              data[offset + item[1]:], 0, data_type_map)
          logger.debug('End result: {0:s}'.format(result))
      log_data.insert(item[3], (item[0], item[2], result))

    found = False
    dsc_range = dsc.DSCRange()

    if data_ref_id != 0:
      for oversize_data in self._oversize_data:
        if (oversize_data.first_proc_id == proc_info.first_number_proc_id and
            oversize_data.second_proc_id == proc_info.second_number_proc_id and
            oversize_data.data_ref_index == data_ref_id):
          log_data = oversize_data.strings
          found = True
          break

      if not found:
        logger.debug((
            'Did not find any oversize log entries from Data Ref ID: '
            '{0:d}, First Proc ID: {1:d}, and Second Proc ID: {2:d}').format(
                data_ref_id, proc_info.first_number_proc_id,
                proc_info.second_number_proc_id))

    if formatter_flags.shared_cache or formatter_flags.large_shared_cache != 0:
      if formatter_flags.large_offset_data != 0:
        logger.error(
            'Large offset Signpost not yet implemented')
        return
      extra_offset_value_result = tracepoint.format_string_location
      (fmt, dsc_range) = self._ExtractSharedStrings(
          tracepoint.format_string_location, extra_offset_value_result,
          dsc_file)
    else:
      if formatter_flags.absolute:
        uuid_file = self._ExtractAbsoluteStrings(
            tracepoint.format_string_location, formatter_flags.uuid_file_index,
            proc_info, message_string_reference)
        if uuid_file != '%s':
          fmt = uuid_file.ReadFormatString(tracepoint.format_string_location)
        else:
          fmt = uuid_file
          uuid_file = None
      elif formatter_flags.uuid_relative:
        uuid_file = self._ExtractAltUUID(formatter_flags.uuid_relative)
        fmt = uuid_file.ReadFormatString(tracepoint.format_string_location)
      else:
        fmt = self._ExtractFormatStrings(
            tracepoint.format_string_location, uuid_file)

    event_data.level = 'Signpost'

    if dsc_range.uuid_index:
      dsc_uuid = dsc_file.uuids[dsc_range.uuid_index]
      dsc_range.path = dsc_uuid.path
      dsc_range.uuid = dsc_uuid.sender_identifier

    event_data.library = (
        dsc_range.path if dsc_range.path else uuid_file.library_path
    )
    event_data.library_uuid = (
        dsc_range.uuid.hex.upper() if dsc_range.uuid else uuid_file.uuid.upper()
    )
    event_data.thread_identifier = tracepoint.thread_identifier
    event_data.subsystem = (proc_info.items.get(subsystem_value, ('', '')))[0]
    event_data.category = (proc_info.items.get(subsystem_value, ('', '')))[1]

    if ttl_value:
      event_data.ttl = ttl_value

    event_data.body = 'Signpost ID: {} - Signpost Name: {} - {}'.format(
        hex(signpost_id).upper()[2:],
        hex(signpost_name).upper()[2:],
        self._FormatString(fmt, log_data))

    event_data.creation_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
        timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)

  def _ParseTimeSyncDatabases(self, parser_mediator):
    """Parses the timesync database files.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    self._timesync_parser = timesync.TimesyncDatabaseFileParser()

    # The timesync database files are stored in ../../timesync relative from
    # the tracev3 file.
    timesync_file_entry = self._tracev3_file_entry.GetParentFileEntry()
    timesync_file_entry = timesync_file_entry.GetParentFileEntry()
    timesync_file_entry = timesync_file_entry.GetSubFileEntryByName('timesync')

    for sub_file_entry in timesync_file_entry.sub_file_entries:
      if sub_file_entry.name.endswith('.timesync'):
        file_object = sub_file_entry.GetFileObject()
        if not file_object:
          relative_path = parser_mediator.GetRelativePathForPathSpec(
              sub_file_entry.path_spec)
          parser_mediator.ProduceExtractionWarning(
              'Unable to open timesync database file: {0:s}.'.format(
                  relative_path))
          continue

        try:
          self._timesync_parser.ParseFileObject(file_object)
        except (IOError, errors.ParseError) as exception:
          relative_path = parser_mediator.GetRelativePathForPathSpec(
              sub_file_entry.path_spec)
          parser_mediator.ProduceExtractionWarning(
              'Unable to parse data block file: {0:s} with error: {1!s}'.format(
                  relative_path, exception))

  def _ParseTracepointData(
      self, parser_mediator, tracepoint, proc_info, time, private_strings):
    """Parses tracepoint data.

    Args:
      TODO:
    """
    logger.debug('Parsing log line')
    log_type = LOG_TYPES.get(tracepoint.log_type, 'Default')
    if tracepoint.log_activity_type == FIREHOSE_LOG_ACTIVITY_TYPE_NONACTIVITY:
      if log_type == 0x80:
        logger.error('Non Activity Signpost not supported')
        return

      self._ParseNonActivityChunk(
          parser_mediator, tracepoint, proc_info, time, private_strings)

    elif tracepoint.log_activity_type == FIREHOSE_LOG_ACTIVITY_TYPE_SIGNPOST:
      self._ParseSignpostChunk(
          parser_mediator, tracepoint, proc_info, time, private_strings)

    elif tracepoint.log_activity_type == FIREHOSE_LOG_ACTIVITY_TYPE_ACTIVITY:
      self._ParseActivityChunk(parser_mediator, tracepoint, proc_info, time)

    elif tracepoint.log_activity_type == FIREHOSE_LOG_ACTIVITY_TYPE_LOSS:
      self._ParseLoss(parser_mediator, tracepoint, proc_info, time)

    elif tracepoint.log_activity_type == FIREHOSE_LOG_ACTIVITY_TYPE_TRACE:
      self._ParceTrace(parser_mediator, tracepoint, proc_info, time)

    elif tracepoint.log_activity_type == 0x0:
      logger.warning('Remnant/Garbage data')

    else:
      logger.error('Unsupported log activity type: {}'.format(
          tracepoint.log_activity_type))

  def _ParceTrace(
      self, parser_mediator, tracepoint, proc_info, time):
    """Parses a Trace chunk.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      tracepoint (tracev3_firehose_tracepoint): Firehose tracepoint chunk.
      proc_info (tracev3_catalog_process_information_entry): Process Info entry.
      time (int): Log timestamp.

    Raises:
      ParseError: if the records cannot be parsed.
    """
    logger.debug('Reading Trace')
    data = tracepoint.data

    event_data = AULEventData()
    generation_subchunk = self._header.generation_subchunk
    generation_subchunk_data = generation_subchunk.generation_subchunk_data
    event_data.boot_uuid = generation_subchunk_data.boot_uuid.hex.upper()

    try:
      uuid_file = self._catalog.files[proc_info.main_uuid_index]
      event_data.process_uuid = uuid_file.uuid
      event_data.process = uuid_file.library_path
    except (AttributeError, IndexError):
      uuid_file = None

    offset = 0

    message_string_reference = self._ReadStructureFromByteStream(
        data[offset:], offset, self._GetDataTypeMap('uint32'))
    logger.debug('Unknown PCID: {0:d}'.format(message_string_reference))
    offset += 4

    item_data = b''
    if len(data[offset:]) < 4:
      logger.warning('Insufficent trace data')
    else:
      item_data = data[offset:offset + 2]
      offset += 2

    format_string = self._ExtractFormatStrings(
        tracepoint.format_string_location, uuid_file)

    if format_string:
      logger.debug('Format string: {0:s}'.format(format_string))
      event_data.body = self._FormatString(
          format_string, [(0, len(item_data), item_data)])

    event_data.thread_identifier = tracepoint.thread_identifier
    event_data.pid = proc_info.pid
    event_data.euid = proc_info.euid
    if uuid_file:
      event_data.library = uuid_file.library_path
    if uuid_file:
      event_data.library_uuid = uuid_file.uuid.upper()

    event_data.creation_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
        timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)

  def _TimestampFromContTime(self, boot_uuid_ts_list, ct):
    """Converts a continuous time into a Date Time string.

    Args:
      boot_uuid_ts_list (List[timesync_sync_record]): List of
          timesync boot records.
      ct (int): A continuous time stamp.

    Returns:
      str: date time string or "N/A" if not available.
    """
    ts = FindClosestTimesyncItemInList(boot_uuid_ts_list, ct)
    time_string = 'N/A'
    if ts is not None:
      time = ts.wall_time + ct - ts.kernel_continuous_timestamp
      date_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
          timestamp=int(time))
      time_string = date_time.CopyToDateTimeString()
    return time_string

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(
        b'\x00\x10\x00\x00', offset=0)
    return format_specification

  # TODO: merge with ParseFileObject.
  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses an Apple Unified Logging file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_entry (dfvfs.FileEntry): file entry.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_object = file_entry.GetFileObject()
    if not file_object:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] unable to open tracev3 file {1:s}'.format(
              self.NAME, display_name))

    self._tracev3_file_entry = file_entry

    # The uuidtext files are stored in ../../../uuidtext/ relative from
    # the tracev3 file.
    self._uuidtext_file_entry = file_entry.GetParentFileEntry()
    self._uuidtext_file_entry = self._uuidtext_file_entry.GetParentFileEntry()
    self._uuidtext_file_entry = self._uuidtext_file_entry.GetParentFileEntry()
    self._uuidtext_file_entry = self._uuidtext_file_entry.GetSubFileEntryByName(
        'uuidtext')

    self._cached_uuidtext_files = {}

    self._ParseTimeSyncDatabases(parser_mediator)

    try:
      self.ParseFileObject(parser_mediator, file_object)
    except (IOError, errors.ParseError) as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] unable to parse tracev3 file {1:s} with error: {2!s}'.format(
              self.NAME, display_name, exception))

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a timezone information file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      WrongParser: when the file cannot be parsed.
      ParseError: if we encounter an unsupported chunk type.
    """
    file_offset = 0
    file_size = file_object.get_size()

    chunkset_index = 0

    while file_offset < file_size:
      chunk_header = self._ReadChunkHeader(file_object, file_offset)
      file_offset += 16

      if chunk_header.chunk_tag == self._CHUNK_TAG_HEADER:
        self._ReadHeaderChunk(file_object, file_offset)

      elif chunk_header.chunk_tag == self._CHUNK_TAG_CATALOG:
        self._catalog = self._ReadCatalog(
            parser_mediator, file_object, file_offset)
        chunkset_index = 0

      elif chunk_header.chunk_tag == self._CHUNK_TAG_CHUNKSET:
        self._ReadChunkSet(
            parser_mediator, file_object, file_offset, chunk_header,
            chunkset_index)
        chunkset_index += 1

      else:
        raise errors.ParseError(
            'Unsupported chunk tag: 0x{0:04x}'.format(chunk_header.chunk_tag))

      file_offset += chunk_header.chunk_data_size

      _, alignment = divmod(file_offset, 8)
      if alignment > 0:
        alignment = 8 - alignment

      file_offset += alignment


manager.ParsersManager.RegisterParser(AULParser)
