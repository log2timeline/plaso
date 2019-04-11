# -*- coding: utf-8 -*-
"""Parser for PL/SQL Developer Recall files."""

from __future__ import unicode_literals

from dfdatetime import delphi_date_time as dfdatetime_delphi_date_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import dtfabric_parser
from plaso.parsers import manager


class PlsRecallEventData(events.EventData):
  """PL/SQL Recall event data.

  Attributes:
    database_name (str): name of the database.
    query (str): PL/SQL query.
    sequence_number (int): sequence number.
    username (str): username used to query.
  """

  DATA_TYPE = 'PLSRecall:event'

  def __init__(self):
    """Initializes event data."""
    super(PlsRecallEventData, self).__init__(data_type=self.DATA_TYPE)
    self.database_name = None
    self.query = None
    self.sequence_number = None
    self.username = None


class PlsRecallParser(dtfabric_parser.DtFabricBaseParser):
  """Parse PL/SQL Recall files.

  This parser is based on the Delphi definition of the data type:

    TRecallRecord = packed record
      Sequence: Integer;
      TimeStamp: TDateTime;
      Username: array[0..30] of Char;
      Database: array[0..80] of Char;
      Text: array[0..4000] of Char;
    end;

    Delphi TDateTime is a little-endian 64-bit floating-point value without
    time zone information.
  """

  NAME = 'pls_recall'
  DESCRIPTION = 'Parser for PL/SQL Recall files.'

  _DEFINITION_FILE = 'pls_recall.yaml'

  _PLS_KEYWORD = frozenset([
      'begin', 'commit', 'create', 'declare', 'drop', 'end', 'exception',
      'execute', 'insert', 'replace', 'rollback', 'select', 'set',
      'update'])

  # 6 * 365 * 24 * 60 * 60 * 1000000.
  _SIX_YEARS_IN_MICRO_SECONDS = 189216000000000

  def _VerifyRecord(self, pls_record):
    """Verifies a PLS Recall record.

    Args:
      pls_record (pls_recall_record): a PLS Recall record to verify.

    Returns:
      bool: True if this is a valid PLS Recall record, False otherwise.
    """
    # Verify that the timestamp is no more than six years into the future.
    # Six years is an arbitrary time length just to evaluate the timestamp
    # against some value. There is no guarantee that this will catch everything.
    # TODO: Add a check for similarly valid value back in time. Maybe if it the
    # timestamp is before 1980 we are pretty sure it is invalid?
    # TODO: This is a very flaky assumption. Find a better one.
    future_timestamp = (
        timelib.Timestamp.GetNow() + self._SIX_YEARS_IN_MICRO_SECONDS)

    if pls_record.last_written_time > future_timestamp:
      return False

    # Take the first word from the query field and attempt to match that against
    # known query keywords.
    first_word, _, _ = pls_record.query.partition(' ')

    if first_word.lower() not in self._PLS_KEYWORD:
      return False

    return True

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a PLSRecall.dat file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_offset = 0
    file_size = file_object.get_size()
    record_map = self._GetDataTypeMap('pls_recall_record')

    while file_offset < file_size:
      try:
        pls_record, record_data_size = self._ReadStructureFromFileObject(
            file_object, file_offset, record_map)
      except (ValueError, errors.ParseError) as exception:
        if file_offset == 0:
          raise errors.UnableToParseFile('Unable to parse first record.')

        parser_mediator.ProduceExtractionWarning((
            'unable to parse record at offset: 0x{0:08x} with error: '
            '{1!s}').format(file_offset, exception))
        break

      if file_offset == 0 and not self._VerifyRecord(pls_record):
        raise errors.UnableToParseFile('Verification of first record failed.')

      event_data = PlsRecallEventData()
      event_data.database_name = pls_record.database_name.rstrip('\x00')
      event_data.sequence_number = pls_record.sequence_number
      event_data.offset = file_offset
      event_data.query = pls_record.query.rstrip('\x00')
      event_data.username = pls_record.username.rstrip('\x00')

      date_time = dfdatetime_delphi_date_time.DelphiDateTime(
          timestamp=pls_record.last_written_time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      file_offset += record_data_size


manager.ParsersManager.RegisterParser(PlsRecallParser)
