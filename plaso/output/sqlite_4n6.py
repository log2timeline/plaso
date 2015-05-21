# -*- coding: utf-8 -*-
"""Defines the output module for the SQLite database used by 4n6time."""


import logging
import os

import sqlite3
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class SQLite4n6OutputModule(interface.OutputModule):
  """Saves the data in a SQLite database, used by the tool 4n6time."""

  NAME = u'sql4n6'
  DESCRIPTION = (
      u'Saves the data in a SQLite database, used by the tool 4n6Time.')

  META_FIELDS = frozenset([
      u'sourcetype', u'source', u'user', u'host', u'MACB', u'color', u'type',
      u'record_number'])

  _DEFAULT_FIELDS = [
      u'host', u'user', u'source', u'sourcetype', u'type', u'datetime',
      u'color']

  def __init__(self, output_mediator, filehandle=None, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
      filehandle: Holds the filename.

    Raises:
      ValueError: if the file handle is missing.
    """
    super(SQLite4n6OutputModule, self).__init__(output_mediator, **kwargs)

    if not filehandle:
      raise errors.ValueError(u'Missing file handle.')

    self._filename = filehandle

    self.set_status = self._output_mediator.GetConfigurationValue(u'set_status')
    self.evidence = self._output_mediator.GetConfigurationValue(
        u'evidence', default_value=u'-')
    self.append = self._output_mediator.GetConfigurationValue(
        u'append', default_value=False)
    self.fields = self._output_mediator.GetConfigurationValue(
        u'fields', default_value=self._DEFAULT_FIELDS)
    self.db_create_table_string = (
        u'CREATE TABLE log2timeline (timezone TEXT, '
        u'MACB TEXT, source TEXT, sourcetype TEXT, type TEXT, '
        u'user TEXT, host TEXT, description TEXT, filename TEXT, '
        u'inode TEXT, notes TEXT, format TEXT, extra TEXT, '
        u'datetime datetime, reportnotes TEXT, '
        u'inreport TEXT, tag TEXT, color TEXT, offset INT,'
        u'store_number INT, store_index INT, vss_store_number INT,'
        u'url TEXT, record_number TEXT, event_identifier TEXT, '
        u'event_type TEXT, source_name TEXT, user_sid TEXT, '
        u'computer_name TEXT, evidence TEXT)')
    self.db_insert_string = (
        u'INSERT INTO log2timeline(timezone, MACB, source, '
        u'sourcetype, type, user, host, description, filename, '
        u'inode, notes, format, extra, datetime, reportnotes, inreport,'
        u'tag, color, offset, store_number, store_index, vss_store_number,'
        u'URL, record_number, event_identifier, event_type,'
        u'source_name, user_sid, computer_name, evidence) '
        u'VALUES (:timezone, :MACB, :source, :sourcetype, :type, :user, :host, '
        u':description, :filename, :inode, :notes, :format, :extra, :datetime, '
        u':reportnotes, :inreport, '
        u':tag, :color, :offset, :store_number, :store_index, '
        u':vss_store_number,'
        u':URL, :record_number, :event_identifier, :event_type,'
        u':source_name, :user_sid, :computer_name, :evidence)')

  def _GetDistinctValues(self, field_name):
    """Query database for unique field types.

    Args:
      field_name: name of the filed to retrieve.
    """
    self.curs.execute(
        u'SELECT {0:s}, COUNT({0:s}) FROM log2timeline GROUP BY {0:s}'.format(
            field_name))

    result = {}
    for row in self.curs.fetchall():
      if row[0]:
        result[row[0]] = row[1]
    return result

  def _GetVSSNumber(self, event_object):
    """Return the vss_store_number of the event or -1.

    Args:
      event_object: the event object (instance of EventObject).
    """
    if not hasattr(event_object, u'pathspec'):
      return -1

    return getattr(event_object.pathspec, u'vss_store_number', -1)

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

  def _GetSanitizedEventValues(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    event_formatter = self._output_mediator.GetEventFormatter(event_object)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

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
    format_variables = self._output_mediator.GetFormatStringAttributeNames(
        event_object)
    if format_variables is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    extra = []
    for key in event_object.GetAttributes():
      if (key in definitions.RESERVED_VARIABLE_NAMES or key in
          format_variables):
        continue
      extra.append(u'{0:s}: {1!s} '.format(
          key, getattr(event_object, key, None)))
    extra = u' '.join(extra)

    inode = getattr(event_object, u'inode', u'-')
    if inode == '-':
      if (hasattr(event_object, u'pathspec') and
          hasattr(event_object.pathspec, u'inode')):
        inode = event_object.pathspec.inode

    date_use_string = u'{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(
        date_use.year, date_use.month, date_use.day, date_use.hour,
        date_use.minute, date_use.second)
    tags = []
    if hasattr(event_object, u'tag'):
      if hasattr(event_object.tag, u'tags'):
        tags = event_object.tag.tags
    taglist = ','.join(tags)
    row = {u'timezone': unicode(self._output_mediator.timezone),
           u'MACB': self._output_mediator.GetMACBRepresentation(event_object),
           u'source': source_short,
           u'sourcetype': source,
           u'type': getattr(event_object, u'timestamp_desc', u'-'),
           u'user': getattr(event_object, u'username', u'-'),
           u'host': getattr(event_object, u'hostname', u'-'),
           u'description': message,
           u'filename': getattr(event_object, u'filename', u'-'),
           u'inode': inode,
           u'notes': getattr(event_object, u'notes', u'-'),
           u'format': getattr(event_object, u'parser', u'-'),
           u'extra': extra,
           u'datetime': date_use_string,
           u'reportnotes': u'',
           u'inreport': u'',
           u'tag': taglist,
           u'color': u'',
           u'offset': getattr(event_object, u'offset', 0),
           u'store_number': event_object.store_number,
           u'store_index': event_object.store_index,
           u'vss_store_number': self._GetVSSNumber(event_object),
           u'URL': getattr(event_object, u'url', u'-'),
           u'record_number': getattr(event_object, u'record_number', 0),
           u'event_identifier': getattr(
               event_object, u'event_identifier', u'-'),
           u'event_type': getattr(event_object, u'event_type', u'-'),
           u'source_name': getattr(event_object, u'source_name', u'-'),
           u'user_sid': getattr(event_object, u'user_sid', u'-'),
           u'computer_name': getattr(event_object, u'computer_name', u'-'),
           u'evidence': self.evidence}

    return row

  def Close(self):
    """Disconnects from the database.

    This method will create the necessary indices and commit outstanding
    transactions before disconnecting.
    """
    # Build up indices for the fields specified in the args.
    # It will commit the inserts automatically before creating index.
    if not self.append:
      for field_name in self.fields:
        sql = u'CREATE INDEX {0}_idx ON log2timeline ({0})'.format(field_name)
        self.curs.execute(sql)
        if self.set_status:
          self.set_status(u'Created index: {0:s}'.format(field_name))

    # Get meta info and save into their tables.
    if self.set_status:
      self.set_status(u'Creating metadata...')

    for field in self.META_FIELDS:
      vals = self._GetDistinctValues(field)
      self.curs.execute(u'DELETE FROM l2t_{0:s}s'.format(field))
      for name, freq in vals.items():
        self.curs.execute((
            u'INSERT INTO l2t_{0:s}s ({1:s}s, frequency) '
            u'VALUES("{2:s}", {3:d}) ').format(field, field, name, freq))
    self.curs.execute(u'DELETE FROM l2t_tags')
    for tag in self._ListTags():
      self.curs.execute(u'INSERT INTO l2t_tags (tag) VALUES (?)', [tag])

    if self.set_status:
      self.set_status(u'Database created.')

    self.conn.commit()
    self.curs.close()
    self.conn.close()

  def Open(self):
    """Connects to the database and creates the required tables.

    Raises:
      IOError: if a file with filename already exists.
    """

    if (not self.append) and os.path.isfile(self._filename):
      raise IOError((
          u'Unable to use an already existing file for output '
          u'[{0:s}]').format(self._filename))

    self.conn = sqlite3.connect(self._filename)
    self.curs = self.conn.cursor()

    # Create table in database.
    if not self.append:
      self.curs.execute(self.db_create_table_string)

      for field in self.META_FIELDS:
        self.curs.execute(
            u'CREATE TABLE l2t_{0}s ({0}s TEXT, frequency INT)'.format(field))
        if self.set_status:
          self.set_status(u'Created table: l2t_{0:s}'.format(field))

      self.curs.execute(u'CREATE TABLE l2t_tags (tag TEXT)')
      if self.set_status:
        self.set_status(u'Created table: l2t_tags')

      self.curs.execute(u'CREATE TABLE l2t_saved_query (name TEXT, query TEXT)')
      if self.set_status:
        self.set_status(u'Created table: l2t_saved_query')

      self.curs.execute(
          u'CREATE TABLE l2t_disk (disk_type INT, mount_path TEXT, '
          u'dd_path TEXT, dd_offset TEXT, storage_file TEXT, export_path TEXT)')

      self.curs.execute(
          u'INSERT INTO l2t_disk (disk_type, mount_path, dd_path,dd_offset, '
          u'storage_file, export_path) VALUES (0, "", "", "", "", "")')
      if self.set_status:
        self.set_status(u'Created table: l2t_disk')

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

    row = self._GetSanitizedEventValues(event_object)
    self.curs.execute(self.db_insert_string, row)
    self.count += 1
    # Commit the current transaction every 10000 inserts.
    if self.count % 10000 == 0:
      self.conn.commit()
      if self.set_status:
        self.set_status(u'Inserting event: {0:d}'.format(self.count))


manager.OutputManager.RegisterOutput(SQLite4n6OutputModule)
