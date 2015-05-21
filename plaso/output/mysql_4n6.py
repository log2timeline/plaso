# -*- coding: utf-8 -*-
"""Defines the output module for the MySQL database used by 4n6time."""


import logging

import MySQLdb

from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class MySQL4n6OutputModule(interface.OutputModule):
  """Class defining the MySQL database output module for 4n6time."""

  NAME = 'mysql4n6'
  DESCRIPTION = u'MySQL database output for the 4n6time tool.'

  META_FIELDS = frozenset([
      u'sourcetype', u'source', u'user', u'host', u'MACB', u'color', u'type',
      u'record_number'])

  ARGUMENTS = [
      ('--db_user', {
          'dest': 'db_user',
          'type': unicode,
          'help': 'Defines the database user.',
          'metavar': 'USERNAME',
          'action': 'store',
          'default': 'root'}),
      ('--db_host', {
          'dest': 'db_host',
          'metavar': 'HOSTNAME',
          'type': unicode,
          'help': (
              'Defines the IP address or the hostname of the database '
              'server.'),
          'action': 'store',
          'default': 'localhost'}),
      ('--db_pass', {
          'dest': 'db_pass',
          'metavar': 'PASSWORD',
          'type': unicode,
          'help': 'The password for the database user.',
          'action': 'store',
          'default': 'forensic'}),
      ('--db_name', {
          'dest': 'db_name',
          'type': unicode,
          'help': 'The name of the database to connect to.',
          'action': 'store',
          'default': 'log2timeline'}),
      ('--append', {
          'dest': 'append',
          'action': 'store_true',
          'help': (
              'Defines whether the intention is to append to an already '
              'existing database or overwrite it. Defaults to overwrite.'),
          'default': False}),
      ('--fields', {
          'dest': 'fields',
          'action': 'store',
          'type': unicode,
          'nargs': '*',
          'help': 'Defines which fields should be indexed in the database.',
          'default': [
              'host', 'user', 'source', 'sourcetype', 'type', 'datetime',
              'color']}),
      ('--evidence', {
          'dest': 'evidence',
          'action': 'store',
          'help': (
              'Set the evidence field to a specific value, defaults to '
              'empty.'),
          'type': unicode,
          'default': '-'})]

  _DEFAULT_FIELDS = [
      u'host', u'user', u'source', u'sourcetype', u'type', u'datetime',
      u'color']

  def __init__(self, output_mediator, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
    """
    super(MySQL4n6OutputModule, self).__init__(output_mediator, **kwargs)

    self.set_status = self._output_mediator.GetConfigurationValue(u'set_status')
    self.host = self._output_mediator.GetConfigurationValue(
        u'db_host', default_value=u'localhost')
    self.user = self._output_mediator.GetConfigurationValue(
        u'db_user', default_value=u'root')
    self.password = self._output_mediator.GetConfigurationValue(
        u'db_pass', default_value=u'forensic')
    self.dbname = self._output_mediator.GetConfigurationValue(
        u'db_name', default_value=u'log2timeline')
    self.evidence = self._output_mediator.GetConfigurationValue(
        u'evidence', default_value=u'-')
    self.append = self._output_mediator.GetConfigurationValue(
        u'append', default_value=False)
    self.fields = self._output_mediator.GetConfigurationValue(
        u'fields', default_value=self._DEFAULT_FIELDS)
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

  def _GetVSSNumber(self, event_object):
    """Return the vss_store_number of the event or -1.

    Args:
      event_object: the event object (instance of EventObject).
    """
    if not hasattr(event_object, u'pathspec'):
      return -1

    return getattr(event_object.pathspec, u'vss_store_number', -1)

  def _GetDistinctValues(self, field_name):
    """Query database for unique field types.

    Args:
      field_name: name of the fieled to retrieve.

    Returns:
      A dictionary containing fields from META_FIELDS.
    """
    self.curs.execute(
        u'SELECT {0:s}, COUNT({0:s}) FROM log2timeline GROUP BY {0:s}'.format(
            field_name))
    result = {}
    for row in self.curs.fetchall():
      if row[0]:
        result[row[0]] = row[1]
    return result

  def _ListTags(self):
    """Query database for unique tag types."""
    all_tags = []
    self.curs.execute(
        u'SELECT DISTINCT tag FROM log2timeline')

    # This cleans up the messy SQL return.
    for tag_row in self.curs.fetchall():
      tag_string = tag_row[0]
      if tag_string:
        tags = tag_string.split(u',')
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
        sql = u'CREATE INDEX {0}_idx ON log2timeline ({0:s})'.format(field_name)
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
      self.curs.execute(
          u'INSERT INTO l2t_tags (tag) VALUES ("{0:s}")'.format(tag))

    if self.set_status:
      self.set_status(u'Database created.')

    self.conn.commit()
    self.curs.close()
    self.conn.close()

  def Open(self):
    """Connects to the database and creates the required tables.

    Raises:
      IOError: If Unable to insert into database.
      ValueError: If no database name given.
    """
    if not self.dbname:
      raise ValueError(u'Missing database name.')

    try:
      if self.append:
        self.conn = MySQLdb.connect(self.host, self.user,
                                    self.password, self.dbname)
        self.curs = self.conn.cursor()

      self.conn.set_character_set(u'utf8')
      self.curs.execute(u'SET NAMES utf8')
      self.curs.execute(u'SET CHARACTER SET utf8')
      self.curs.execute(u'SET character_set_connection=utf8')
      self.curs.execute(u'SET GLOBAL innodb_large_prefix=ON')
      self.curs.execute(u'SET GLOBAL innodb_file_format=barracuda')
      self.curs.execute(u'SET GLOBAL innodb_file_per_table=ON')
      self.curs.execute(
          u'CREATE DATABASE IF NOT EXISTS {0:s}'.format(self.dbname))
      self.curs.execute(u'USE {0:s}'.format(self.dbname))
      # Create tables.
      self.curs.execute(
          (u'CREATE TABLE IF NOT EXISTS log2timeline ('
           u'rowid INT NOT NULL AUTO_INCREMENT, timezone VARCHAR(256), '
           u'MACB VARCHAR(256), source VARCHAR(256), sourcetype VARCHAR(256), '
           u'type VARCHAR(256), user VARCHAR(256), host VARCHAR(256), '
           u'description TEXT, filename VARCHAR(256), inode VARCHAR(256), '
           u'notes VARCHAR(256), format VARCHAR(256), '
           u'extra TEXT, datetime datetime, reportnotes VARCHAR(256), '
           u'inreport VARCHAR(256), tag VARCHAR(256), color VARCHAR(256), '
           u'offset INT, store_number INT, store_index INT, '
           u'vss_store_number INT, URL TEXT, '
           u'record_number VARCHAR(256), event_identifier VARCHAR(256), '
           u'event_type VARCHAR(256), source_name VARCHAR(256), '
           u'user_sid VARCHAR(256), computer_name VARCHAR(256), '
           u'evidence VARCHAR(256), '
           u'PRIMARY KEY (rowid)) ENGINE=InnoDB ROW_FORMAT=COMPRESSED'))
      if self.set_status:
        self.set_status(u'Created table: log2timeline')

      for field in self.META_FIELDS:
        self.curs.execute(
            u'CREATE TABLE IF NOT EXISTS l2t_{0}s ({0}s TEXT, frequency INT) '
            u'ENGINE=InnoDB ROW_FORMAT=COMPRESSED'.format(field))
        if self.set_status:
          self.set_status(u'Created table: l2t_{0:s}'.format(field))

      self.curs.execute(
          u'CREATE TABLE IF NOT EXISTS l2t_tags (tag TEXT) '
          u'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
      if self.set_status:
        self.set_status(u'Created table: l2t_tags')

      self.curs.execute(
          u'CREATE TABLE IF NOT EXISTS l2t_saved_query ('
          u'name TEXT, query TEXT) '
          u'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
      if self.set_status:
        self.set_status(u'Created table: l2t_saved_query')

      self.curs.execute(
          u'CREATE TABLE IF NOT EXISTS l2t_disk ('
          u'disk_type INT, mount_path TEXT, '
          u'dd_path TEXT, dd_offset TEXT, '
          u'storage_file TEXT, export_path TEXT) '
          u'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
      self.curs.execute(
          u'INSERT INTO l2t_disk ('
          u'disk_type, mount_path, dd_path, '
          u'dd_offset, storage_file, '
          u'export_path) VALUES '
          u'(0, "", "", "", "", "")')
      if self.set_status:
        self.set_status(u'Created table: l2t_disk')
    except MySQLdb.Error as exception:
      raise IOError(u'Unable to insert into database with error: {0:s}'.format(
          exception))

    self.count = 0

  def _GetSanitizedEventValues(self, event_object):
    """Formats event output and returns a dictionary.

    Args:
      event_object: the event object (instance of EventObject).

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """

    data_type = getattr(event_object, u'data_type', u'UNKNOWN')
    event_formatter = self._output_mediator.GetEventFormatter(event_object)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    message, _ = self._output_mediator.GetFormattedMessages(event_object)
    if message is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    source_short, source = self._output_mediator.GetFormattedSources(
        event_object)
    if source is None or source_short is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self._output_mediator.timezone)
    if not date_use:
      logging.error(u'Unable to process date for entry: {0:s}'.format(message))
      return

    format_variables = event_formatter.GetFormatStringAttributeNames()
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

    inode = getattr(event_object, u'inode', u'-')
    if inode == u'-':
      if (hasattr(event_object, u'pathspec') and
          hasattr(event_object.pathspec, u'inode')):
        inode = event_object.pathspec.inode

    date_use_string = u'{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(
        date_use.year, date_use.month, date_use.day, date_use.hour,
        date_use.minute, date_use.second)

    if getattr(event_object, u'tag', None):
      tags_value = getattr(event_object.tag, u'tags', None)
    else:
      tags_value = None

    if isinstance(tags_value, (list, tuple)):
      tags = tags_value
    else:
      tags = []

    taglist = u','.join(tags)
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

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    if not hasattr(event_object, u'timestamp'):
      return

    row = self._GetSanitizedEventValues(event_object)
    try:
      self.curs.execute(self.db_insert_string, row)
    except MySQLdb.Error as exception:
      logging.warning(
          u'Unable to insert into database with error: {0:s}.'.format(
              exception))

    self.count += 1

    # TODO: Experiment if committing the current transaction
    # every 10000 inserts is the optimal approach.
    if self.count % 10000 == 0:
      self.conn.commit()
      if self.set_status:
        self.set_status(u'Inserting event: {0:d}'.format(self.count))


manager.OutputManager.RegisterOutput(MySQL4n6OutputModule)
