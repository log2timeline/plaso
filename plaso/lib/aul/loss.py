# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) loss activity parser."""
import csv
import os

from dfdatetime import apfs_time as dfdatetime_apfs_time

from plaso.lib import dtfabric_helper

from plaso.parsers import aul
from plaso.parsers import logger


class LossParser(dtfabric_helper.DtFabricHelper):
  """Loss data chunk parser"""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'loss.yaml')

  def ParseLoss(self, tracev3, parser_mediator, tracepoint, proc_info, time):
    """Processes a Loss chunk.

    Args:
      tracev3 (TraceV3FileParser): TraceV3 File Parser.
      parser_mediator (ParserMediator): a parser mediator.
      tracepoint (tracev3_firehose_tracepoint): Firehose tracepoint chunk.
      proc_info (tracev3_catalog_process_information_entry): Process Info entry.
      time (int): Log timestamp.

    Raises:
      ParseError: if the non-activity chunk cannot be parsed.
    """
    logger.debug("Reading Loss")
    data_type_map = self._GetDataTypeMap('tracev3_firehose_loss')

    loss_structure = self._ReadStructureFromByteStream(
        tracepoint.data, 0, data_type_map)
    logger.debug("Loss data: Start Time {0:d} // End time {1:d} "
      "// Count {2:d}".format(
      loss_structure.start_time, loss_structure.end_time, loss_structure.count
    ))

    event_data = aul.AULEventData()
    event_data.boot_uuid = tracev3.header.generation_subchunk.generation_subchunk_data.boot_uuid.hex
    event_data.pid = proc_info.pid
    event_data.euid = proc_info.euid
    event_data.level = "Loss"
    event_data.thread_id = hex(tracepoint.thread_identifier)
    event_data.message = "Lost {0:d} log messages".format(loss_structure.count)

    with open("/tmp/fryoutput.csv", "a") as f:
      csv.writer(f).writerow([
          dfdatetime_apfs_time.APFSTime(timestamp=time).CopyToDateTimeString(),
          event_data.level, event_data.message
      ])

    event_data.creation_time = dfdatetime_apfs_time.APFSTime(timestamp=time)
    parser_mediator.ProduceEventData(event_data)
