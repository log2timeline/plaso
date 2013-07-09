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
import logging
import os
import tempfile

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import registry

import sqlite3


class PlasoParser(object):
  """A parent class defining a typical log parser.

  This parent class gets inherited from other classes that are parsing
  log files.

  """
  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

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


class SQLiteParser(PlasoParser):
  """A SQLite assistance parser for Plaso."""

  __abstract = True

  # Queries to be executed.
  # Should be a list of tuples with two entries, SQLCommand and callback
  # function name.
  QUERIES = []

  # List of tables that should be present in the database, for verification.
  REQUIRED_TABLES = ()

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
      raise errors.UnableToParseFile(
          u'File %s not a %s. (invalid signature)' % (
              filehandle.name, self.parser_name))

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

    with sqlite3.connect(name) as self.db:
      try:
        self.db.row_factory = sqlite3.Row
        cursor = self.db.cursor()
      except sqlite3.DatabaseError as e:
        logging.debug('SQLite error occured: %s', e)

      # Verify the table by reading in all table names and compare it to
      # the list of required tables.
      try:
        sql_results = cursor.execute(
            'SELECT name FROM sqlite_master WHERE type="table"')
      except sqlite3.DatabaseError as e:
        logging.debug('SQLite error occured: %s', e)
        raise errors.UnableToParseFile(
            u'Unable to open the database file: %s', e)
      tables = []
      for row in sql_results:
        tables.append(row[0])

      if not set(tables) >= set(self.REQUIRED_TABLES):
        self._RemoveTempFile(name, filehandle.name)
        raise errors.UnableToParseFile(
            u'File %s not a %s (wrong tables).' % (filehandle.name,
            self.parser_name))

      for query, action in self.QUERIES:
        try:
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

    self._RemoveTempFile(name, filehandle.name)

  def _RemoveTempFile(self, name, orig_name):
    """Delete the temporary created db file from the system."""
    try:
      os.remove(name)
    except (OSError, IOError) as e:
      logging.warning(
          u'Unable to remove temporary file: %s [derived from %s] due to: %s',
          name, orig_name, e)

  def Default(self, **kwarg):
    """Default callback method for SQLite events, does nothing."""
    __pychecker__ = 'unusednames=self'
    logging.debug('Default handler: %s', kwarg)


class BundleParser(PlasoParser):
  """A base class for parsers that need more than a single file to parse."""

  __abstract = True

  # A list of all file patterns to match against. This list will be used by the
  # collector to find all available files to parse.
  PATTERNS = []

  @abc.abstractmethod
  def ParseBundle(self, filehandles):
    """Return a generator of EventObjects from a list of files.

    Args:
      filehandles: A list of open file like objects.

    Yields:
      EventObject for each extracted event.
    """
    pass

  def Parse(self, filebundle):
    """Return a generator for EventObjects extracted from a path bundle."""
    if not isinstance(filebundle, event.EventPathBundle):
      raise errors.UnableToParseFile(u'Not a file bundle.')

    bundle_pattern = getattr(filebundle, 'pattern', None)

    if not bundle_pattern:
      raise errors.UnableToParseFile(u'No bundle pattern defined.')

    if u'|'.join(self.PATTERNS) != bundle_pattern:
      raise errors.UnableToParseFile(u'No bundle pattern defined.')

    filehandles = list(filebundle)

    return self.ParseBundle(filehandles)
