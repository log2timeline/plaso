# -*- coding: utf-8 -*-
"""Defines the output module for the MySQL database used by 4n6time."""

# TODO: Add a unit test for this output module.

import logging

import MySQLdb

from plaso import formatters
from plaso.formatters import interface as formatters_interface
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import helper
from plaso.output import interface
from plaso.output import manager


__author__ = 'David Nides (david.nides@gmail.com)'


class MySQL4n6OutputModule(interface.OutputModule):
  """Class defining the MySQL database output module for 4n6time."""

  NAME = 'mysql4n6'
  DESCRIPTION = u'MySQL database output for the 4n6time tool.'

  META_FIELDS = frozenset([
      'sourcetype', 'source', 'user', 'host', 'MACB', 'color', 'type',
      'record_number'])

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

  def _GetDistinctValues(self, field_name):
    """Query database for unique field types.

    Args:
      field_name: name of the filed to retrieve.
    """
    self.curs.execute(
        u'SELECT {0}, COUNT({0}) FROM log2timeline GROUP BY {0}'.format(
            field_name))
    res = {}
    for row in self.curs.fetchall():
      if row[0] != '':
        res[row[0]] = int(row[1])
    return res

  def _ListTags(self):
    """Query database for unique tag types."""
    all_tags = []
    self.curs.execute(
        u'SELECT DISTINCT tag FROM log2timeline')

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
    """Connects to the database and creates the required tables."""
    if self.dbname == '':
      raise IOError(u'Specify a database name.')

    try:
      if self.append:
        self.conn = MySQLdb.connect(self.host, self.user,
                                    self.password, self.dbname)
        self.curs = self.conn.cursor()
      else:
        self.conn = MySQLdb.connect(self.host, self.user, self.password)
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

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).

    Raises:
      raise errors.NoFormatterFound: If no formatter for this event is found.
    """
    if not hasattr(event_object, u'timestamp'):
      return

    # TODO: remove this hack part of the storage/output refactor.
    # The event formatter class constants should not be changed directly.
    event_formatter = self._output_mediator.GetEventFormatter(event_object)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to output event, no event formatter found.')

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

    msg, _ = self._output_mediator.GetFormattedMessages(event_object)
    source_short, source_long = self._output_mediator.GetFormattedSources(
        event_object)

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self._output_mediator.timezone)
    if not date_use:
      logging.error(u'Unable to process date for entry: {0:s}'.format(msg))
      return
    extra = []
    format_variables = event_formatter.GetFormatStringAttributeNames()
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

    date_use_string = u'{0:d}-{1:d}-{2:d} {3:d}:{4:d}:{5:d}'.format(
        date_use.year, date_use.month, date_use.day, date_use.hour,
        date_use.minute, date_use.second)

    tags = []
    if hasattr(event_object, 'tag') and hasattr(event_object.tag, 'tags'):
      tags = event_object.tag.tags
    else:
      tags = u''

    taglist = u','.join(tags)
    row = (
        str(self._output_mediator.timezone),
        helper.GetLegacy(event_object),
        source_short,
        source_long,
        getattr(event_object, 'timestamp_desc', '-'),
        getattr(event_object, 'username', '-'),
        getattr(event_object, 'hostname', '-'),
        msg,
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
        self.GetVSSNumber(event_object),
        getattr(event_object, 'url', '-'),
        getattr(event_object, 'record_number', 0),
        getattr(event_object, 'event_identifier', '-'),
        getattr(event_object, 'event_type', '-'),
        getattr(event_object, 'source_name', '-'),
        getattr(event_object, 'user_sid', '-'),
        getattr(event_object, 'computer_name', '-'),
        self.evidence)

    try:
      self.curs.execute(
          'INSERT INTO log2timeline(timezone, MACB, source, '
          'sourcetype, type, user, host, description, filename, '
          'inode, notes, format, extra, datetime, reportnotes, '
          'inreport, tag, color, offset, store_number, '
          'store_index, vss_store_number, URL, record_number, '
          'event_identifier, event_type, source_name, user_sid, '
          'computer_name, evidence) VALUES ('
          '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '
          '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '
          '%s, %s, %s, %s)', row)
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

  def GetVSSNumber(self, event_object):
    """Return the vss_store_number of the event."""
    if not hasattr(event_object, 'pathspec'):
      return -1

    return getattr(event_object.pathspec, 'vss_store_number', -1)


manager.OutputManager.RegisterOutput(MySQL4n6OutputModule)
