# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) Oversize chunk parser."""
import os

from plaso.lib import dtfabric_helper

from plaso.lib import errors

from plaso.lib.aul import constants

from plaso.parsers import logger


class OversizeData():
  """Apple Unified Logging (AUL) Oversize Data file.

  Attributes:
    data_ref_index (str): Index of the data reference.
    first_proc_id (str): First process ID
    second_proc_id (str): Second process ID
    strings (List[str]): List of the oversized strings.
  """
  def __init__(self, first_proc_id, second_proc_id, data_ref_index):
    super(OversizeData, self).__init__()
    self.data_ref_index = data_ref_index
    self.first_proc_id = first_proc_id
    self.second_proc_id = second_proc_id
    self.strings = []

class OversizeParser(dtfabric_helper.DtFabricHelper):
  """Oversized data chunk parser"""

  _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), 'oversize.yaml')

  def ParseOversizeChunkData(self, tracev3_parser, chunk_data, data_offset):
    """Processes the Oversized data chunk.

    Args:
      tracev3_parser (TraceV3FileParser): TraceV3 File Parser.
      chunk_data (bytes): oversize chunk data.
      data_offset (int): offset of the oversize chunk relative to the start
        of the chunk set.

    Raises:
      ParseError: if the oversize chunk cannot be parsed.
    """
    logger.debug("Reading Oversize")
    data_type_map = self._GetDataTypeMap('tracev3_oversize')

    oversize = self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map)
    logger.debug(
      'Firehose Header data: ProcID 1 {0:d} // ProcID 2 {1:d} // '
      'Ref Index {2:d} // CT {3:d} (Oversize)'
      .format(oversize.first_number_proc_id, oversize.second_number_proc_id,
              oversize.data_ref_index, oversize.continuous_time))

    offset = 0
    data_meta = self._ReadStructureFromByteStream(
      oversize.data,
      offset,
      self._GetDataTypeMap('tracev3_firehose_tracepoint_data'))
    offset += 2

    logger.debug(
      "After activity data: Unknown {0:d} // Number of Items {1:d}".format(
        data_meta.unknown1, data_meta.num_items))
    (oversize_strings, deferred_data_items,
      offset) = tracev3_parser.ReadItems(
        data_meta, oversize.data, offset)

    # Check for backtrace
    if oversize.data[offset:offset+3] == [0x01, 0x00, 0x18]:
      raise errors.ParseError("Backtrace !?")

    private_items = []
    rolling_offset = offset
    for index, item in enumerate(deferred_data_items):
      if item[2] == 0:
        oversize_strings.append((item[0], item[2], ""))
        continue
      if item[0] in constants.FIREHOSE_ITEM_PRIVATE_STRING_TYPES:
        logger.debug("Private Oversize")
        private_items.append((item, index))
        oversize_strings.insert(index, (item[0], item[2], '<private>'))
        continue
      oversize_strings.append(
          (item[0], item[2],
           self._ReadStructureFromByteStream(
            oversize.data[offset + item[1]:],
            0,
            self._GetDataTypeMap('cstring'))))
      rolling_offset += item[2]
    offset = rolling_offset
    for item, index in private_items:
      oversize_strings[index] = (item[0], item[2],
                                 self._ReadStructureFromByteStream(
                                     oversize.data[offset + item[1]:], 0,
                                     self._GetDataTypeMap('cstring')))

    oversize = OversizeData(
      oversize.first_number_proc_id,
      oversize.second_number_proc_id,
      oversize.data_ref_index)
    oversize.strings = oversize_strings
    logger.debug("Oversize Data: {0!s}".format(oversize_strings))
    return oversize
