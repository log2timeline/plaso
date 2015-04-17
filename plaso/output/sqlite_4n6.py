# -*- coding: utf-8 -*-
"""Defines the output module for the SQLite database used by 4n6time."""

# TODO: Add a unit test for this output module.

import logging
import os
import sys

import sqlite3

from plaso import formatters
from plaso.formatters import interface as formatters_interface
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


__author__ = 'David Nides (david.nides@gmail.com)'


class SQLite4n6OutputModule(interface.OutputModule):
  """Saves the data in a SQLite database, used by the tool 4n6Time."""

  NAME = u'sql4n6'
  DESCRIPTION = (
      u'Saves the data in a SQLite database, used by the tool 4n6Time.')

  META_FIELDS = frozenset([
      'sourcetype', 'source', 'user', 'host', 'MACB', 'color', 'type',
      'record_number'])

  _DEFAULT_FIELDS = [
      u'host', u'user', u'source', u'sourcetype', u'type', u'datetime',
      u'color']

  def __init__(self, output_mediator, filehandle=sys.stdout, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
      filehandle: Optional file-like object that can be written to.
                  The default is sys.stdout.
    """
    super(SQLite4n6OutputModule, self).__init__(output_mediator, **kwargs)
    self._file_object = filehandle

    self.set_status = self._output_mediator.GetConfigurationValue(u'set_status')
    self.evidence = self._output_mediator.GetConfigurationValue(
        u'evidence', default_value=u'-')
    self.append = self._output_mediator.GetConfigurationValue(
        u'append', default_value=False)
    self.fields = self._output_mediator.GetConfigurationValue(
        u'fields', default_value=self._DEFAULT_FIELDS)

  def _GetDistinctValues(self, field_name):
    """Query database for unique field types.

    Args:
      field_name: name of the filed to retrieve.
    """
    self.curs.execute(
        u'SELECT {0:s}, COUNT({0:s}) FROM log2timeline GROUP BY {0:s}'.format(
            field_name))
    res = {}
    for row in self.curs.fetchall():
      if row[0] != '':
        res[row[0]] = int(row[1])
    return res

  def _ListTags(self):
    """Query database for unique tag types."""
    all_tags = []
    self.curs.execute(u'SELECT DISTINCT tag FROM log2timeline')

    # This cleans up the messy SQL return.
    for tag_row in self.curs.fetchall():
      tag_string = tag_row[0]
      if tag_string:
        tags = tag_string.split(',')
        for tag in tags:
          if tag not in all_tags:
            all_tags.append(tag)
    return all_tags

  def Close(self):
    """Disconnects from the database.

    This method will create the necessary indices and commit outstanding
    transactions before disconnecting.
    """
    # Build up indices for the fields specified in the args.
    # It will commit the inserts automatically before creating index.
    if not self.append:
      for field_name in self.fields:
        sql = 'CREATE INDEX {0}_idx ON log2timeline ({0})'.format(field_name)
        self.curs.execute(sql)
        if self.set_status:
          self.set_status('Created index: {0:s}'.format(field_name))

    # Get meta info and save into their tables.
    if self.set_status:
      self.set_status('Creating metadata...')

    for field in self.META_FIELDS:
      vals = self._GetDistinctValues(field)
      self.curs.execute('DELETE FROM l2t_{0:s}s'.format(field))
      for name, freq in vals.items():
        self.curs.execute((
            'INSERT INTO l2t_{0:s}s ({1:s}s, frequency) '
            'VALUES("{2:s}", {3:d}) ').format(field, field, name, freq))
    self.curs.execute('DELETE FROM l2t_tags')
    for tag in self._ListTags():
      self.curs.execute('INSERT INTO l2t_tags (tag) VALUES (?)', [tag])

    if self.set_status:
      self.set_status('Database created.')

    self.conn.commit()
    self.curs.close()
    self.conn.close()

  def Open(self):
    """Connects to the database and creates the required tables."""
    if self._file_object == sys.stdout:
      raise IOError(
          u'Unable to connect to stdout as database, please specify a file.')

    if (not self.append) and os.path.isfile(self._file_object):
      raise IOError((
          u'Unable to use an already existing file for output '
          u'[{0:s}]').format(self._file_object))

    self.conn = sqlite3.connect(self._file_object)
    self.conn.text_factory = str
    self.curs = self.conn.cursor()

    # Create table in database.
    if not self.append:
      self.curs.execute(
          ('CREATE TABLE log2timeline (timezone TEXT, '
           'MACB TEXT, source TEXT, sourcetype TEXT, type TEXT, '
           'user TEXT, host TEXT, description TEXT, filename TEXT, '
           'inode TEXT, notes TEXT, format TEXT, extra TEXT, '
           'datetime datetime, reportnotes TEXT, '
           'inreport TEXT, tag TEXT, color TEXT, offset INT,'
           'store_number INT, store_index INT, vss_store_number INT,'
           'url TEXT, record_number TEXT, event_identifier TEXT, '
           'event_type TEXT, source_name TEXT, user_sid TEXT, '
           'computer_name TEXT, evidence TEXT)'))
      if self.set_status:
        self.set_status('Created table: log2timeline')

      for field in self.META_FIELDS:
        self.curs.execute(
            'CREATE TABLE l2t_{0}s ({0}s TEXT, frequency INT)'.format(field))
        if self.set_status:
          self.set_status('Created table: l2t_{0:s}'.format(field))

      self.curs.execute('CREATE TABLE l2t_tags (tag TEXT)')
      if self.set_status:
        self.set_status('Created table: l2t_tags')

      self.curs.execute('CREATE TABLE l2t_saved_query (name TEXT, query TEXT)')
      if self.set_status:
        self.set_status('Created table: l2t_saved_query')

      self.curs.execute('CREATE TABLE l2t_disk (disk_type INT, mount_path TEXT,'
                        ' dd_path TEXT, dd_offset TEXT, storage_file TEXT,'
                        ' export_path TEXT)')
      self.curs.execute('INSERT INTO l2t_disk (disk_type, mount_path, dd_path,'
                        'dd_offset, storage_file, export_path) VALUES '
                        '(0, "", "", "", "", "")')
      if self.set_status:
        self.set_status('Created table: l2t_disk')

    self.count = 0

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    if u'timestamp' not in event_object.GetAttributes():
      return

    # TODO: remove this hack part of the storage/output refactor.
    # The event formatter class constants should not be changed directly.
    event_formatter = self._output_mediator.GetEventFormatter(event_object)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    if (isinstance(
        event_formatter, formatters.winreg.WinRegistryGenericFormatter) and
        event_formatter.FORMAT_STRING.find('<|>') == -1):
      event_formatter.FORMAT_STRING = u'[{keyname}]<|>{text}<|>'

    elif isinstance(
        event_formatter, formatters_interface.ConditionalEventFormatter):
      event_formatter.FORMAT_STRING_SEPARATOR = u'<|>'

    elif isinstance(event_formatter, formatters_interface.EventFormatter):
      event_formatter.FORMAT_STRING = event_formatter.FORMAT_STRING.replace(
          '}', '}<|>')

    message, _ = self._output_mediator.GetFormattedMessages(event_object)
    if message is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    source_short, source = self._output_mediator.GetFormattedSources(
        event_object)
    if source is None or source_short is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self._output_mediator.timezone)
    if not date_use:
      logging.error(u'Unable to process date for entry: {0:s}'.format(message))
      return
    format_variables = self._output_mediator.GetFormatStringAttributeNames()
    if format_variables is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    extra = []
    for key in event_object.GetAttributes():
      if (key in definitions.RESERVED_VARIABLE_NAMES or
          key in format_variables):
        continue
      extra.append(u'{0:s}: {1!s} '.format(
          key, getattr(event_object, key, None)))
    extra = u' '.join(extra)

    inode = getattr(event_object, 'inode', '-')
    if inode == '-':
      if (hasattr(event_object, 'pathspec') and
          hasattr(event_object.pathspec, 'image_inode')):
        inode = event_object.pathspec.image_inode

    date_use_string = u'{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(
        date_use.year, date_use.month, date_use.day, date_use.hour,
        date_use.minute, date_use.second)

    tags = []
    if hasattr(event_object, 'tag'):
      if hasattr(event_object.tag, 'tags'):
        tags = event_object.tag.tags
    taglist = ','.join(tags)
    row = (str(self._output_mediator.timezone),
           self._output_mediator.GetMACBRepresentation(event_object),
           source_short,
           source,
           getattr(event_object, 'timestamp_desc', '-'),
           getattr(event_object, 'username', '-'),
           getattr(event_object, 'hostname', '-'),
           message,
           getattr(event_object, 'filename', '-'),
           inode,
           getattr(event_object, 'notes', '-'),
           getattr(event_object, 'parser', '-'),
           extra,
           date_use_string,
           '',
           '',
           taglist,
           '',
           getattr(event_object, 'offset', 0),
           event_object.store_number,
           event_object.store_index,
           GetVSSNumber(event_object),
           getattr(event_object, 'url', '-'),
           getattr(event_object, 'record_number', 0),
           getattr(event_object, 'event_identifier', '-'),
           getattr(event_object, 'event_type', '-'),
           getattr(event_object, 'source_name', '-'),
           getattr(event_object, 'user_sid', '-'),
           getattr(event_object, 'computer_name', '-'),
           self.evidence
          )

    self.curs.execute(
        ('INSERT INTO log2timeline(timezone, MACB, source, '
         'sourcetype, type, user, host, description, filename, '
         'inode, notes, format, extra, datetime, reportnotes, inreport,'
         'tag, color, offset, store_number, store_index, vss_store_number,'
         'URL, record_number, event_identifier, event_type,'
         'source_name, user_sid, computer_name, evidence)'
         ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,'
         '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'), row)

    self.count += 1

    # Commit the current transaction every 10000 inserts.
    if self.count % 10000 == 0:
      self.conn.commit()
      if self.set_status:
        self.set_status('Inserting event: {0:d}'.format(self.count))


def GetVSSNumber(event_object):
  """Return the vss_store_number of the event."""
  if not hasattr(event_object, 'pathspec'):
    return -1

  return getattr(event_object.pathspec, 'vss_store_number', -1)


manager.OutputManager.RegisterOutput(SQLite4n6OutputModule)
