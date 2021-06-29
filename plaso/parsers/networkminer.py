# -*- coding: utf-8 -*-
"""Parser for NetworkMiner .fileinfos files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
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


class NetworkMinerParser(dsv_parser.DSVParser):
  """Parser for NetworkMiner .fileinfos files."""

  NAME = 'networkminer_fileinfo'
  DATA_FORMAT = 'NetworkMiner .fileinfos file'

  COLUMNS = (
      'source_ip', 'source_port', 'destination_ip', 'destination_port',
      'filename', 'file_path', 'file_size', 'unused', 'file_md5', 'unused2',
      'file_details', 'unused4', 'timestamp')

  MIN_COLUMNS = 13

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): line number of the row.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    event_data = NetworkMinerEventData()

    if row.get('timestamp', None) != 'Timestamp':
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      for field in (
          'source_ip', 'source_port', 'destination_ip',
          'destination_port', 'filename', 'file_path', 'file_size', 'file_md5',
          'file_details'):
        setattr(event_data, field, row[field])

      try:
        timestamp = row.get('timestamp', None)
        date_time.CopyFromStringISO8601(timestamp)

      except ValueError:
        parser_mediator.ProduceExtractionWarning('invalid date time value')
        return

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) != self.MIN_COLUMNS:
      return False

    # Check the date format
    # If it doesn't parse, then this isn't a NetworkMiner .fileinfos file.
    timestamp_value = row.get('timestamp', None)
    if timestamp_value != 'Timestamp':
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      try:
        date_time.CopyFromStringISO8601(timestamp_value)
      except ValueError:
        return False

    return True


manager.ParsersManager.RegisterParser(NetworkMinerParser)
