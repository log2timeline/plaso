#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
import calendar
import datetime
import logging
import os
import pytz
import tempfile

import sqlite3

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import lexer
from plaso.lib import registry
from plaso.lib import timelib


class PlasoParser(object):
  """A parent class defining a typical log parser.

  This parent class gets inherited from other classes that are parsing
  log files.

  There is one class variables that needs defining:
    NAME - the name of the type of file being parsed, eg. Syslog
    PARSER_TYPE - the name of the filetype the parser is capable of
    parsing. (eg. TXT, EVTX)
  """
  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  NAME = 'General Log Parser'
  PARSER_TYPE = 'all'

  def __init__(self, pre_obj):
    """Parser constructor.

    Args:
      pre_obj: A PlasoPreprocess object that may contain information gathered
      from a preprocessing process.
    """
    self._pre_obj = pre_obj

  @property
  def parser_name(self):
    """Return the name of the parser."""
    return self.__class__.__name__

  @abc.abstractmethod
  def Parse(self, filehandle):
    """Verifies and parses the log file and returns EventObjects.

    This is the main function of the class, the one that actually
    goes through the log file and parses each line of it to
    produce a parsed line and a timestamp.

    It also tries to verify the file structure and see if the class is capable
    of parsing the file passed to the module. It will do so with series of tests
    that should determine if the file is of the correct structure.

    If the class is not capable of parsing the file passed to it an exception
    should be raised, an exception of the type UnableToParseFile that indicates
    the reason why the class does not parse it.

    Args:
      filehandle: A filehandle/file-like-object that is seekable to the file
      needed to be checked.

    Raises:
      NotImplementedError when not implemented.
    """
    raise NotImplementedError

  def Scan(self, filehandle):
    """Scans the file without verifying it, extracting EventObjects from it.

    Unlike the Parse() method it is not required to implement this method.
    This method skips the verification portion that is included in the Parse()
    method and automatically assumes that the file may not be correctly formed,
    potentially corrupted or only contains portion of the format that this
    parser provides support for.

    If the parser has the potential to scan the file and extract potential
    EventObjects from it, then this method should be implemented. It will never
    been called during the normal runtime of the tool, it is only called
    against a single file (for instance unallocated) using a single parser.

    Args:
      filehandle: A filehandle/file-like-object that is seekable to the file
      needed to be checked.

    Raises:
      NotImplementedError when not implemented.
    """
    raise NotImplementedError


class TextParser(PlasoParser, lexer.SelfFeederMixIn):
  """Generic text based parser that uses lexer to assist with parsing.

  This text based parser needs to be extended to provide an accurate
  list of tokens that define the structure of the log file that the
  parser is designed for.
  """
  __abstract = True

  # Description of the log file.
  NAME = 'Generic Text File'
  PARSER_TYPE = 'txt'

  # Define the max number of lines before we determine this is
  # not the correct parser.
  MAX_LINES = 15

  # List of tokens that describe the structure of the log file.
  tokens = [
      lexer.Token('INITIAL', '(.+)\n', 'ParseString', ''),
      ]

  def __init__(self, pre_obj, local_zone=True):
    """Constructor for the TextParser.

    Args:
      pre_obj: A PlasoPreprocess object that may contain information gathered
      from a preprocessing process.
      local_zone: A boolean value that determines if the entries
                  in the log file are stored in the local time
                  zone of the computer that stored it or in a fixed
                  timezone, like UTC.
    """
    lexer.SelfFeederMixIn.__init__(self)
    PlasoParser.__init__(self, pre_obj)
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
    """Set the month value."""
    self.attributes['imonth'] = int(
        timelib.MONTH_DICT.get(match.group(1).lower(), 1))

  def SetDay(self, match, **_):
    """Set the day attribute."""
    self.attributes['iday'] = int(match.group(1))

  def SetTime(self, match, **_):
    """Set the time attribute."""
    self.attributes['time'] = match.group(1)

  def SetYear(self, match, **_):
    """Set the year."""
    self.attributes['iyear'] = int(match.group(1))

  def Parse(self, filehandle):
    """Try to parse each line in the file."""
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
        raise errors.UnableToParseFile('File %s not a %s.' % (name, self.NAME))
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
                             'Msg: [%s]'), self.NAME, e)
          else:
            logging.debug('[%s EVALUATING] Error count: %d and ERROR: %d',
                          filehandle.name, error_count, self.error)
            if error_count >= self.MAX_LINES:
              raise errors.UnableToParseFile('File %s not a %s.' % (
                  self.fd.name, self.NAME))

        finally:
          self.ClearValues()
      if self.Empty():
        break

    if not file_verified:
      raise errors.UnableToParseFile('File %s not a %s.' % (filehandle.name,
                                                            self.NAME))

  def ParseString(self, match, **_):
    """Add a string to the body attribute."""
    try:
      self.attributes['body'] += match.group(1).strip('\n')
    except IndexError:
      self.attributes['body'] += match.group(0).strip('\n')

  def PrintLine(self):
    """Return a string with combined values from the lexer.

    Returns:
      A string that combines the values that are so far
      saved from the lexer.
    """
    month = int(self.attributes['imonth'])
    day = int(self.attributes['iday'])
    year = int(self.attributes['iyear'])

    return '%02d/%02d/%04d %s [%s] %s => %s' % (month, day, year,
                                                self.attributes['time'],
                                                self.attributes['hostname'],
                                                self.attributes['reporter'],
                                                self.attributes['body'])

  def ParseLine(self, zone):
    """Return an EventObject extracted from the current line."""
    times = self.attributes['time'].split(':')
    if self.local_zone:
      time_zone = zone
    else:
      time_zone = pytz.UTC

    if len(times) < 3:
      raise errors.TimestampNotCorrectlyFormed(('Unable to parse timestamp, '
                                                'not of the format HH:MM:SS '
                                                '[%s]') % self.PrintLine())
    try:
      secs = times[2].split('.')
      if len(secs) == 2:
        sec, us = secs
      else:
        sec = times[2]
        us = 0

      timestamp = datetime.datetime(int(self.attributes['iyear']),
                                    self.attributes['imonth'],
                                    self.attributes['iday'], int(times[0]),
                                    int(times[1]), int(sec), int(us),
                                    time_zone)
    except ValueError as e:
      raise errors.TimestampNotCorrectlyFormed('Unable to parse: %s [er: %s]',
                                               self.PrintLine(), e)

    epoch = int(calendar.timegm(timestamp.timetuple()) * 1e6)
    epoch += timestamp.microsecond

    __pychecker__ = ('missingattrs=source_long')
    evt = event.TextEvent(epoch, self.attributes, self.source_long)
    evt.offset = getattr(self, 'entry_offset', 0)
    return evt


class SQLiteParser(PlasoParser):
  """A SQLite assistance parser for Plaso."""

  __abstract = True

  # Queries to be executed.
  # Should be a list of tuples with two entries, SQLCommand and callback
  # function name.
  QUERIES = []

  # List of tables that should be present in the database, for verification.
  REQUIRED_TABLES = ()

  # Description of the log file.
  NAME = 'Generic SQLite Parsing'
  PARSER_TYPE = 'sqlite'

  def __init__(self, pre_obj, local_zone=False):
    """Constructor for the SQLite parser."""
    super(SQLiteParser, self).__init__(pre_obj)
    self._local_zone = local_zone

  def Parse(self, filehandle):
    """Return a generator for EventObjects extracted from SQLite db."""

    # TODO: Remove this when the classifier gets implemented
    # and used. As of now, there is no check made against the file
    # to verify it's signature, thus all files are sent here, meaning
    # that this method assumes everything is a SQLite file and starts
    # copying the content of the file into memory, which is not good
    # for very large files.
    magic = 'SQLite format 3'
    data = filehandle.read(len(magic))

    if data != magic:
      filehandle.seek(-len(magic), 1)
      raise errors.UnableToParseFile('File %s not a %s. (wrong magic)' % (
          filehandle.name, self.NAME))

    # TODO: Current design copies the entire file into a buffer
    # that is parsed by each SQLite parser. This is not very efficient,
    # especially when many SQLite parsers are ran against a relatively
    # large SQLite database. This temporary file that is created should
    # be usable by all SQLite parsers so the file should only be read
    # once in memory and then deleted when all SQLite parsers have completed.

    # TODO: Change this into a proper implementation using APSW
    # and virtual filesystems when that will be available.
    # Info: http://apidoc.apsw.googlecode.com/hg/vfs.html#vfs and
    # http://apidoc.apsw.googlecode.com/hg/example.html#example-vfs
    # Until then, just copy the file into a tempfile and parse it.
    name = ''
    with tempfile.NamedTemporaryFile(delete=False) as fh:
      name = fh.name
      while data:
        fh.write(data)
        data = filehandle.read(65536)

    try:
      with sqlite3.connect(name) as self.db:
        self.db.row_factory = sqlite3.Row
        cursor = self.db.cursor()

        # Verify the table by reading in all table names and compare it to
        # the list of required tables.
        sql_results = cursor.execute(('SELECT name FROM sqlite_master WHERE '
                                      'type="table"'))
        tables = []
        for row in sql_results:
          tables.append(row[0])

        if not set(tables) >= set(self.REQUIRED_TABLES):
          raise errors.UnableToParseFile(
              'File %s not a %s (wrong tables).' % (filehandle.name,
                                                    self.NAME))

        for query, action in self.QUERIES:
          call_back = getattr(self, action, self.Default)
          sql_results = cursor.execute(query)
          row = sql_results.fetchone()
          while row:
            evt_gen = call_back(row=row, zone=self._pre_obj.zone)
            if evt_gen:
              for evt in evt_gen:
                if evt.timestamp < 0:
                  # TODO: For now we dependend on the timestamp to be
                  # set, change this soon so the timestamp does not need to
                  # be set.
                  evt.timestamp = 0
                evt.query = query
                if not hasattr(evt, 'offset'):
                  if 'id' in row.keys():
                    evt.offset = row['id']
                  else:
                    evt.offset = 0
                yield evt
            row = sql_results.fetchone()
    except sqlite3.DatabaseError as e:
      logging.debug('SQLite error occured: %s', e)

    try:
      os.remove(name)
    except (OSError, IOError) as e:
      logging.warning(
          u'Unable to remove temporary file: %s [derived from %s] due to: %s',
          name, filehandle.name, e)

  def Default(self, **kwarg):
    """Default callback method for SQLite events, does nothing."""
    __pychecker__ = 'unusednames=self'
    logging.debug('Default handler: %s', kwarg)

