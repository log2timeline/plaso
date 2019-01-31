# -*- coding: utf-8 -*-
"""Defines the output module for the MySQL database used by 4n6time."""

from __future__ import unicode_literals

try:
  import MySQLdb
except ImportError:
  MySQLdb = None

from plaso.output import logger
from plaso.output import manager
from plaso.output import shared_4n6time


class MySQL4n6TimeOutputModule(shared_4n6time.Shared4n6TimeOutputModule):
  """Class defining the MySQL database output module for 4n6time."""

  NAME = '4n6time_mysql'
  DESCRIPTION = 'MySQL database output for the 4n6time tool.'

  _META_FIELDS = frozenset([
      'sourcetype', 'source', 'user', 'host', 'MACB', 'type',
      'record_number'])

  _CREATE_TABLE_QUERY = (
      'CREATE TABLE IF NOT EXISTS log2timeline ('
      'rowid INT NOT NULL AUTO_INCREMENT, timezone VARCHAR(256), '
      'MACB VARCHAR(256), source VARCHAR(256), sourcetype VARCHAR(256), '
      'type VARCHAR(256), user VARCHAR(256), host VARCHAR(256), '
      'description TEXT, filename VARCHAR(256), inode VARCHAR(256), '
      'notes VARCHAR(256), format VARCHAR(256), '
      'extra TEXT, datetime datetime, reportnotes VARCHAR(256), '
      'inreport VARCHAR(256), tag VARCHAR(256), offset INT, '
      'vss_store_number INT, URL TEXT, record_number VARCHAR(256), '
      'event_identifier VARCHAR(256), event_type VARCHAR(256), '
      'source_name VARCHAR(256), user_sid VARCHAR(256), '
      'computer_name VARCHAR(256), evidence VARCHAR(256), '
      'PRIMARY KEY (rowid)) ENGINE=InnoDB ROW_FORMAT=COMPRESSED')

  _INSERT_QUERY = (
      'INSERT INTO log2timeline(timezone, MACB, source, '
      'sourcetype, type, user, host, description, filename, '
      'inode, notes, format, extra, datetime, reportnotes, inreport, '
      'tag, offset, vss_store_number, URL, record_number, '
      'event_identifier, event_type, source_name, user_sid, computer_name, '
      'evidence) '
      'VALUES (:timezone, :MACB, :source, :sourcetype, :type, :user, :host, '
      ':description, :filename, :inode, :notes, :format, :extra, :datetime, '
      ':reportnotes, :inreport, :tag, :offset, :vss_store_number, :URL, '
      ':record_number, :event_identifier, :event_type, :source_name, '
      ':user_sid, :computer_name, :evidence)')

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    super(MySQL4n6TimeOutputModule, self).__init__(output_mediator)
    self._connection = None
    self._count = None
    self._cursor = None
    self._dbname = 'log2timeline'
    self._host = 'localhost'
    self._password = 'forensic'
    self._port = None
    self._user = 'root'

  def _GetTags(self):
    """Retrieves tags from the database.

    Returns:
      list[str]: tags.
    """
    all_tags = []
    self._cursor.execute('SELECT DISTINCT tag FROM log2timeline')

    # This cleans up the messy SQL return.
    tag_row = self._cursor.fetchone()
    while tag_row:
      tag_string = tag_row[0]
      if tag_string:
        tags = tag_string.split(',')
        for tag in tags:
          if tag not in all_tags:
            all_tags.append(tag)
      tag_row = self._cursor.fetchone()

    # TODO: make this method an iterator.
    return all_tags

  def _GetUniqueValues(self, field_name):
    """Retrieves the unique values of a specific field from the database.

    Args:
      field_name (str): name of the field.

    Returns:
      dict[str, int]: number of instances of the field value per field name.
    """
    self._cursor.execute(
        'SELECT {0:s}, COUNT({0:s}) FROM log2timeline GROUP BY {0:s}'.format(
            field_name))

    result = {}
    row = self._cursor.fetchone()
    while row:
      if row[0]:
        result[row[0]] = row[1]

      row = self._cursor.fetchone()

    return result

  def Close(self):
    """Disconnects from the database.

    This method will create the necessary indices and commit outstanding
    transactions before disconnecting.
    """
    # Build up indices for the fields specified in the args.
    # It will commit the inserts automatically before creating index.
    if not self._append:
      for field_name in self._fields:
        query = 'CREATE INDEX {0:s}_idx ON log2timeline ({0:s})'.format(
            field_name)
        self._cursor.execute(query)
        if self._set_status:
          self._set_status('Created index: {0:s}'.format(field_name))

    # Get meta info and save into their tables.
    if self._set_status:
      self._set_status('Creating metadata...')

    for field in self._META_FIELDS:
      values = self._GetUniqueValues(field)
      self._cursor.execute('DELETE FROM l2t_{0:s}s'.format(field))
      for name, frequency in iter(values.items()):
        self._cursor.execute((
            'INSERT INTO l2t_{0:s}s ({0:s}s, frequency) '
            'VALUES("{1:s}", {2:d}) ').format(field, name, frequency))

    self._cursor.execute('DELETE FROM l2t_tags')
    for tag in self._GetTags():
      self._cursor.execute(
          'INSERT INTO l2t_tags (tag) VALUES ("{0:s}")'.format(tag))

    if self._set_status:
      self._set_status('Database created.')

    self._connection.commit()
    self._cursor.close()
    self._connection.close()

    self._cursor = None
    self._connection = None

  def Open(self):
    """Connects to the database and creates the required tables.

    Raises:
      IOError: if the 4n6time tables cannot be created or data not inserted
          in the database.
      OSError: if the 4n6time tables cannot be created or data not inserted
          in the database.
      ValueError: if no database name given.
    """
    if not self._dbname:
      raise ValueError('Missing database name.')

    try:
      if self._append:
        self._connection = MySQLdb.connect(
            self._host, self._user, self._password, self._dbname)
        self._cursor = self._connection.cursor()

      self._connection.set_character_set('utf8')
      self._cursor.execute('SET NAMES utf8')
      self._cursor.execute('SET CHARACTER SET utf8')
      self._cursor.execute('SET character_set_connection=utf8')
      self._cursor.execute('SET GLOBAL innodb_large_prefix=ON')
      self._cursor.execute('SET GLOBAL innodb_file_format=barracuda')
      self._cursor.execute('SET GLOBAL innodb_file_per_table=ON')
      self._cursor.execute(
          'CREATE DATABASE IF NOT EXISTS {0:s}'.format(self._dbname))
      self._cursor.execute('USE {0:s}'.format(self._dbname))
      # Create tables.
      self._cursor.execute(self._CREATE_TABLE_QUERY)
      if self._set_status:
        self._set_status('Created table: log2timeline')

      for field in self._META_FIELDS:
        self._cursor.execute(
            'CREATE TABLE IF NOT EXISTS l2t_{0}s ({0}s TEXT, frequency INT) '
            'ENGINE=InnoDB ROW_FORMAT=COMPRESSED'.format(field))
        if self._set_status:
          self._set_status('Created table: l2t_{0:s}'.format(field))

      self._cursor.execute(
          'CREATE TABLE IF NOT EXISTS l2t_tags (tag TEXT) '
          'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
      if self._set_status:
        self._set_status('Created table: l2t_tags')

      self._cursor.execute(
          'CREATE TABLE IF NOT EXISTS l2t_saved_query ('
          'name TEXT, query TEXT) '
          'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
      if self._set_status:
        self._set_status('Created table: l2t_saved_query')

      self._cursor.execute(
          'CREATE TABLE IF NOT EXISTS l2t_disk ('
          'disk_type INT, mount_path TEXT, '
          'dd_path TEXT, dd_offset TEXT, '
          'storage_file TEXT, export_path TEXT) '
          'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
      self._cursor.execute(
          'INSERT INTO l2t_disk ('
          'disk_type, mount_path, dd_path, '
          'dd_offset, storage_file, '
          'export_path) VALUES '
          '(0, "", "", "", "", "")')
      if self._set_status:
        self._set_status('Created table: l2t_disk')
    except MySQLdb.Error as exception:
      raise IOError('Unable to insert into database with error: {0!s}'.format(
          exception))

    self._count = 0

  def SetCredentials(self, password=None, username=None):
    """Sets the database credentials.

    Args:
      password (Optional[str]): password to access the database.
      username (Optional[str]): username to access the database.
    """
    if password:
      self._password = password
    if username:
      self._user = username

  def SetDatabaseName(self, name):
    """Sets the database name.

    Args:
      name (str): name of the database.
    """
    self._dbname = name

  def SetServerInformation(self, server, port):
    """Sets the server information.

    Args:
      server (str): hostname or IP address of the database server.
      port (int): port number of the database server.
    """
    self._host = server
    self._port = port

  def WriteEventBody(self, event):
    """Writes the body of an event object to the output.

    Args:
      event (EventObject): event.
    """
    if not hasattr(event, 'timestamp'):
      return

    row = self._GetSanitizedEventValues(event)
    try:
      self._cursor.execute(self._INSERT_QUERY, row)
    except MySQLdb.Error as exception:
      logger.warning(
          'Unable to insert into database with error: {0!s}.'.format(
              exception))

    self._count += 1

    # TODO: Experiment if committing the current transaction
    # every 10000 inserts is the optimal approach.
    if self._count % 10000 == 0:
      self._connection.commit()
      if self._set_status:
        self._set_status('Inserting event: {0:d}'.format(self._count))


manager.OutputManager.RegisterOutput(
    MySQL4n6TimeOutputModule, disabled=MySQLdb is None)
