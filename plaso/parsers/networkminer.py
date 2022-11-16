# -*- coding: utf-8 -*-
"""Parser for NetworkMiner .fileinfos files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import dsv_parser
from plaso.parsers import manager


class NetworkMinerEventData(events.EventData):
  """NetworkMiner event Data.

  Attributes:
    destination_ip (str): Destination IP address.
    destination_port (str): Destination port number.
    file_details (string): Details about the file.
    file_md5 (string): MD5 hash of the file.
    file_path (string): File path to where it was downloaded.
    file_size (string): Size of the file.
    filename (string): Name of the file.
    source_ip (str): Originating IP address.
    source_port (str): Originating port number.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'networkminer:fileinfos:file'

  def __init__(self):
    super(NetworkMinerEventData, self).__init__(data_type=self.DATA_TYPE)
    self.destination_ip = None
    self.destination_port = None
    self.file_details = None
    self.file_md5 = None
    self.file_path = None
    self.file_size = None
    self.filename = None
    self.source_ip = None
    self.source_port = None
    self.written_time = None


class NetworkMinerParser(dsv_parser.DSVParser):
  """Parser for NetworkMiner .fileinfos files."""

  NAME = 'networkminer_fileinfo'
  DATA_FORMAT = 'NetworkMiner .fileinfos file'

  COLUMNS = (
      'source_ip', 'source_port', 'destination_ip', 'destination_port',
      'filename', 'file_path', 'file_size', 'unused', 'file_md5', 'unused2',
      'file_details', 'unused4', 'timestamp')

  _ATTRIBUTE_NAMES = frozenset([
      'destination_ip',
      'destination_port',
      'file_details',
      'file_md5',
      'filename',
      'file_path',
      'file_size',
      'source_ip',
      'source_port'])

  _MINIMUM_NUMBER_OF_COLUMNS = 13

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      row_offset (int): line number of the row.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    timestamp = row.get('timestamp', None)
    if timestamp == 'Timestamp':
      return

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(timestamp)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('invalid date time value')
      date_time = None

    event_data = NetworkMinerEventData()
    event_data.written_time = date_time

    for attribute_name in self._ATTRIBUTE_NAMES:
      setattr(event_data, attribute_name, row[attribute_name])

    parser_mediator.ProduceEventData(event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) != self._MINIMUM_NUMBER_OF_COLUMNS:
      return False

    # Check the date format
    # If it doesn't parse, then this isn't a NetworkMiner .fileinfos file.
    timestamp_value = row.get('timestamp', None)
    if timestamp_value != 'Timestamp':
      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(timestamp_value)
      except (TypeError, ValueError):
        return False

    return True


manager.ParsersManager.RegisterParser(NetworkMinerParser)
