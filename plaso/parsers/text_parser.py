#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains a class to provide a parsing framework to plaso.

This class contains a base framework class for parsing fileobjects, and
also some implementations that extend it to provide a more comprehensive
parser.
"""

import abc
import csv
import logging
import os

from dfvfs.helpers import text_file
import pyparsing

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import lexer
from plaso.lib import timelib
from plaso.lib import utils
from plaso.parsers import interface

import pytz

# Pylint complains about some functions not being implemented that shouldn't
# be since they need to be implemented by children.
# pylint: disable=abstract-method


class SlowLexicalTextParser(interface.BaseParser, lexer.SelfFeederMixIn):
  """Generic text based parser that uses lexer to assist with parsing.

  This text parser is based on a rather slow lexer, which makes the
  use of this interface highly discouraged. Parsers that already
  implement it will most likely all be rewritten to support faster
  text parsing implementations.

  This text based parser needs to be extended to provide an accurate
  list of tokens that define the structure of the log file that the
  parser is designed for.
  """
  __abstract = True

  # Define the max number of lines before we determine this is
  # not the correct parser.
  MAX_LINES = 15

  # List of tokens that describe the structure of the log file.
  tokens = [
      lexer.Token('INITIAL', '(.+)\n', 'ParseString', ''),
      ]

  def __init__(self, local_zone=True):
    """Constructor for the SlowLexicalTextParser.

    Args:
      local_zone: A boolean value that determines if the entries
                  in the log file are stored in the local time
                  zone of the computer that stored it or in a fixed
                  timezone, like UTC.
    """
    # TODO: remove the multiple inheritance.
    lexer.SelfFeederMixIn.__init__(self)
    interface.BaseParser.__init__(self)
    self.line_ready = False
    self.attributes = {
        'body': '',
        'iyear': 0,
        'imonth': 0,
        'iday': 0,
        'time': '',
        'hostname': '',
        'username': '',
    }
    self.local_zone = local_zone
    self.file_entry = None

  def ClearValues(self):
    """Clears all the values inside the attributes dict.

    All values that start with the letter 'i' are considered
    to be an integer, otherwise string value is assumed.
    """
    self.line_ready = False
    for attr in self.attributes:
      if attr[0] == 'i':
        self.attributes[attr] = 0
      else:
        self.attributes[attr] = ''

  def ParseIncomplete(self, match=None, **unused_kwargs):
    """Indication that we've got a partial line to match against.

    Args:
      match: The regular expression match object.
    """
    self.attributes['body'] += match.group(0)
    self.line_ready = True

  def ParseMessage(self, **unused_kwargs):
    """Signal that a line is ready to be parsed."""
    self.line_ready = True

  def SetMonth(self, match=None, **unused_kwargs):
    """Parses the month.

       This is a callback function for the text parser (lexer) and is
       called by the corresponding lexer state.

    Args:
      match: The regular expression match object.
    """
    self.attributes['imonth'] = int(
        timelib.MONTH_DICT.get(match.group(1).lower(), 1))

  def SetDay(self, match=None, **unused_kwargs):
    """Parses the day of the month.

       This is a callback function for the text parser (lexer) and is
       called by the corresponding lexer state.

    Args:
      match: The regular expression match object.
    """
    self.attributes['iday'] = int(match.group(1))

  def SetTime(self, match=None, **unused_kwargs):
    """Set the time attribute.

    Args:
      match: The regular expression match object.
    """
    self.attributes['time'] = match.group(1)

  def SetYear(self, match=None, **unused_kwargs):
    """Parses the year.

       This is a callback function for the text parser (lexer) and is
       called by the corresponding lexer state.

    Args:
      match: The regular expression match object.
    """
    self.attributes['iyear'] = int(match.group(1))

  def Parse(self, parser_context, file_entry):
    """Extract data from a text file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Yields:
      An event object (instance of EventObject).
    """
    path_spec_printable = u'{0:s}:{1:s}'.format(
        file_entry.path_spec.type_indicator, file_entry.name)
    file_object = file_entry.GetFileObject()

    self.file_entry = file_entry
    # TODO: this is necessary since we inherit from lexer.SelfFeederMixIn.
    self.file_object = file_object

    # Start by checking, is this a text file or not? Before we proceed
    # any further.
    file_object.seek(0, os.SEEK_SET)
    if not utils.IsText(file_object.read(40)):
      raise errors.UnableToParseFile(u'Not a text file, unable to proceed.')

    file_object.seek(0, os.SEEK_SET)

    error_count = 0
    file_verified = False
    # We need to clear out few values in the Lexer before continuing.
    # There might be some leftovers from previous run.
    self.error = 0
    self.buffer = ''

    while True:
      _ = self.NextToken()

      if self.state == 'INITIAL':
        self.entry_offset = getattr(self, 'next_entry_offset', 0)
        self.next_entry_offset = file_object.tell() - len(self.buffer)

      if not file_verified and self.error >= self.MAX_LINES * 2:
        logging.debug(
            u'Lexer error count: {0:d} and current state {1:s}'.format(
                self.error, self.state))
        file_object.close()
        raise errors.UnableToParseFile(
            u'[{0:s}] unsupported file: {1:s}.'.format(
                self.parser_name, path_spec_printable))

      if self.line_ready:
        try:
          yield self.ParseLine(parser_context)
          file_verified = True

        except errors.TimestampNotCorrectlyFormed as exception:
          error_count += 1
          if file_verified:
            logging.debug(
                u'[{0:s} VERIFIED] Error count: {1:d} and ERROR: {2:d}'.format(
                    path_spec_printable, error_count, self.error))
            logging.warning(
                u'[{0:s}] Unable to parse timestamp with error: {1:s}'.format(
                    self.parser_name, exception))

          else:
            logging.debug((
                u'[{0:s} EVALUATING] Error count: {1:d} and ERROR: '
                u'{2:d})').format(path_spec_printable, error_count, self.error))

            if error_count >= self.MAX_LINES:
              file_object.close()
              raise errors.UnableToParseFile(
                  u'[{0:s}] unsupported file: {1:s}.'.format(
                      self.parser_name, path_spec_printable))

        finally:
          self.ClearValues()

      if self.Empty():
        # Try to fill the buffer to prevent the parser from ending prematurely.
        self.Feed()

      if self.Empty():
        break

    if not file_verified:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parser file: {1:s}.'.format(
              self.parser_name, path_spec_printable))

    file_offset = file_object.get_offset()
    if file_offset < file_object.get_size():
      logging.error((
          u'{0:s} prematurely terminated parsing: {1:s} at offset: '
          u'0x{2:08x}.').format(
              self.parser_name, path_spec_printable, file_offset))
    file_object.close()

  def ParseString(self, match=None, **unused_kwargs):
    """Return a string with combined values from the lexer.

    Args:
      match: The regular expression match object.

    Returns:
      A string that combines the values that are so far
      saved from the lexer.
    """
    try:
      self.attributes['body'] += match.group(1).strip('\n')
    except IndexError:
      self.attributes['body'] += match.group(0).strip('\n')

  def PrintLine(self):
    """"Return a string with combined values from the lexer."""
    year = getattr(self.attributes, 'iyear', None)
    month = getattr(self.attributes, 'imonth', None)
    day = getattr(self.attributes, 'iday', None)

    if None in [year, month, day]:
      date_string = u'[DATE NOT SET]'
    else:
      try:
        year = int(year, 10)
        month = int(month, 10)
        day = int(day, 10)

        date_string = u'{0:04d}-{1:02d}-{2:02d}'.format(year, month, day)
      except ValueError:
        date_string = u'[DATE INVALID]'

    time_string = getattr(self.attributes, 'time', u'[TIME NOT SET]')
    hostname_string = getattr(self.attributes, 'hostname', u'HOSTNAME NOT SET')
    reporter_string = getattr(
        self.attributes, 'reporter', u'[REPORTER NOT SET]')
    body_string = getattr(self.attributes, 'body', u'[BODY NOT SET]')

    # TODO: this is a work in progress. The reason for the try-catch is that
    # the text parser is handed a non-text file and must deal with converting
    # arbitrary binary data.
    try:
      line = u'{0:s} {1:s} [{2:s}] {3:s} => {4:s}'.format(
          date_string, time_string, hostname_string, reporter_string,
          body_string)
    except UnicodeError:
      line = 'Unable to print line - due to encoding error.'

    return line

  def ParseLine(self, parser_context):
    """Return an event object extracted from the current line.

    Args:
      parser_context: A parser context object (instance of ParserContext).

    Returns:
      An event object (instance of TextEvent).
    """
    if not self.attributes['time']:
      raise errors.TimestampNotCorrectlyFormed(
          u'Unable to parse timestamp, time not set.')

    if not self.attributes['iyear']:
      raise errors.TimestampNotCorrectlyFormed(
          u'Unable to parse timestamp, year not set.')

    times = self.attributes['time'].split(':')
    if self.local_zone:
      timezone = parser_context.timezone
    else:
      timezone = pytz.UTC

    if len(times) < 3:
      raise errors.TimestampNotCorrectlyFormed((
          u'Unable to parse timestamp, not of the format HH:MM:SS '
          u'[{0:s}]').format(self.PrintLine()))
    try:
      secs = times[2].split('.')
      if len(secs) == 2:
        sec, us = secs
      else:
        sec = times[2]
        us = 0

      timestamp = timelib.Timestamp.FromTimeParts(
          int(self.attributes['iyear']), self.attributes['imonth'],
          self.attributes['iday'], int(times[0]), int(times[1]),
          int(sec), microseconds=int(us), timezone=timezone)

    except ValueError as exception:
      raise errors.TimestampNotCorrectlyFormed(
          u'Unable to parse: {0:s} with error: {1:s}'.format(
              self.PrintLine(), exception))

    return self.CreateEvent(
        timestamp, getattr(self, 'entry_offset', 0), self.attributes)

  # TODO: this is a rough initial implementation to get this working.
  def CreateEvent(self, timestamp, offset, attributes):
    """Creates an event.

       This function should be overwritten by text parsers that require
       to generate specific event object type, the default is TextEvent.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      offset: The offset of the event.
      attributes: A dict that contains the events attributes.

    Returns:
      An event object (instance of TextEvent).
    """
    event_object = event.TextEvent(timestamp, attributes)
    event_object.offset = offset
    return event_object


class TextCSVParser(interface.BaseParser):
  """An implementation of a simple CSV line-per-entry log files."""

  __abstract = True

  # A list that contains the names of all the fields in the log file.
  COLUMNS = []

  # A CSV file is comma separated, but this can be overwritten to include
  # tab, pipe or other character separation.
  VALUE_SEPARATOR = ','

  # If there is a header before the lines start it can be defined here, and
  # the number of header lines that need to be skipped before the parsing
  # starts.
  NUMBER_OF_HEADER_LINES = 0

  # If there is a special quote character used inside the structured text
  # it can be defined here.
  QUOTE_CHAR = '"'

  # Value that should not appear inside the file, made to test the actual
  # file to see if it confirms to standards.
  MAGIC_TEST_STRING = 'RegnThvotturMeistarans'

  def VerifyRow(self, unused_parser_context, unused_row):
    """Return a bool indicating whether or not this is the correct parser.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: A single row from the CSV file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    pass

  def ParseRow(self, unused_parser_context, row):
    """Parse a line of the log file and yield extracted EventObject(s).

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: A dictionary containing all the fields as denoted in the
           COLUMNS class list.

    Yields:
      An EventObject extracted from a single line from the log file.
    """
    event_object = event.EventObject()
    event_object.row_dict = row
    yield event_object

  def Parse(self, parser_context, file_entry):
    """Extract data from a CVS file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Yields:
      An event object (instance of EventObject).
    """
    path_spec_printable = file_entry.path_spec.comparable.replace(u'\n', u';')
    file_object = file_entry.GetFileObject()
    file_object.seek(0, os.SEEK_SET)

    text_file_object = text_file.TextFile(file_object)

    # If we specifically define a number of lines we should skip do that here.
    for _ in range(0, self.NUMBER_OF_HEADER_LINES):
      _ = text_file_object.readline()

    reader = csv.DictReader(
        text_file_object, fieldnames=self.COLUMNS,
        restkey=self.MAGIC_TEST_STRING, restval=self.MAGIC_TEST_STRING,
        delimiter=self.VALUE_SEPARATOR, quotechar=self.QUOTE_CHAR)

    try:
      row = reader.next()
    except csv.Error:
      raise errors.UnableToParseFile(
          u'[{0:s}] Unable to parse CSV file: {1:s}.'.format(
              self.parser_name, path_spec_printable))

    number_of_columns = len(self.COLUMNS)
    number_of_records = len(row)

    if number_of_records != number_of_columns:
      raise errors.UnableToParseFile((
          u'[{0:s}] Unable to parse CSV file: {1:s}. Wrong number of '
          u'records (expected: {2:d}, got: {3:d})').format(
              self.parser_name, path_spec_printable, number_of_columns,
              number_of_records))

    for key, value in row.items():
      if key == self.MAGIC_TEST_STRING or value == self.MAGIC_TEST_STRING:
        raise errors.UnableToParseFile((
            u'[{0:s}] Unable to parse CSV file: {1:s}. Signature '
            u'mismatch.').format(self.parser_name, path_spec_printable))

    if not self.VerifyRow(parser_context, row):
      raise errors.UnableToParseFile((
          u'[{0:s}] Unable to parse CSV file: {1:s}. Verification '
          u'failed.').format(self.parser_name, path_spec_printable))

    for event_object in self.ParseRow(parser_context, row):
      if event_object:
        event_object.offset = text_file_object.tell()
        yield event_object

    for row in reader:
      for event_object in self.ParseRow(parser_context, row):
        if event_object:
          event_object.offset = text_file_object.tell()
          yield event_object

    file_object.close()


def PyParseRangeCheck(lower_bound, upper_bound):
  """Verify that a number is within a defined range.

  This is a callback method for pyparsing setParseAction
  that verifies that a read number is within a certain range.

  To use this method it needs to be defined as a callback method
  in setParseAction with the upper and lower bound set as parameters.

  Args:
    lower_bound: An integer representing the lower bound of the range.
    upper_bound: An integer representing the upper bound of the range.

  Returns:
    A callback method that can be used by pyparsing setParseAction.
  """
  def CheckRange(unused_string, unused_location, tokens):
    """Parse the arguments."""
    try:
      check_number = tokens[0]
    except IndexError:
      check_number = -1

    if check_number < lower_bound:
      raise pyparsing.ParseException(
          u'Value: {0:d} precedes lower bound: {1:d}'.format(
              check_number, lower_bound))

    if check_number > upper_bound:
      raise pyparsing.ParseException(
          u'Value: {0:d} exceeds upper bound: {1:d}'.format(
              check_number, upper_bound))

  # Since callback methods for pyparsing need to accept certain parameters
  # and there is no way to define conditions, like upper and lower bounds
  # we need to return here a method that accepts those pyparsing parameters.
  return CheckRange


def PyParseIntCast(unused_string, unused_location, tokens):
  """Return an integer from a string.

  This is a pyparsing callback method that converts the matched
  string into an integer.

  The method modifies the content of the tokens list and converts
  them all to an integer value.

  Args:
    unused_string: The original parsed string.
    unused_location: The location within the string where the match was made.
    tokens: A list of extracted tokens (where the string to be converted is
    stored).
  """
  # Cast the regular tokens.
  for index, token in enumerate(tokens):
    try:
      tokens[index] = int(token)
    except ValueError:
      logging.error(u'Unable to cast [{0:s}] to an int, setting to 0'.format(
          token))
      tokens[index] = 0

  # We also need to cast the dictionary built tokens.
  for key in tokens.keys():
    try:
      tokens[key] = int(tokens[key], 10)
    except ValueError:
      logging.error(
          u'Unable to cast [{0:s} = {1:d}] to an int, setting to 0'.format(
              key, tokens[key]))
      tokens[key] = 0


def PyParseJoinList(unused_string, unused_location, tokens):
  """Return a joined token from a list of tokens.

  This is a callback method for pyparsing setParseAction that modifies
  the returned token list to join all the elements in the list to a single
  token.

  Args:
    unused_string: The original parsed string.
    unused_location: The location within the string where the match was made.
    tokens: A list of extracted tokens. This is the list that should be joined
    together and stored as a single token.
  """
  join_list = []
  for token in tokens:
    try:
      join_list.append(str(token))
    except UnicodeDecodeError:
      join_list.append(repr(token))

  tokens[0] = u''.join(join_list)
  del tokens[1:]


class PyparsingConstants(object):
  """A class that maintains constants for pyparsing."""

  # Numbers.
  INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(PyParseIntCast)
  IPV4_OCTET = pyparsing.Word(pyparsing.nums, min=1, max=3).setParseAction(
      PyParseIntCast, PyParseRangeCheck(0, 255))
  IPV4_ADDRESS = (IPV4_OCTET + ('.' + IPV4_OCTET) * 3).setParseAction(
      PyParseJoinList)

  # TODO: Fix the IPv6 address specification to be more accurate (8 :, correct
  # size, etc).
  IPV6_ADDRESS = pyparsing.Word(':' + pyparsing.hexnums).setParseAction(
      PyParseJoinList)

  # Common words.
  MONTH = pyparsing.Word(
      pyparsing.string.uppercase, pyparsing.string.lowercase,
      exact=3)

  # Define date structures.
  HYPHEN = pyparsing.Literal('-').suppress()
  YEAR = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      PyParseIntCast)
  TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      PyParseIntCast)
  ONE_OR_TWO_DIGITS = pyparsing.Word(
      pyparsing.nums, min=1, max=2).setParseAction(PyParseIntCast)
  DATE = pyparsing.Group(
      YEAR + pyparsing.Suppress('-') + TWO_DIGITS +
      pyparsing.Suppress('-') + TWO_DIGITS)
  DATE_REV = pyparsing.Group(
      TWO_DIGITS + pyparsing.Suppress('-') + TWO_DIGITS +
      pyparsing.Suppress('-') + YEAR)
  TIME = pyparsing.Group(
      TWO_DIGITS + pyparsing.Suppress(':') + TWO_DIGITS +
      pyparsing.Suppress(':') + TWO_DIGITS)
  TIME_MSEC = TIME + pyparsing.Suppress('.') + INTEGER
  DATE_TIME = DATE + TIME
  DATE_TIME_MSEC = DATE + TIME_MSEC

  COMMENT_LINE_HASH = pyparsing.Literal('#') + pyparsing.SkipTo(
      pyparsing.LineEnd())
  # TODO: Add more commonly used structs that can be used by parsers.
  PID = pyparsing.Word(
      pyparsing.nums, min=1, max=5).setParseAction(PyParseIntCast)


class PyparsingSingleLineTextParser(interface.BaseParser):
  """Single line text parser based on the pyparsing library."""
  __abstract = True

  # The actual structure, this needs to be defined by each parser.
  # This is defined as a list of tuples so that more then a single line
  # structure can be defined. That way the parser can support more than a
  # single type of log entry, despite them all having in common the constraint
  # that each log entry is a single line.
  # The tuple should have two entries, a key and a structure. This is done to
  # keep the structures in an order of priority/preference.
  # The key is a comment or an identification that is passed to the ParseRecord
  # function so that the developer can identify which structure got parsed.
  # The value is the actual pyparsing structure.
  LINE_STRUCTURES = []

  # In order for the tool to not read too much data into a buffer to evaluate
  # whether or not the parser is the right one for this file or not we
  # specifically define a maximum amount of bytes a single line can occupy. This
  # constant can be overwritten by implementations if their format might have a
  # longer line than 400 bytes.
  MAX_LINE_LENGTH = 400

  # Define an encoding. If a file is encoded using specific encoding it is
  # advised to include it here. If this class constant is set all lines wil be
  # decoded prior to being sent to parsing by pyparsing, if not properly set it
  # could negatively affect parsing of the file.
  # If this value needs to be calculated on the fly (not a fixed constant for
  # this particular file type) it can be done by modifying the self.encoding
  # attribute.
  ENCODING = ''

  def __init__(self):
    """A constructor for the pyparsing assistant."""
    super(PyparsingSingleLineTextParser, self).__init__()
    self.encoding = self.ENCODING
    self._current_offset = 0
    # TODO: self._line_structures is a work-around and this needs
    # a structural fix.
    self._line_structures = self.LINE_STRUCTURES

  def _ReadLine(self, text_file_object, max_len=0, quiet=False, depth=0):
    """Read a single line from a text file and return it back.

    Args:
      text_file_object: A text file object (instance of dfvfs.TextFile).
      max_len: If defined determines the maximum number of bytes a single line
      can take.
      quiet: If True then a decode warning is not displayed.
      depth: A threshold of how many newlines we can encounter before bailing
      out.

    Returns:
      A single line read from the file-like object, or the maximum number of
      characters (if max_len defined and line longer than the defined size).
    """
    if max_len:
      line = text_file_object.readline(max_len)
    else:
      line = text_file_object.readline()

    if not line:
      return

    # If line is empty, skip it and go on.
    if line == '\n' or line == '\r\n':
      # Max 40 new lines in a row before we bail out.
      if depth == 40:
        return ''

      return self._ReadLine(text_file_object, max_len, depth=depth + 1)

    if not self.encoding:
      return line.strip()

    try:
      decoded_line = line.decode(self.encoding)
      return decoded_line.strip()
    except UnicodeDecodeError:
      if not quiet:
        logging.warning(u'Unable to decode line [{0:s}...] using {1:s}'.format(
            repr(line[1:30]), self.encoding))
      return line.strip()

  def Parse(self, parser_context, file_entry):
    """Extract data from a text file using a pyparsing definition.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Yields:
      An event object (instance of EventObject).
    """
    # TODO: find a more elegant way for this; currently the mac_wifi and
    # syslog parser seem to rely on this member.
    self.file_entry = file_entry

    file_object = file_entry.GetFileObject()

    # TODO: self._line_structures is a work-around and this needs
    # a structural fix.
    if not self._line_structures:
      raise errors.UnableToParseFile(
          u'Line structure undeclared, unable to proceed.')

    file_object.seek(0, os.SEEK_SET)
    text_file_object = text_file.TextFile(file_object)

    line = self._ReadLine(text_file_object, self.MAX_LINE_LENGTH, True)
    if not line:
      raise errors.UnableToParseFile(u'Not a text file.')

    if len(line) == self.MAX_LINE_LENGTH or len(
        line) == self.MAX_LINE_LENGTH - 1:
      logging.debug((
          u'Trying to read a line and reached the maximum allowed length of '
          u'{0:d}. The last few bytes of the line are: {1:s} [parser '
          u'{2:s}]').format(
              self.MAX_LINE_LENGTH, repr(line[-10:]), self.parser_name))

    if not utils.IsText(line):
      raise errors.UnableToParseFile(u'Not a text file, unable to proceed.')

    if not self.VerifyStructure(parser_context, line):
      raise errors.UnableToParseFile('Wrong file structure.')

    # Set the offset to the beginning of the file.
    self._current_offset = 0
    # Read every line in the text file.
    while line:
      parsed_structure = None
      use_key = None
      # Try to parse the line using all the line structures.
      for key, structure in self.LINE_STRUCTURES:
        try:
          parsed_structure = structure.parseString(line)
        except pyparsing.ParseException:
          pass
        if parsed_structure:
          use_key = key
          break

      if parsed_structure:
        parsed_event = self.ParseRecord(
            parser_context, use_key, parsed_structure)
        if parsed_event:
          parsed_event.offset = self._current_offset
          yield parsed_event
      else:
        logging.warning(u'Unable to parse log line: {0:s}'.format(line))

      self._current_offset = text_file_object.get_offset()
      line = self._ReadLine(text_file_object)

    file_object.close()

  @abc.abstractmethod
  def ParseRecord(self, parser_context, key, structure):
    """Parse a single extracted pyparsing structure.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.

    Returns:
      An event object (instance of EventObject) or None.
    """

  @abc.abstractmethod
  def VerifyStructure(self, parser_context, line):
    """Verify the structure of the file and return boolean based on that check.

    This function should read enough text from the text file to confirm
    that the file is the correct one for this particular parser.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """


class PyparsingMultiLineTextParser(PyparsingSingleLineTextParser):
  """Multi line text parser based on the pyparsing library."""

  __abstract = True

  BUFFER_SIZE = 2048

  def __init__(self):
    """A constructor for the pyparsing assistant."""
    super(PyparsingMultiLineTextParser, self).__init__()
    self._buffer = ''
    self._buffer_size = self.BUFFER_SIZE

  def _FillBuffer(self, filehandle):
    """Fill the buffer."""
    if len(self._buffer) > self._buffer_size:
      return

    self._buffer += filehandle.read(self._buffer_size)

    # If a parser specifically indicates specific encoding we need
    # to handle the buffer as it is an unicode string.
    # If it fails we fail back to the original raw string.
    if self.encoding:
      try:
        buffer_decoded = self._buffer.decode(self.encoding)
        self._buffer = buffer_decoded
      except UnicodeDecodeError:
        pass

  def _NextLine(self, filehandle):
    """Move to the next newline in the buffer."""
    throw, _, self._buffer = self._buffer.partition('\n')
    if throw.startswith('\r'):
      throw = throw[1:]
      self._current_offset += 1

    self._current_offset += 1 + len(throw)
    self._FillBuffer(filehandle)
    return throw

  def Parse(self, parser_context, file_entry):
    """Parse a text file using a pyparsing definition.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Yields:
      An event object (instance of EventObject).
    """
    self.file_entry = file_entry

    file_object = file_entry.GetFileObject()

    if not self.LINE_STRUCTURES:
      raise errors.UnableToParseFile(
          u'Line structure undeclared, unable to proceed.')

    file_object.seek(0, os.SEEK_SET)

    self._buffer = ''
    self._FillBuffer(file_object)

    if not utils.IsText(self._buffer):
      raise errors.UnableToParseFile(u'Not a text file, unable to proceed.')

    if not self.VerifyStructure(parser_context, self._buffer):
      raise errors.UnableToParseFile('Wrong file structure.')

    # Set the offset to the beginning of the file.
    self._current_offset = 0

    # Read every line in the text file.
    while self._buffer:
      # Initialize pyparsing objects.
      tokens = None
      start = 0
      end = 0

      structure_key = None

      # Try to parse the line using all the line structures.
      for key, structure in self.LINE_STRUCTURES:
        try:
          parsed_structure = next(
              structure.scanString(self._buffer, maxMatches=1), None)
        except pyparsing.ParseException:
          continue
        if not parsed_structure:
          continue

        tokens, start, end = parsed_structure

        # Only want to parse the structure if it starts
        # at the beginning of the buffer.
        if start == 0:
          structure_key = key
          break

      if tokens and not start:
        parsed_event = self.ParseRecord(parser_context, structure_key, tokens)
        if parsed_event:
          parsed_event.offset = self._current_offset
          yield parsed_event
        self._current_offset += end
        self._buffer = self._buffer[end:]
      else:
        old_line = self._NextLine(file_object)
        if old_line:
          logging.warning(u'Unable to parse log line: {0:s}'.format(
              repr(old_line)))

      # Re-fill the buffer.
      self._FillBuffer(file_object)
