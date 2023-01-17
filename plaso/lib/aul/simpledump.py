# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) Simpledump chunk parser."""
import csv
import os

from dfdatetime import apfs_time as dfdatetime_apfs_time

from plaso.lib.aul import time as aul_time

from plaso.lib import dtfabric_helper

from plaso.parsers import aul
from plaso.parsers import logger

class SimpledumpParser(dtfabric_helper.DtFabricHelper):
  """SimpledumpParser data chunk parser"""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'simpledump.yaml')

  def ReadSimpledumpChunkData(self, tracev3, parser_mediator, chunk_data,
                              data_offset):
    """Parses the Simpledump Chunk and adds a DateTimeEvent.

    Args:
      tracev3 (TraceV3FileParser): TraceV3 File Parser.
      parser_mediator (ParserMediator): a parser mediator.
      chunk_data (bytes): oversize chunk data.
      data_offset (int): offset of the oversize chunk relative to the start
        of the chunk set.

    Raises:
      ParseError: if the records cannot be parsed.
    """
    logger.debug("Reading Statedump")
    data_type_map = self._GetDataTypeMap('tracev3_simpledump')

    simpledump_structure = self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map)
    logger.debug(
        ("Simpledump data: ProcID 1 {0:d} // ProcID 2 {1:d} // "
        "CT {2:d} // ThreadID {3:d}")
        .format(simpledump_structure.first_number_proc_id,
                simpledump_structure.second_number_proc_id,
                simpledump_structure.continuous_time,
                simpledump_structure.thread_id))
    logger.debug('Substring: {0:s} // Message string: {1:s}'.format(
        simpledump_structure.subsystem_string,
        simpledump_structure.message_string
    ))

    event_data = aul.AULEventData()
    event_data.boot_uuid = tracev3.header.generation_subchunk.generation_subchunk_data.boot_uuid.hex.upper()
    event_data.level = "Simpledump"

    event_data.thread_id = hex(simpledump_structure.thread_id)
    event_data.pid = simpledump_structure.first_number_proc_id
    event_data.subsystem = simpledump_structure.subsystem_string
    event_data.library_uuid = simpledump_structure.sender_uuid.hex.upper()
    event_data.process_uuid = simpledump_structure.dsc_uuid.hex
    event_data.message = simpledump_structure.message_string
    logger.debug("Log line: {0!s}".format(event_data.message))

    ct = simpledump_structure.continuous_time
    ts = aul_time.FindClosestTimesyncItemInList(
      tracev3.boot_uuid_ts.sync_records, ct, True)
    wt = 0
    kct = 0
    if ts:
      wt = ts.wall_time
      kct = ts.kernel_continuous_timestamp
    time = wt + (ct * tracev3.boot_uuid_ts.adjustment) - (kct * tracev3.boot_uuid_ts.adjustment)

    with open('/tmp/fryoutput.csv', 'a') as f:
      csv.writer(f).writerow([
          dfdatetime_apfs_time.APFSTime(
            timestamp=int(time)).CopyToDateTimeString(), event_data.level,
          event_data.message
      ])

    event_data.creation_time = dfdatetime_apfs_time.APFSTime(timestamp=int(time))
    parser_mediator.ProduceEventData(event_data)