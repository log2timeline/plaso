#!/usr/bin/python
# -*- coding: utf-8 -*-
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

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import lexer
from plaso.lib import parser
from plaso.lib import timelib
from plaso.lib import utils

import pyparsing
import pytz


class SlowLexicalTextParser(parser.PlasoParser, lexer.SelfFeederMixIn):
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

  def __init__(self, pre_obj, local_zone=True):
    """Constructor for the SlowLexicalTextParser.

    Args:
      pre_obj: A PlasoPreprocess object that may contain information gathered
      from a preprocessing process.
      local_zone: A boolean value that determines if the entries
                  in the log file are stored in the local time
                  zone of the computer that stored it or in a fixed
                  timezone, like UTC.
    """
    lexer.SelfFeederMixIn.__init__(self)
    parser.PlasoParser.__init__(self, pre_obj)
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

  def ParseIncomplete(self, match, **_):
    """Indication that we've got a partial line to match against."""
    self.attributes['body'] += match.group(0)
    self.line_ready = True

  def ParseMessage(self, **_):
    """Signal that a line is ready to be parsed."""
    self.line_ready = True

  def SetMonth(self, match, **_):
    """Parses the month.

       This is a callback function for the text parser (lexer) and is
       called by the corresponding lexer state.

    Args:
      match: A regular expression match group that contains the match
             by the lexer.
    """
    self.attributes['imonth'] = int(
        timelib.MONTH_DICT.get(match.group(1).lower(), 1))

  def SetDay(self, match, **_):
    """Parses the day of the month.

       This is a callback function for the text parser (lexer) and is
       called by the corresponding lexer state.

    Args:
      match: A regular expression match group that contains the match
             by the lexer.
    """
    self.attributes['iday'] = int(match.group(1))

  def SetTime(self, match, **_):
    """Set the time attribute."""
    self.attributes['time'] = match.group(1)

  def SetYear(self, match, **_):
    """Parses the year.

       This is a callback function for the text parser (lexer) and is
       called by the corresponding lexer state.

    Args:
      match: A regular expression match group that contains the match
             by the lexer.
    """
    self.attributes['iyear'] = int(match.group(1))

  def Parse(self, filehandle):
    """Try to parse each line in the file."""
    # Start by checking, is this a text file or not? Before we proceed
    # any further.
    filehandle.seek(0)
    if not utils.IsText(filehandle.read(40)):
      raise errors.UnableToParseFile(u'Not a text file, unable to proceed.')

    self.fd = filehandle
    filehandle.seek(0)
    error_count = 0
    file_verified = False
    # We need to clear out few values in the Lexer before continuing.
    # There might be some leftovers from previous run.
    self.error = 0
    self.buffer = ''

    while 1:
      _ = self.NextToken()

      if self.state == 'INITIAL':
        self.entry_offset = getattr(self, 'next_entry_offset', 0)
        self.next_entry_offset = self.fd.tell() - len(self.buffer)

      if not file_verified and self.error >= self.MAX_LINES * 2:
        logging.debug('Lexer error count: %d and current state %s', self.error,
                      self.state)
        name = '%s (%s)' % (self.fd.name, self.fd.display_name)
        raise errors.UnableToParseFile(u'File %s not a %s.' % (
            name, self.parser_name))

      if self.line_ready:
        try:
          yield self.ParseLine(self._pre_obj.zone)
          file_verified = True
        except errors.TimestampNotCorrectlyFormed as e:
          error_count += 1
          if file_verified:
            logging.debug('[%s VERIFIED] Error count: %d and ERROR: %d',
                          filehandle.name, error_count, self.error)
            logging.warning(('[%s] Unable to parse timestamp, skipping entry. '
                             'Msg: [%s]'), self.parser_name, e)
          else:
            logging.debug('[%s EVALUATING] Error count: %d and ERROR: %d',
                          filehandle.name, error_count, self.error)
            if error_count >= self.MAX_LINES:
              raise errors.UnableToParseFile(u'File %s not a %s.' % (
                  self.fd.name, self.parser_name))

        finally:
          self.ClearValues()
      if self.Empty():
        break

    if not file_verified:
      raise errors.UnableToParseFile(
          u'File %s not a %s.' % (filehandle.name, self.parser_name))

  def ParseString(self, match, **_):
    """Return a string with combined values from the lexer.

    Args:
      match: The matching object.

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
    month = int(self.attributes['imonth'])
    day = int(self.attributes['iday'])
    year = int(self.attributes['iyear'])

    # TODO: this is a work in progress. The reason for the try-catch is that
    # the text parser is handed a non-text file and must deal with converting
    # arbitrary binary data.
    try:
      line = u'%04d-%02d-%02d %s [%s] %s => %s' % (
          year, month, day, self.attributes['time'],
          self.attributes['hostname'], self.attributes['reporter'],
          self.attributes['body'])
    except UnicodeError:
      line = 'Unable to print line - due to encoding error.'

    return line

  def ParseLine(self, zone):
    """Return an EventObject extracted from the current line."""
    if not self.attributes['time']:
      raise errors.TimestampNotCorrectlyFormed(
          u'Unable to parse timestamp, time not set.')

    if not self.attributes['iyear']:
      raise errors.TimestampNotCorrectlyFormed(
          u'Unable to parse timestamp, year not set.')

    times = self.attributes['time'].split(':')
    if self.local_zone:
      time_zone = zone
    else:
      time_zone = pytz.UTC

    if len(times) < 3:
      raise errors.TimestampNotCorrectlyFormed(
          u'Unable to parse timestamp, not of the format HH:MM:SS [%s]' % (
              self.PrintLine()))
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
          int(sec), int(us), time_zone)

    except ValueError as e:
      raise errors.TimestampNotCorrectlyFormed(
          u'Unable to parse: %s [er: %s]', self.PrintLine(), e)

    return self.CreateEvent(
        timestamp, getattr(self, 'entry_offset', 0), self.attributes)

  # TODO: this is a rough initial implementation to get this working.
  # pylint: disable-msg=R0201
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
      A text event (TextEvent).
    """
    event_object = event.TextEvent(timestamp, attributes)
    event_object.offset = offset
    return event_object


class TextCSVParser(parser.PlasoParser):
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

  @abc.abstractmethod
  def VerifyRow(self, row):
    """Return a bool indicating whether or not this is the correct parser."""
    pass

  def ParseRow(self, row):    # pylint: disable-msg=R0201
    """Parse a line of the log file and return an extracted EventObject.

    Args:
      row: A dictionary containing all the fields as denoted in the
      COLUMNS class list.

    Returns:
      An EventObject extracted from a single line from the log file.
    """
    event_object = event.EventObject()
    event_object.row_dict = row
    return event_object

  def Parse(self, filehandle):
    """A generator that returns extracted EventObjects from the log file."""
    self.entry_offset = 0
    # If we specifically define a number of lines we should skip do that here.
    for _ in range(0, self.NUMBER_OF_HEADER_LINES):
      line = filehandle.readline()
      self.entry_offset += len(line)

    reader = csv.DictReader(
        filehandle, fieldnames=self.COLUMNS, restkey=self.MAGIC_TEST_STRING,
        restval=self.MAGIC_TEST_STRING, delimiter=self.VALUE_SEPARATOR,
        quotechar=self.QUOTE_CHAR)

    try:
      row = reader.next()
    except csv.Error:
      raise errors.UnableToParseFile(
          u'File %s not a CSV file, unable to parse.' % filehandle.name)

    if len(row) != len(self.COLUMNS):
      raise errors.UnableToParseFile(
          u'File %s not a %s. (wrong nr. of columns %d vs. %d)' % (
              filehandle.name, self.parser_name, len(row), len(self.COLUMNS)))

    for key, value in row.items():
      if key == self.MAGIC_TEST_STRING or value == self.MAGIC_TEST_STRING:
        raise errors.UnableToParseFile(
            u'File %s not a %s (wrong nr. of columns, should be %d' % (
                filehandle.name, self.parser_name, len(row)))

    if not self.VerifyRow(row):
      raise errors.UnableToParseFile('File %s not a %s. (wrong magic)' % (
          filehandle.name, self.parser_name))

    for evt in self._ParseRow(row):
      if evt:
        yield evt

    for row in reader:
      for evt in self._ParseRow(row):
        if evt:
          yield evt

  def _ParseRow(self, row):
    """Parse a line and extract an EventObject from it if possible."""
    for evt in self.ParseRow(row):
      if not evt:
        continue
      evt.offset = self.entry_offset
      yield evt

    self.entry_offset += len(self.VALUE_SEPARATOR.join(row.values())) + 1


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
  def CheckRange(dummy_string, dummy_location, tokens):
    """Parse the arguments."""
    try:
      check_number = tokens[0]
    except IndexError:
      check_number = -1
    if check_number < lower_bound:
      raise pyparsing.ParseException('Value [{}] is lower than {}'.format(
          check_number, lower_bound))
    if check_number > upper_bound:
      raise pyparsing.ParseException('Value [{}] is higher than {}'.format(
          check_number, upper_bound))

  # Since callback methods for pyparsing need to accept certain parameters
  # and there is no way to define conditions, like upper and lower bounds
  # we need to return here a method that accepts those pyparsing parameters.
  return CheckRange


def PyParseIntCast(dummy_string, dummy_location, tokens):
  """Return an integer from a string.

  This is a pyparsing callback method that converts the matched
  string into an integer.

  The method modifies the content of the tokens list and converts
  them all to an integer value.

  Args:
    dummy_string: The original parsed string.
    dummy_location: The location within the string where the match was made.
    tokens: A list of extracted tokens (where the string to be converted is
    stored).
  """
  for index, token in enumerate(tokens):
    try:
      tokens[index] = int(token)
    except ValueError:
      logging.error(u'Unable to cast [{}] to an int, returning -1'.format(
          token))
      tokens[index] = 0


def PyParseJoinList(dummy_string, dummy_location, tokens):
  """Return a joined token from a list of tokens.

  This is a callback method for pyparsing setParseAction that modifies
  the returned token list to join all the elements in the list to a single
  token.

  Args:
    dummy_string: The original parsed string.
    dummy_location: The location within the string where the match was made.
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


class PyparsingSingleLineTextParser(parser.PlasoParser):
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

  def __init__(self, pre_obj):
    """A constructor for the pyparsing assistant."""
    super(PyparsingSingleLineTextParser, self).__init__(pre_obj)
    self.encoding = self.ENCODING
    self._current_offset = 0

  @abc.abstractmethod
  def VerifyStructure(self, line):
    """Verify the structure of the file and return boolean based on that check.

    This function should read enough text from the text file to confirm
    that the file is the correct one for this particular parser.

    Args:
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    if not line:
      return False

    return False

  @abc.abstractmethod
  def ParseRecord(self, key, structure):
    """Parse a single extracted pyparsing structure.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

    Args:
      key: An identification string indicating the name of the parsed
      structure.
      structure: A pyparsing.ParseResults object from a line in the
      log file.

    Returns:
      An EventObject if one can be extracted from the structure, otherwise
      None.
    """
    pass

  def _ReadLine(self, filehandle, max_len=0):
    """Read a single line from a text file and return it back."""
    if max_len:
      line = filehandle.readline(max_len)
    else:
      line = filehandle.readline()

    # If line is empty, skip it and go on.
    if line == '\n' or line == '\r\n':
      return self._ReadLine(filehandle, max_len)

    if not self.encoding:
      return line.strip()

    try:
      decoded_line = line.decode(self.encoding)
      return decoded_line.strip()
    except UnicodeDecodeError:
      logging.warning(u'Unable to decode line [{}...] using {}'.format(
          repr(line[1:30]), self.encoding))
      return line.strip()


  def Parse(self, filehandle):
    """Parse a text file using a pyparsing definition."""
    if not self.LINE_STRUCTURES:
      raise errors.UnableToParseFile(
          u'Line structure undeclared, unable to proceed.')

    filehandle.seek(0)

    line = self._ReadLine(filehandle, self.MAX_LINE_LENGTH)
    if len(line) == self.MAX_LINE_LENGTH or len(
        line) == self.MAX_LINE_LENGTH - 1:
      logging.debug((
          u'Trying to read a line and reached the maximum allowed length of '
          '{}. The last few bytes of the line are: {} [parser {}]').format(
              self.MAX_LINE_LENGTH, repr(line[-10:]), self.parser_name))

    if not utils.IsText(line):
      raise errors.UnableToParseFile(u'Not a text file, unable to proceed.')

    if not self.VerifyStructure(line):
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
        parsed_event = self.ParseRecord(use_key, parsed_structure)
        if parsed_event:
          parsed_event.offset = self._current_offset
          yield parsed_event
      else:
        logging.warning(u'Unable to parse log line: {}'.format(line))

      self._current_offset = filehandle.tell()
      line = self._ReadLine(filehandle)
