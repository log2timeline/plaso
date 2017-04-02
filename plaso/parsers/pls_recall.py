# -*- coding: utf-8 -*-
"""Parser for PL/SQL Developer Recall files."""

import os

import construct

from dfdatetime import delphi_date_time as dfdatetime_delphi_date_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.lib import utils
from plaso.parsers import interface
from plaso.parsers import manager


class PlsRecallEventData(events.EventData):
  """PL/SQL Recall event data.

  Attributes:
    database_name (str): name of the database.
    query (str): PL/SQL query.
    sequence_number (int): sequence number.
    username (str): username used to query.
  """

  DATA_TYPE = u'PLSRecall:event'

  def __init__(self):
    """Initializes event data."""
    super(PlsRecallEventData, self).__init__(data_type=self.DATA_TYPE)
    self.database_name = None
    self.query = None
    self.sequence_number = None
    self.username = None


class PlsRecallParser(interface.FileObjectParser):
  """Parse PL/SQL Recall files.

  Parser is based on:

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

  _INITIAL_FILE_OFFSET = None
  _PLS_KEYWORD = frozenset([
      u'begin', u'commit', u'create', u'declare', u'drop', u'end', u'exception',
      u'execute', u'insert', u'replace', u'rollback', u'select', u'set',
      u'update'])

  # 6 * 365 * 24 * 60 * 60 * 1000000.
  _SIX_YEARS_IN_MICRO_SECONDS = 189216000000000

  NAME = u'pls_recall'
  DESCRIPTION = u'Parser for PL/SQL Recall files.'

  _PLS_RECALL_RECORD = construct.Struct(
      u'PL/SQL_Recall',
      construct.ULInt32(u'Sequence'),
      construct.LFloat64(u'TimeStamp'),
      construct.String(u'Username', 31, None, b'\x00'),
      construct.String(u'Database', 81, None, b'\x00'),
      construct.String(u'Query', 4001, None, b'\x00'))

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a PLSRecall.dat file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      is_pls = self.VerifyFile(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile((
          u'Not a PLSrecall File, unable to parse.'
          u'with error: {0:s}').format(exception))

    if not is_pls:
      raise errors.UnableToParseFile(
          u'Not a PLSRecall File, unable to parse.')

    file_object.seek(0, os.SEEK_SET)
    pls_record = self._PLS_RECALL_RECORD.parse_stream(file_object)

    while pls_record:
      event_data = PlsRecallEventData()

      event_data.database_name = pls_record.Database
      event_data.sequence_number = pls_record.Sequence
      event_data.query = pls_record.Query
      event_data.username = pls_record.Username

      date_time = dfdatetime_delphi_date_time.DelphiDateTime(
          timestamp=pls_record.TimeStamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      try:
        pls_record = self._PLS_RECALL_RECORD.parse_stream(file_object)
      except construct.FieldError:
        # The code has reached the end of file (EOF).
        break

  def VerifyFile(self, file_object):
    """Check if the file is a PLSRecall.dat file.

    Args:
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      bool: True if this is a valid PLSRecall.dat file, False otherwise.
    """
    file_object.seek(0, os.SEEK_SET)

    # The file consists of PL/SQL structures that are equal
    # size (4125 bytes) TRecallRecord records. It should be
    # noted that the query value is free form.
    try:
      structure = self._PLS_RECALL_RECORD.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return False

    # Verify that the timestamp is no more than six years into the future.
    # Six years is an arbitrary time length just to evaluate the timestamp
    # against some value. There is no guarantee that this will catch everything.
    # TODO: Add a check for similarly valid value back in time. Maybe if it the
    # timestamp is before 1980 we are pretty sure it is invalid?
    # TODO: This is a very flaky assumption. Find a better one.
    future_timestamp = (
        timelib.Timestamp.GetNow() + self._SIX_YEARS_IN_MICRO_SECONDS)

    if structure.TimeStamp > future_timestamp:
      return False

    # TODO: Add other verification checks here. For instance make sure
    # that the query actually looks like a SQL query. This structure produces a
    # lot of false positives and thus we need to add additional verification to
    # make sure we are not parsing non-PLSRecall files.
    # Another check might be to make sure the username looks legitimate, or the
    # sequence number, or the database name.
    # For now we just check if all three fields pass our "is this a text" test.
    if not utils.IsText(structure.Username):
      return False
    if not utils.IsText(structure.Query):
      return False
    if not utils.IsText(structure.Database):
      return False

    # Take the first word from the query field and attempt to match that against
    # allowed queries.
    first_word, _, _ = structure.Query.partition(b' ')

    if first_word.lower() not in self._PLS_KEYWORD:
      return False

    return True


manager.ParsersManager.RegisterParser(PlsRecallParser)
