# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) TraceV3 file parser."""

import binascii
import decimal
import ipaddress
import os
import re
import stat

import lz4.block

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.helpers.macos import darwin
from plaso.helpers.macos import dns
from plaso.helpers.macos import location
from plaso.helpers.macos import opendirectory
from plaso.helpers.macos import tcp
from plaso.helpers import sqlite

from plaso.lib.aul import activity
from plaso.lib.aul import constants
from plaso.lib.aul import dsc
from plaso.lib.aul import loss
from plaso.lib.aul import nonactivity
from plaso.lib.aul import oversize
from plaso.lib.aul import signpost
from plaso.lib.aul import simpledump
from plaso.lib.aul import statedump
from plaso.lib.aul import trace
from plaso.lib.aul import time as aul_time

from plaso.lib import dtfabric_helper
from plaso.lib import errors

from plaso.parsers import interface
from plaso.parsers import logger


class TraceV3FileParser(interface.FileObjectParser,
                        dtfabric_helper.DtFabricHelper):
  """Apple Unified Logging and Activity Tracing (tracev3) file."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'aul.yaml')

  _CATALOG_LZ4_COMPRESSION = 0x100

  # Chunk Tags
  _CHUNK_TAG_HEADER = 0x1000
  _CHUNK_TAG_FIREHOSE = 0x6001
  _CHUNK_TAG_OVERSIZE = 0x6002
  _CHUNK_TAG_STATEDUMP = 0x6003
  _CHUNK_TAG_SIMPLEDUMP = 0x6004
  _CHUNK_TAG_CATALOG = 0x600B
  _CHUNK_TAG_CHUNKSET = 0x600D

  # pylint: disable=line-too-long
  # Taken from https://github.com/ydkhatri/UnifiedLogReader/blob/master/UnifiedLog/tracev3_file.py#L56
  # pylint: enable=line-too-long
  format_strings_re = re.compile(
      r'%(\{[^\}]{1,64}\})?([0-9.'
      r" *\-+#']{0,6})([hljztLq]{0,2})([@dDiuUxXoOfeEgGcCsSpaAFPm])"
  )

  def __init__(self, timesync_parser, uuid_parser, dsc_parser):
    """Initializes a tracev3 file parser."""
    super(TraceV3FileParser, self).__init__()
    self.boot_uuid_ts = None
    self.catalog = None
    self.catalog_files = []
    self.chunksets = []
    self.dsc_parser = dsc_parser
    self.header = None
    self.logs = []
    self.oversize_data = []
    self.timesync_parser = timesync_parser
    self.uuid_parser = uuid_parser

  def GetDataTypeMap(self, name):
    """Wrapper around dtfabric's _GetDataTypeMap()"""
    return self._GetDataTypeMap(name)

  def ReadStructureFromByteStream(self, data, offset, data_map):
    """Wrapper around dtfabric's _ReadStructureFromByteStream"""
    return self._ReadStructureFromByteStream(data, offset, data_map)

  def FormatString(self, format_string, data):
    """Substitutes data items into the format string.

    Args:
      format_string (str): The supplied format string.
      data (list[tuple[int, int, bytes]]): List of data items

    Returns:
      string

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
          data_item[0] == constants.FIREHOSE_ITEM_DYNAMIC_PRECISION_TYPE
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
              in constants.FIREHOSE_ITEM_PRIVATE_STRING_TYPES
              + constants.FIREHOSE_ITEM_STRING_ARBITRARY_DATA_TYPES
              + [constants.FIREHOSE_ITEM_STRING_PRIVATE]
          )
          and len(raw_data) == 0
          and (
              data_size == 0
              or (
                  data_type == constants.FIREHOSE_ITEM_STRING_PRIVATE
                  and data_size == 0x8000
              )
          )
      ) or (
          data_type == constants.FIREHOSE_ITEM_SENSITIVE
          and custom_specifier == '{sensitive}'
      ):
        output += '<private>'
        i += 1
        continue

      if (specifier
          not in ('p', 'P', 's', 'S')) and '*' in flags_width_precision:
        logger.error("* not supported for p/P/s/S")
        output += 'Unsupported specifier'
        i += 1
        continue

      if (
          data_type in constants.FIREHOSE_ITEM_STRING_ARBITRARY_DATA_TYPES
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
            and data_type != constants.FIREHOSE_ITEM_STRING_PRIVATE
        ):
          output += 'Invalid specifier'
          logger.error(
              'Size 0 in int fmt {0:s} // data {1!s}'.format(
                  format_string, data_item))
          i += 1
          continue

        if (
            data_type == constants.FIREHOSE_ITEM_STRING_PRIVATE and not raw_data
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
            output += "[{0:d}: {1:s}]".format(
              number, darwin.DarwinErrorHelper.GetError(number))
          elif '{darwin.mode}' in custom_specifier:
            output += "{0:s} ({1:s})".format(
              oct(number).replace('o', ''), stat.filemode(number))
          elif 'odtypes:ODError' in custom_specifier:
            output += opendirectory.ODErrorsHelper.GetError(number)
          elif 'odtypes:mbridtype' in custom_specifier:
            output += opendirectory.ODMBRIdHelper.GetType(number)
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
              output += "add"
            else:
              output += "rmv"
          elif 'mdns:rrtype' in custom_specifier:
            output += dns.DNS.GetRecordType(number)
          elif 'mdns:yesno' in custom_specifier:
            if number == 0:
              output += "no"
            else:
              output += "yes"
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
              output += "unacceptable"
            else:
              output += "acceptable"
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
            and data_type != constants.FIREHOSE_ITEM_STRING_PRIVATE
        ):
          logger.error(
              'Size 0 in float fmt {0:s} // data {1!s}'.format(
                  format_string, data_item))
          output += 'Invalid specifier'
          i += 1
          continue
        if (
            data_type == constants.FIREHOSE_ITEM_STRING_PRIVATE and not raw_data
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
          if data_type in constants.FIREHOSE_ITEM_STRING_TYPES:
            chars = '(null)'
          elif data_type & constants.FIREHOSE_ITEM_STRING_PRIVATE:
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
              data_type in constants.FIREHOSE_ITEM_PRIVATE_STRING_TYPES
              and not raw_data
          ):
            chars = '<private>'
          else:
            uuid = self._ReadStructureFromByteStream(raw_data, 0,
                                                     uuid_data_type_map)
            chars = str(uuid).upper()
        elif 'odtypes:mbr_details' in custom_specifier:
          if raw_data[0] in constants.USER_TYPES + constants.GROUP_TYPES:
            user_group_type = self._ReadStructureFromByteStream(
                raw_data[1:], 1, self._GetDataTypeMap('mbr_user_group_type'))
            mbr_type = 'group'
            if raw_data[0] in constants.USER_TYPES:
              mbr_type = 'user'
            chars = '{0:s}: {1:s}@{2:s}'.format(
                mbr_type,
                user_group_type.name,
                (user_group_type.domain or '<not found>'),
            )
          elif raw_data[0] in constants.UID_TYPES + constants.GID_TYPES:
            uid_gid_type = self._ReadStructureFromByteStream(
                raw_data[1:], 1, self._GetDataTypeMap('mbr_uid_gid_type'))
            mbr_type = 'group'
            if raw_data[0] in constants.UID_TYPES:
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
          if data_type & constants.FIREHOSE_ITEM_STRING_PRIVATE:
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

  def _ReadHeader(self, file_object, file_offset):
    """Reads a Header.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the catalog data relative to the start of the
        file.

    Raises:
      ParseError: if the chunk header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_header')

    self.header, _ = self._ReadStructureFromFileObject(file_object, file_offset,
                                                       data_type_map)

    logger.debug('Header data: CT {0:d} // Bias {1:d}'.format(
        self.header.continuous_time, self.header.bias_in_minutes))
    logger.debug('SI Info: BVS: {0:s} // HMS: {1:s}'.format(
        self.header.systeminfo_subchunk.systeminfo_subchunk_data
        .build_version_string, self.header.systeminfo_subchunk
        .systeminfo_subchunk_data.hardware_model_string))
    logger.debug('Boot UUID: {0:s}'.format(
        self.header.generation_subchunk.generation_subchunk_data.boot_uuid.hex))
    logger.debug('TZ Info: {0:s}'.format(
        self.header.timezone_subchunk.timezone_subchunk_data.path_to_tzfile))

    self.boot_uuid_ts = aul_time.GetBootUuidTimeSync(
        self.timesync_parser.records,
        self.header.generation_subchunk.generation_subchunk_data.boot_uuid)
    logger.debug(
        'Tracev3 Header Timestamp: %s',
        aul_time.TimestampFromContTime(
            self.boot_uuid_ts.sync_records,
            self.header.continuous_time_subchunk.continuous_time_data))

  def _ReadCatalog(self, parser_mediator, file_object, file_offset):
    """Reads a catalog.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the catalog data relative to the start of the
        file.

    Raises:
      ParseError: if the chunk header cannot be read.
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
      for file in self.catalog_files:
        if file.uuid == filename:
          found = file
          found_in_cache = True
          logger.debug('Found in cache')
          break
      if not found:
        found = self.dsc_parser.FindFile(parser_mediator, filename)
      if not found:
        found = self.uuid_parser.FindFile(parser_mediator, filename)
        if not found:
          logger.error(
              'Neither UUID nor DSC file found for UUID: {0:s}'.format(
                  uuid.hex))
          catalog.files.append(None)
          continue
        if not found_in_cache:
          self.catalog_files.append(found)
        catalog.files.append(found)
      else:
        if not found_in_cache:
          self.catalog_files.append(found)
        catalog.files.append(found)

    data_type_map = self._GetDataTypeMap(
        'tracev3_catalog_process_information_entry')
    catalog.process_entries = []

    for _ in range(catalog.number_of_process_information_entries):
      process_entry, new_bytes = self._ReadStructureFromFileObject(
          file_object, file_offset + offset_bytes, data_type_map)
      try:
        process_entry.main_uuid = catalog.uuids[process_entry.main_uuid_index]
      except IndexError:
        pass
      try:
        process_entry.dsc_uuid = catalog.uuids[process_entry.catalog_dsc_index]
      except IndexError:
        pass
      process_entry.items = {}
      logger.debug('Process Entry data: PID {0:d} // EUID {1:d}'.format(
          process_entry.pid, process_entry.euid))
      for subsystem in process_entry.subsystems:
        offset = 0
        subsystem_string = None
        category_string = None
        for string in catalog.sub_system_strings:
          if subsystem_string is None:
            if offset >= subsystem.subsystem_offset:
              subsystem_string = string
          if category_string is None:
            if offset >= subsystem.category_offset:
              category_string = string
          offset += len(string) + 1
        process_entry.items[subsystem.identifier] = (subsystem_string,
                                                     category_string)
        logger.debug(
            'Process Entry coalesce: Subsystem {0:s} // Category {1:s}'.format(
                subsystem_string, category_string))
      catalog.process_entries.append(process_entry)
      offset_bytes += new_bytes

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

    chunk_header, _ = self._ReadStructureFromFileObject(file_object,
                                                        file_offset,
                                                        data_type_map)

    return chunk_header

  def _ReadChunkSet(self, parser_mediator, file_object, file_offset,
                    chunk_header, chunkset_index):
    """Reads a chunk set.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the chunk set data relative to the start of
        the file.
      chunk_header (tracev3_chunk_header): the chunk header of the chunk set.
      chunkset_index (int): What number chunk this is in the catalog.

    Raises:
      ParseError: if the chunk header cannot be read.
    """
    if self.catalog.subchunks[
        chunkset_index].compression_algorithm != self._CATALOG_LZ4_COMPRESSION:
      logger.error('Unknown compression algorithm : {0:s}'.format(
          self.catalog.compression_algorithm))
      return

    chunk_data = file_object.read(chunk_header.chunk_data_size)

    data_type_map = self._GetDataTypeMap('tracev3_lz4_block_header')

    lz4_block_header, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)
    logger.debug(
        'Read LZ4 block: Compressed size {0:d} // Uncompressed size {1:d}'
        .format(lz4_block_header.compressed_data_size,
                lz4_block_header.uncompressed_data_size))

    end_of_compressed_data_offset = 12 + lz4_block_header.compressed_data_size

    if lz4_block_header.signature == b'bv41':
      uncompressed_data = lz4.block.decompress(
          chunk_data[12:end_of_compressed_data_offset],
          uncompressed_size=lz4_block_header.uncompressed_data_size)

    elif lz4_block_header.signature == b'bv4-':
      logger.debug('It was already uncompressed!')
      uncompressed_data = chunk_data[12:end_of_compressed_data_offset]

    else:
      logger.error('Unsupported start of compressed data marker')
      return

    end_of_compressed_data_identifier = chunk_data[
        end_of_compressed_data_offset:end_of_compressed_data_offset + 4]

    if end_of_compressed_data_identifier != b'bv4$':
      logger.error('Unsupported end of compressed data marker')
      return

    data_type_map = self._GetDataTypeMap('tracev3_chunk_header')

    data_offset = 0
    while data_offset < lz4_block_header.uncompressed_data_size:
      chunkset_chunk_header = self._ReadStructureFromByteStream(
          uncompressed_data[data_offset:], data_offset, data_type_map)
      data_offset += 16
      logger.debug('Processing a chunk: Tag {0:d} // Size {1:d}'.format(
          chunkset_chunk_header.chunk_tag,
          chunkset_chunk_header.chunk_data_size))

      data_end_offset = data_offset + chunkset_chunk_header.chunk_data_size
      chunkset_chunk_data = uncompressed_data[data_offset:data_end_offset]

      if chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_FIREHOSE:
        logger.debug('Processing a Firehose Chunk (0x6001)')
        self._ReadFirehoseChunkData(parser_mediator, chunkset_chunk_data,
          data_offset)
      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_OVERSIZE:
        logger.debug('Processing an Oversize Chunk (0x6002)')
        oversize_parser = oversize.OversizeParser()
        self.oversize_data.append(
            oversize_parser.ParseOversizeChunkData(
              self, chunkset_chunk_data, data_offset))
      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_STATEDUMP:
        logger.debug('Processing an Statedump Chunk (0x6003)')
        statedump_parser = statedump.StatedumpParser()
        statedump_parser.ReadStatedumpChunkData(self, parser_mediator,
          chunkset_chunk_data, data_offset)
      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_SIMPLEDUMP:
        logger.debug('Processing an Simpledump Chunk (0x6004)')
        simpledump_parser = simpledump.SimpledumpParser()
        simpledump_parser.ReadSimpledumpChunkData(self, parser_mediator,
          chunkset_chunk_data, data_offset)
      else:
        logger.error('Unsupported Chunk Type: {0:d}'.format(
            chunkset_chunk_header.chunk_tag))
        return

      data_offset = data_end_offset

      # Not actually an alignment but \x00 padding
      count = 0
      new_data_offset = data_offset
      try:
        while (uncompressed_data[new_data_offset]) == 0:
          new_data_offset += 1
          count += 1
      except IndexError:
        pass

      data_offset = new_data_offset

  def ExtractAltUUID(self, uuid):
    """Extracts the requested alternate UUID file.

    Args:
      uuid (str): Requested UUID.

    Returns:
      UUIDText object or None.

    Raises:
      ParseError: if the requested UUID file was not found.
    """
    uuid_file = [f for f in self.catalog_files if f.uuid == uuid.hex.upper()]
    if len(uuid_file) != 1:
      logger.error('Couldn\'t find UUID file for {0:s}'.format(
          uuid.hex))
      return None
    return uuid_file[0]

  def ExtractAbsoluteStrings(self, original_offset, uuid_file_index, proc_info,
                             message_string_reference):
    """Extracts the absolute strings from the UUID file.

    Args:
      message_string_reference (int): Offset into file of message string
      original_offset (int): Original offset into file
      proc_info (tracev3_catalog_process_information_entry): Process Info entry
      uuid_file_index (int): Which UUID file to extract from

    Returns:
      A uuid_file or a string.

    Raises:
      ParseError: if the data cannot be parsed.
    """
    logger.debug('Extracting absolute strings from UUID file')
    if original_offset & 0x80000000:
      return '%s'

    absolute_uuids = [
        x for x in proc_info.uuids if x.absolute_ref == uuid_file_index and
        message_string_reference >= x.absolute_offset and
        message_string_reference - x.absolute_offset < x.size
    ]
    if len(absolute_uuids) != 1:
      return '<compose failure [missing precomposed log]>'
    uuid_file = self.catalog.files[absolute_uuids[0].catalog_uuid_index]
    return uuid_file

  def ExtractFormatStrings(self, offset, uuid_file):
    """Extracts a format string from a UUID file.

    Args:
      offset (int): The offset into the file to grab the string.
      uuid_file (UUIDText): The UUID file to search.

    Returns:
      str: The format string.
    """
    logger.debug('Extracting format string from UUID file')
    return uuid_file.ReadFormatString(offset)

  def ExtractSharedStrings(self, original_offset, extra_offset, dsc_file):
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

  def ReadItems(self, data_meta, data, offset):
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
      if data_item.item_type in constants.FIREHOSE_ITEM_NUMBER_TYPES:
        log_data.append(
            (data_item.item_type, data_item.item_size, data_item.item))
        index += 1
      elif (
          data_item.item_type
          in constants.FIREHOSE_ITEM_PRIVATE_STRING_TYPES
          + constants.FIREHOSE_ITEM_STRING_TYPES
          + [constants.FIREHOSE_ITEM_STRING_PRIVATE]
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
      elif data_item.item_type in constants.FIREHOSE_ITEM_PRECISION_TYPES:
        pass
      elif data_item.item_type == constants.FIREHOSE_ITEM_SENSITIVE:
        log_data.append(
            (data_item.item_type, data_item.item_size, data_item.item))
        index += 1
      else:
        raise errors.ParseError(
          'Unsupported data type: {}'.format(data_item.data_type))
    return (log_data, deferred_data_items, offset)

  def _ParseTracepointData(self, parser_mediator, tracepoint, proc_info, time,
                           private_strings):
    """Parses a log line"""

    logger.debug('Parsing log line')
    log_type = constants.LOG_TYPES.get(tracepoint.log_type, 'Default')
    if (
        tracepoint.log_activity_type
        == constants.FIREHOSE_LOG_ACTIVITY_TYPE_NONACTIVITY
    ):
      if log_type == 0x80:
        logger.error('Non Activity Signpost not supported')
        return
      nap = nonactivity.NonactivityParser()
      nap.ParseNonActivity(self, parser_mediator, tracepoint, proc_info, time,
          private_strings)
    elif (
        tracepoint.log_activity_type
        == constants.FIREHOSE_LOG_ACTIVITY_TYPE_SIGNPOST
    ):
      spp = signpost.SignpostParser()
      spp.ParseSignpost(self, parser_mediator, tracepoint, proc_info, time,
                          private_strings)
    elif (
        tracepoint.log_activity_type
        == constants.FIREHOSE_LOG_ACTIVITY_TYPE_ACTIVITY
    ):
      ap = activity.ActivityParser()
      ap.ParseActivity(self, parser_mediator, tracepoint, proc_info, time)
    elif (
        tracepoint.log_activity_type
        == constants.FIREHOSE_LOG_ACTIVITY_TYPE_LOSS
    ):
      # This is Loss
      lp = loss.LossParser()
      lp.ParseLoss(self, parser_mediator, tracepoint, proc_info, time)
    elif (
        tracepoint.log_activity_type
        == constants.FIREHOSE_LOG_ACTIVITY_TYPE_TRACE
    ):
      tp = trace.TraceParser()
      tp.ParceTrace(self, parser_mediator, tracepoint, proc_info, time)
    elif tracepoint.log_activity_type == 0x0:
      logger.warning("Remnant/Garbage data")
    else:
      logger.error('Unsupported log activity type: {}'.format(
          tracepoint.log_activity_type))

  def _ReadFirehoseChunkData(self, parser_mediator, chunk_data, data_offset):
    """Reads firehose chunk data.

    Args:
      chunk_data (bytes): firehose chunk data.
      data_offset (int): offset of the firehose chunk relative to the start of
        the chunk set.

    Raises:
      ParseError: if the firehose chunk cannot be read.
    """
    logger.debug('Reading Firehose')
    data_type_map = self._GetDataTypeMap('tracev3_firehose_header')

    firehose_header = self._ReadStructureFromByteStream(chunk_data, data_offset,
                                                        data_type_map)

    logger.debug(
        'Firehose Header data: ProcID 1 {0:d} // ProcID 2 {1:d} // TTL {2:d} //'
        ' CT {3:d}'.format(
            firehose_header.first_number_proc_id,
            firehose_header.second_number_proc_id,
            firehose_header.ttl,
            firehose_header.base_continuous_time,
        )
    )

    proc_id = firehose_header.second_number_proc_id | (
        firehose_header.first_number_proc_id << 32)
    proc_info = [
        c for c in self.catalog.process_entries
        if c.second_number_proc_id | (c.first_number_proc_id << 32) == proc_id
    ]
    if len(proc_info) == 0:
      logger.error('Could not find Process Info block for ID: %d', proc_id)
      return
    else:
      proc_info = proc_info[0]

    private_strings = None
    private_data_len = 0
    if firehose_header.private_data_virtual_offset != 4096:
      logger.debug('Parsing Private Firehose Data')
      private_data_len = 4096 - firehose_header.private_data_virtual_offset
      private_strings = (firehose_header.private_data_virtual_offset,
                         chunk_data[-private_data_len:])

    logger.debug(
        'Firehose Header Timestamp: %s',
        aul_time.TimestampFromContTime(self.boot_uuid_ts.sync_records,
                                       firehose_header.base_continuous_time))

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
        wt = self.boot_uuid_ts.boot_time
      ts = aul_time.FindClosestTimesyncItemInList(
          self.boot_uuid_ts.sync_records, ct, wt == 0)
      if ts:
        wt = ts.wall_time
        kct = ts.kernel_continuous_timestamp
      time = (
          wt
          + (ct * self.boot_uuid_ts.adjustment)
          - (kct * self.boot_uuid_ts.adjustment)
      )
      self._ParseTracepointData(parser_mediator, firehose_tracepoint, proc_info,
                                time, private_strings)

      chunk_data_offset += 24 + firehose_tracepoint.data_size
      _, alignment = divmod(chunk_data_offset, 8)
      if alignment > 0:
        alignment = 8 - alignment

      chunk_data_offset += alignment

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a timezone information file-like object.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
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
        logger.debug('Processing a HEADER (0x1000)')
        self._ReadHeader(file_object, file_offset)
      elif chunk_header.chunk_tag == self._CHUNK_TAG_CATALOG:
        logger.debug('Processing a CATALOG (0x600B)')
        self.catalog = self._ReadCatalog(parser_mediator, file_object,
                                         file_offset)
        chunkset_index = 0
      elif chunk_header.chunk_tag == self._CHUNK_TAG_CHUNKSET:
        logger.debug('Processing a CHUNKSET (0x600D)')
        self._ReadChunkSet(parser_mediator, file_object, file_offset,
                           chunk_header, chunkset_index)
        chunkset_index += 1
      else:
        logger.error(
          'UNKNOWN CHUNK TAG: {0:d}'.format(chunk_header.chunk_tag))

      file_offset += chunk_header.chunk_data_size

      _, alignment = divmod(file_offset, 8)
      if alignment > 0:
        alignment = 8 - alignment

      file_offset += alignment
