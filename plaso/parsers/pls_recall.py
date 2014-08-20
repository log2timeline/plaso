#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specifiSc language governing permissions and
# limitations under the License.
"""Parser for PL-SQL Developer Recall files."""

import construct
import os

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import timelib
from plaso.lib import utils
from plaso.parsers import interface


class PlsRecallEvent(event.EventObject):
  """Convenience class for a PL-SQL Recall file container."""

  DATA_TYPE = 'PLSRecall:event'

  def __init__(self, timestamp, sequence, user, database, query):
    """Initializes the event object.

    Args:
      timestamp: The timestamp when the entry was created.
      sequence: Sequence indicates the order of execution.
      username: The username that made the query.
      database_name: String containing the databe name.
      query: String containing the PL-SQL query.
    """
    super(PlsRecallEvent, self).__init__()
    self.timestamp = timestamp
    self.sequence = sequence
    self.username = user
    self.database_name = database
    self.query = query


class PlsRecallParser(interface.BaseParser):
  """Parse PL-SQL Recall files.

  Parser is based on a:
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

  NAME = 'pls_recall'

  PLS_STRUCT = construct.Struct(
    'PL-SQL_Recall',
    construct.ULInt32('Sequence'),
    construct.LFloat64('TimeStamp'),
    construct.String('Username', 31, None, '\x00'),
    construct.String('Database', 81, None, '\x00'),
    construct.String('Query', 4001, None, '\x00'))

  def Parse(self, parser_context, file_entry):
    """Extract entries from a PLSRecall.dat file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Yields:
      An pls_recall event for each entry in the file.
    """
    file_object = file_entry.GetFileObject()

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
      yield PlsRecallEvent(
        timelib.Timestamp.FromDelphiTime(pls_record.TimeStamp),
        pls_record.Sequence, pls_record.Username,
        pls_record.Database, pls_record.Query)

      try:
        pls_record = self.PLS_STRUCT.parse_stream(file_object)
      except (construct.FieldError) as exception:
        # The code has reached the end of file (EOF).
        break

    file_object.close()

  def VerifyFile(self, file_object):
    """Check if the file is a PLSRecall.dat file.

    Args:
      file_object: file that we want to check.

    Returns:
      True if this is a valid PLSRecall.dat file, otherwise False.
    """
    file_object.seek(0, os.SEEK_SET)

    # The file consists of PL-SQL structures that are equal
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

    return True
