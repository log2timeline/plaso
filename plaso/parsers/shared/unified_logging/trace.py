# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) Trace chunk parser."""

import os

from dfdatetime import apfs_time as dfdatetime_apfs_time

from plaso.containers import unified_logging_event
from plaso.lib import dtfabric_helper
from plaso.parsers import logger


class TraceParser(dtfabric_helper.DtFabricHelper):
  """TraceParser data chunk parser"""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'trace.yaml')

  def ParceTrace(self, tracev3, parser_mediator, tracepoint, proc_info,
                         time):
    """Parses a Trace chunk.

    Args:
      tracev3 (TraceV3FileParser): TraceV3 File Parser.
      parser_mediator (ParserMediator): a parser mediator.
      tracepoint (tracev3_firehose_tracepoint): Firehose tracepoint chunk.
      proc_info (tracev3_catalog_process_information_entry): Process Info entry.
      time (int): Log timestamp.

    Raises:
      ParseError: if the records cannot be parsed.
    """
    logger.debug("Reading Trace")
    data = tracepoint.data

    event_data = unified_logging_event.AULEventData()
    generation_subchunk = tracev3.header.generation_subchunk
    generation_subchunk_data = generation_subchunk.generation_subchunk_data
    event_data.boot_uuid = generation_subchunk_data.boot_uuid.hex.upper()

    try:
      uuid_file = tracev3.catalog.files[proc_info.main_uuid_index]
      event_data.process_uuid = uuid_file.uuid
      event_data.process = uuid_file.library_path
    except IndexError:
      uuid_file = None
    except AttributeError:
      uuid_file = None

    offset = 0

    message_string_reference = tracev3.ReadStructureFromByteStream(
        data[offset:], offset, self._GetDataTypeMap('uint32'))
    logger.debug('Unknown PCID: {0:d}'.format(message_string_reference))
    offset += 4

    item_data = b''
    if len(data[offset:]) < 4:
      logger.warning("Insufficent trace data")
    else:
      item_data = data[offset:offset+2]
      offset += 2

    fmt = tracev3.ExtractFormatStrings(tracepoint.format_string_location,
                                           uuid_file)
    logger.debug("Format string: {0:s}".format(fmt))

    if fmt:
      event_data.body = tracev3.FormatString(
          fmt, [(0, len(item_data), item_data)])

    event_data.thread_id = hex(tracepoint.thread_identifier)
    event_data.pid = proc_info.pid
    event_data.euid = proc_info.euid
    if uuid_file:
      event_data.library = uuid_file.library_path
    if uuid_file:
      event_data.library_uuid = uuid_file.uuid.upper()

    event_data.creation_time = dfdatetime_apfs_time.APFSTime(
        timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)
