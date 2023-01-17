# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) Activity chunk parser."""

import base64

from dfdatetime import apfs_time as dfdatetime_apfs_time

from plaso.lib.aul import constants
from plaso.lib.aul import formatter
from plaso.lib.aul import dsc

from plaso.lib import errors

from plaso.parsers import aul
from plaso.parsers import logger


class ActivityParser():
  """Activity data chunk parser"""

  _USER_ACTION_ACTIVITY_TYPE = 0x3

  def ParseActivity(self, tracev3, parser_mediator, tracepoint, proc_info,
                     time):
    """Processes an Activity chunk.

    Args:
      tracev3 (TraceV3FileParser): TraceV3 File Parser.
      parser_mediator (ParserMediator): a parser mediator.
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

    event_data = aul.AULEventData()
    event_data.boot_uuid = tracev3.header.generation_subchunk.generation_subchunk_data.boot_uuid.hex.upper()

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
    except AttributeError:
      uuid_file = None

    uint32_data_type_map = tracev3.GetDataTypeMap('uint32')
    uint64_data_type_map = tracev3.GetDataTypeMap('uint64')

    if tracepoint.log_type != self._USER_ACTION_ACTIVITY_TYPE:
      activity_id = tracev3.ReadStructureFromByteStream(data, offset,
                                                      uint32_data_type_map)
      offset += 4
      sentinel = tracev3.ReadStructureFromByteStream(data[offset:], offset,
                                                   uint32_data_type_map)
      offset += 4

    if flags & constants.UNIQUE_PID:
      unique_pid = tracev3.ReadStructureFromByteStream(data[offset:], offset,
                                                     uint64_data_type_map)
      offset += 8
      logger.debug('Signpost has unique_pid: {0:d}'.format(unique_pid))

    if flags & constants.CURRENT_AID:
      logger.debug('Activity has current_aid')
      activity_id = tracev3.ReadStructureFromByteStream(data, offset,
                                                      uint32_data_type_map)
      offset += 4
      sentinel = tracev3.ReadStructureFromByteStream(data[offset:], offset,
                                                   uint32_data_type_map)
      offset += 4

    if flags & constants.HAS_SUBSYSTEM:
      logger.debug('Activity has has_other_current_aid')
      activity_id = tracev3.ReadStructureFromByteStream(data, offset,
                                                      uint32_data_type_map)
      offset += 4
      sentinel = tracev3.ReadStructureFromByteStream(data[offset:], offset,
                                                   uint32_data_type_map)
      offset += 4

    message_string_reference = tracev3.ReadStructureFromByteStream(
        data[offset:], offset, uint32_data_type_map)
    offset += 4
    logger.debug('Unknown PCID: {0:d}'.format(message_string_reference))

    ffh = formatter.FormatterFlagsHelper()
    formatter_flags = ffh.FormatFlags(tracev3, flags, data, offset)
    offset = formatter_flags.offset

    if flags & constants.PRIVATE_STRING_RANGE:
      raise errors.ParseError('Activity with Private String Range')

    # If there's data...
    if tracepoint.data_size - offset >= 6:
      data_meta = tracev3.ReadStructureFromByteStream(
          data[offset:], offset,
          tracev3.GetDataTypeMap('tracev3_firehose_tracepoint_data'))
      offset += 2

      logger.debug(
          'After activity data: Unknown {0:d} // Number of Items {1:d}'.format(
              data_meta.unknown1, data_meta.num_items))
      (log_data, deferred_data_items,
       offset) = tracev3.ReadItems(data_meta, data, offset)

      if flags & constants.HAS_CONTEXT_DATA != 0:
        raise errors.ParseError('Backtrace data in Activity log chunk')

      if flags & constants.HAS_DATA_REF:
        raise errors.ParseError('Activity log chunk with Data Ref')

      #TODO(fryy): Functionise this
      for item in deferred_data_items:
        if item[2] == 0:
          result = ''
        elif item[0] in constants.FIREHOSE_ITEM_PRIVATE_STRING_TYPES:
          if not private_string:
            raise errors.ParseError('Trying to read from empty Private String')
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

    if formatter_flags.shared_cache or formatter_flags.large_shared_cache != 0:
      extra_offset_value_result = tracepoint.format_string_location
      if formatter_flags.large_offset_data != 0:
        if formatter_flags.large_offset_data != formatter_flags.large_shared_cache / 2 and not formatter_flags.shared_cache:
          # Recovery ?
          formatter_flags.large_offset_data = int(formatter_flags.large_shared_cache / 2)
          extra_offset_value = '{0:X}{1:08x}'.format(formatter_flags.large_offset_data, tracepoint.format_string_location)
        elif formatter_flags.shared_cache:
          formatter_flags.large_offset_data = 8
          extra_offset_value = '{0:X}{1:07x}'.format(formatter_flags.large_offset_data, tracepoint.format_string_location)
        else:
          extra_offset_value = '{0:X}{1:08x}'.format(formatter_flags.large_offset_data, tracepoint.format_string_location)
        extra_offset_value_result = int(extra_offset_value, 16)
      (fmt, dsc_range) = tracev3.ExtractSharedStrings(
          tracepoint.format_string_location, extra_offset_value_result,
          dsc_file)
    else:
      if formatter_flags.absolute:
        raise errors.ParseError(
            'Absolute Activity not supported - signpost.rs:224')
      elif formatter_flags.uuid_relative:
        uuid_file = tracev3.ExtractAltUUID(formatter_flags.uuid_relative)
        fmt = uuid_file.ReadFormatString(tracepoint.format_string_location)
      else:
        fmt = tracev3.ExtractFormatStrings(tracepoint.format_string_location,
                                           uuid_file)
    if not fmt and not log_data:
      return

    event_data.level = constants.LOG_TYPES.get(tracepoint.log_type, 'Default')

    # Info is 'Create' when it's an Activity
    if tracepoint.log_type == 0x1:
      event_data.level = 'Create'

    if activity_id:
      event_data.activity_id = hex(activity_id)
    event_data.thread_id = hex(tracepoint.thread_identifier)
    event_data.pid = proc_info.pid
    event_data.euid = proc_info.euid

    if dsc_range.uuid_index:
      dsc_uuid = dsc_file.uuids[dsc_range.uuid_index]
      dsc_range.path = dsc_uuid.path
      dsc_range.uuid = dsc_uuid.sender_identifier

    if dsc_range.path or uuid_file:
      event_data.library = dsc_range.path if dsc_range.path else uuid_file.library_path
    if dsc_range.uuid or uuid_file:
      event_data.library_uuid = dsc_range.uuid.hex.upper() if dsc_range.uuid else uuid_file.uuid.upper()
    event_data.message = tracev3.FormatString(fmt, log_data)

    event_data.creation_time = dfdatetime_apfs_time.APFSTime(timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)
