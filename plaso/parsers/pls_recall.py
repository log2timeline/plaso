# -*- coding: utf-8 -*-
"""Parser for PL/SQL Developer Recall files."""

import os

import construct

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.lib import utils
from plaso.parsers import interface
from plaso.parsers import manager


class PlsRecallEvent(time_events.DelphiTimeEvent):
  """Convenience class for a PL/SQL Recall file container."""

  DATA_TYPE = u'PLSRecall:event'

  def __init__(self, delphi_time, sequence, user, database, query):
    """Initializes the event object.

    Args:
      delphi_time: the Delphi time value when the entry was created.
      sequence: Sequence indicates the order of execution.
      username: The username that made the query.
      database_name: String containing the database name.
      query: String containing the PL/SQL query.
    """
    super(PlsRecallEvent, self).__init__(
        delphi_time, eventdata.EventTimestamp.CREATION_TIME)
    self.database_name = database
    self.query = query
    self.sequence = sequence
    self.username = user


class PlsRecallParser(interface.FileObjectParser):
  """Parse PL/SQL Recall files.

  Parser is based on a::

    TRecallRecord = packed record
      Sequence: Integer;
      TimeStamp: TDateTime;
      Username: array[0..30] of Char;
      Database: array[0..80] of Char;
      Text: array[0..4000] of Char;
    end;

    Delphi TDateTime is a little endian 64-bit
    floating point without any time zone information
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

  PLS_STRUCT = construct.Struct(
      u'PL/SQL_Recall',
      construct.ULInt32(u'Sequence'),
      construct.LFloat64(u'TimeStamp'),
      construct.String(u'Username', 31, None, b'\x00'),
      construct.String(u'Database', 81, None, b'\x00'),
      construct.String(u'Query', 4001, None, b'\x00'))

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a PLSRecall.dat file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

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
    pls_record = self.PLS_STRUCT.parse_stream(file_object)

    while pls_record:
      event_object = PlsRecallEvent(
          pls_record.TimeStamp, pls_record.Sequence, pls_record.Username,
          pls_record.Database, pls_record.Query)
      parser_mediator.ProduceEvent(event_object)

      try:
        pls_record = self.PLS_STRUCT.parse_stream(file_object)
      except construct.FieldError:
        # The code has reached the end of file (EOF).
        break

  def VerifyFile(self, file_object):
    """Check if the file is a PLSRecall.dat file.

    Args:
      file_object: file that we want to check.

    Returns:
      True if this is a valid PLSRecall.dat file, otherwise False.
    """
    file_object.seek(0, os.SEEK_SET)

    # The file consists of PL/SQL structures that are equal
    # size (4125 bytes) TRecallRecord records. It should be
    # noted that the query value is free form.
    try:
      structure = self.PLS_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return False

    # Verify few entries inside the structure.
    try:
      timestamp = timelib.Timestamp.FromDelphiTime(structure.TimeStamp)
    except ValueError:
      return False

    if timestamp <= 0:
      return False

    # Verify that the timestamp is no more than six years into the future.
    # Six years is an arbitrary time length just to evaluate the timestamp
    # against some value. There is no guarantee that this will catch everything.
    # TODO: Add a check for similarly valid value back in time. Maybe if it the
    # timestamp is before 1980 we are pretty sure it is invalid?
    # TODO: This is a very flaky assumption. Find a better one.
    current_timestamp = timelib.Timestamp.GetNow()
    if timestamp > current_timestamp + self._SIX_YEARS_IN_MICRO_SECONDS:
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
