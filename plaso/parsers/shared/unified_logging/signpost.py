# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) Signpost chunk parser."""

import base64

from dfdatetime import apfs_time as dfdatetime_apfs_time

from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib.aul import constants
from plaso.containers import unified_logging_event
from plaso.lib.aul import formatter
from plaso.parsers.shared.unified_logging import dsc
from plaso.parsers import logger


class SignpostParser(dtfabric_helper.DtFabricHelper):
  """Signpost data chunk parser"""

  def ParseSignpost(
      self, tracev3, parser_mediator, tracepoint, proc_info, time,
      private_strings):
    """Processes a Signpost chunk.

    Args:
      tracev3 (TraceV3FileParser): TraceV3 File Parser.
      parser_mediator (ParserMediator): a parser mediator.
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

    event_data = unified_logging_event.AULEventData()
    generation_subchunk = tracev3.header.generation_subchunk
    generation_subchunk_data = generation_subchunk.generation_subchunk_data
    event_data.boot_uuid = generation_subchunk_data.boot_uuid.hex.upper()
    event_data.pid = proc_info.pid
    event_data.euid = proc_info.euid

    try:
      dsc_file = tracev3.catalog.files[proc_info.catalog_dsc_index]
    except IndexError:
      dsc_file = None

    try:
      uuid_file = tracev3.catalog.files[proc_info.main_uuid_index]
      event_data.process_uuid = uuid_file.uuid
      event_data.process = uuid_file.library_path
    except IndexError:
      uuid_file = None

    uint8_data_type_map = tracev3.GetDataTypeMap('uint8')
    uint16_data_type_map = tracev3.GetDataTypeMap('uint16')
    uint32_data_type_map = tracev3.GetDataTypeMap('uint32')
    uint64_data_type_map = tracev3.GetDataTypeMap('uint64')

    if flags & constants.CURRENT_AID:
      logger.debug('Signpost has current_aid')
      activity_id = tracev3.ReadStructureFromByteStream(data, offset,
                                                      uint32_data_type_map)
      offset += 4
      sentinel = tracev3.ReadStructureFromByteStream(data[offset:], offset,
                                                   uint32_data_type_map)
      offset += 4

      # Note that activity_id and sentinel are currently unused.
      _ = activity_id
      _ = sentinel

    if flags & constants.PRIVATE_STRING_RANGE:
      logger.debug('Signpost has private_string_range (has_private_data flag)')

      private_strings_offset = tracev3.ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 2
      private_strings_size = tracev3.ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 2

    message_string_reference = tracev3.ReadStructureFromByteStream(
        data[offset:], offset, uint32_data_type_map)
    offset += 4
    logger.debug('Unknown PCID: {0:d}'.format(message_string_reference))

    ffh = formatter.FormatterFlagsHelper()
    formatter_flags = ffh.FormatFlags(tracev3, flags, data, offset)
    offset = formatter_flags.offset

    subsystem_value = ''
    if flags & constants.HAS_SUBSYSTEM:
      subsystem_value = tracev3.ReadStructureFromByteStream(
          data[offset:], offset, uint16_data_type_map)
      offset += 2
      logger.debug('Signpost has subsystem: {0:d}'.format(subsystem_value))

    signpost_id = tracev3.ReadStructureFromByteStream(data[offset:], offset,
                                                    uint64_data_type_map)
    offset += 8

    if flags & constants.HAS_TTL:
      ttl_value = tracev3.ReadStructureFromByteStream(data[offset:], offset,
                                                    uint8_data_type_map)
      offset += 1
      logger.debug('Signpost has TTL: {0:d}'.format(ttl_value))

    if flags & constants.HAS_DATA_REF:
      data_ref_id = tracev3.ReadStructureFromByteStream(data[offset:], offset,
                                                      uint16_data_type_map)
      offset += 1
      logger.debug('Signpost with data reference: {0:d}'.format(data_ref_id))

    if flags & constants.HAS_SIGNPOST_NAME:
      signpost_name = tracev3.ReadStructureFromByteStream(data[offset:], offset,
                                                        uint32_data_type_map)
      offset += 4
      if formatter_flags.large_shared_cache != 0:
        offset += 2

    if flags & constants.PRIVATE_STRING_RANGE:
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

    data_meta = tracev3.ReadStructureFromByteStream(
        data[offset:], offset,
        tracev3.GetDataTypeMap('tracev3_firehose_tracepoint_data'))
    offset += 2

    logger.debug(
        'After activity data: Unknown {0:d} // Number of Items {1:d}'.format(
            data_meta.unknown1, data_meta.num_items))
    try:
      (log_data, deferred_data_items,
      offset) = tracev3.ReadItems(data_meta, data, offset)
    except errors.ParseError as exception:
      logger.error('Unable to parse data items: {0!s}'.format(exception))
      return

    if flags & constants.HAS_CONTEXT_DATA != 0:
      logger.error('Backtrace data in Signpost log chunk')
      return

    for item in deferred_data_items:
      if item[2] == 0:
        result = ''
      elif item[0] in constants.FIREHOSE_ITEM_PRIVATE_STRING_TYPES:
        if not private_string:
          logger.error('Trying to read from empty Private String')
          return
        try:
          result = tracev3.ReadStructureFromByteStream(
              private_string[item[1]:], 0, tracev3.GetDataTypeMap('cstring'))
          logger.debug('End result: {0:s}'.format(result))
        except errors.ParseError:
          result = ''  # Private
      else:
        if item[0] in constants.FIREHOSE_ITEM_STRING_ARBITRARY_DATA_TYPES:
          result = data[offset + item[1]:offset + item[1] + item[2]]
        elif item[0] == constants.FIREHOSE_ITEM_STRING_BASE64_TYPE:
          result = base64.encodebytes(data[offset + item[1]:offset + item[1] +
                                           item[2]]).strip()
        else:
          result = tracev3.ReadStructureFromByteStream(
              data[offset + item[1]:], 0, tracev3.GetDataTypeMap('cstring'))
          logger.debug('End result: {0:s}'.format(result))
      log_data.insert(item[3], (item[0], item[2], result))

    found = False
    dsc_range = dsc.DSCRange()

    if data_ref_id != 0:
      for oversize_data in tracev3.oversize_data:
        if (
            oversize_data.first_proc_id == proc_info.first_number_proc_id
            and oversize_data.second_proc_id == proc_info.second_number_proc_id
            and oversize_data.data_ref_index == data_ref_id
        ):
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
      (fmt, dsc_range) = tracev3.ExtractSharedStrings(
          tracepoint.format_string_location, extra_offset_value_result,
          dsc_file)
    else:
      if formatter_flags.absolute:
        uuid_file = tracev3.ExtractAbsoluteStrings(
            tracepoint.format_string_location, formatter_flags.uuid_file_index,
            proc_info, message_string_reference)
        if uuid_file != '%s':
          fmt = uuid_file.ReadFormatString(tracepoint.format_string_location)
        else:
          fmt = uuid_file
          uuid_file = None
      elif formatter_flags.uuid_relative:
        uuid_file = tracev3.ExtractAltUUID(formatter_flags.uuid_relative)
        fmt = uuid_file.ReadFormatString(tracepoint.format_string_location)
      else:
        fmt = tracev3.ExtractFormatStrings(tracepoint.format_string_location,
                                           uuid_file)

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
    event_data.thread_id = hex(tracepoint.thread_identifier)
    event_data.subsystem = (proc_info.items.get(subsystem_value, ('', '')))[0]
    event_data.category = (proc_info.items.get(subsystem_value, ('', '')))[1]

    if ttl_value:
      event_data.ttl = ttl_value

    event_data.body = 'Signpost ID: {} - Signpost Name: {} - {}'.format(
        hex(signpost_id).upper()[2:],
        hex(signpost_name).upper()[2:],
        tracev3.FormatString(fmt, log_data))

    event_data.creation_time = dfdatetime_apfs_time.APFSTime(
        timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)
