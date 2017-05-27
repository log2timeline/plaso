# -*- coding: utf-8 -*-
"""Parser for the Mac OS X Document Versions files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class MacDocumentVersionsEventData(events.EventData):
  """Mac OS X Document Versions database event data.

  Attributes:
    name (str): name of the original file.
    path (str): path from the original file.
    version_path (str): path to the version copy of the original file.
    last_time (str): the system user ID of the user that opened the file.
    user_sid (str): identification user ID that open the file.
  """

  DATA_TYPE = u'mac:document_versions:file'

  def __init__(self):
    """Initializes event data."""
    super(MacDocumentVersionsEventData, self).__init__(data_type=self.DATA_TYPE)
    # TODO: shouldn't this be a separate event?
    self.last_time = None
    self.name = None
    self.path = None
    self.user_sid = None
    self.version_path = None


class MacDocumentVersionsPlugin(interface.SQLitePlugin):
  """Parse the Mac OS X Document Versions SQLite database.."""

  NAME = u'mac_document_versions'
  DESCRIPTION = u'Parser for document revisions SQLite database files.'

  # Define the needed queries.
  # name: name from the original file.
  # path: path from the original file (include the file)
  # last_time: last time when the file was replicated.
  # version_path: path where the version is stored.
  # version_time: the timestamp when the version was created.
  QUERIES = [
      ((u'SELECT f.file_name AS name, f.file_path AS path, '
        u'f.file_last_seen AS last_time, g.generation_path AS version_path, '
        u'g.generation_add_time AS version_time FROM files f, generations g '
        u'WHERE f.file_storage_id = g.generation_storage_id;'),
       u'DocumentVersionsRow')]

  # The required tables for the query.
  REQUIRED_TABLES = frozenset([u'files', u'generations'])

  SCHEMAS = [{
      u'files': (
          u'CREATE TABLE files (file_row_id INTEGER PRIMARY KEY ASC, file_name '
          u'TEXT, file_parent_id INTEGER, file_path TEXT, file_inode INTEGER, '
          u'file_last_seen INTEGER NOT NULL DEFAULT 0, file_status INTEGER NOT '
          u'NULL DEFAULT 1, file_storage_id INTEGER NOT NULL)'),
      u'generations': (
          u'CREATE TABLE generations (generation_id INTEGER PRIMARY KEY ASC, '
          u'generation_storage_id INTEGER NOT NULL, generation_name TEXT NOT '
          u'NULL, generation_client_id TEXT NOT NULL, generation_path TEXT '
          u'UNIQUE, generation_options INTEGER NOT NULL DEFAULT 1, '
          u'generation_status INTEGER NOT NULL DEFAULT 1, generation_add_time '
          u'INTEGER NOT NULL DEFAULT 0, generation_size INTEGER NOT NULL '
          u'DEFAULT 0, generation_prunable INTEGER NOT NULL DEFAULT 0)'),
      u'storage': (
          u'CREATE TABLE storage (storage_id INTEGER PRIMARY KEY ASC '
          u'AUTOINCREMENT, storage_options INTEGER NOT NULL DEFAULT 1, '
          u'storage_status INTEGER NOT NULL DEFAULT 1)')}]

  # The SQL field path is the relative path from DocumentRevisions.
  # For this reason the Path to the program has to be added at the beginning.
  ROOT_VERSION_PATH = u'/.DocumentRevisions-V100/'

  def DocumentVersionsRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a document versions row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    # version_path = "PerUser/UserID/xx/client_id/version_file"
    # where PerUser and UserID are a real directories.
    paths = row['version_path'].split(u'/')
    if len(paths) < 2 or not paths[1].isdigit():
      user_sid = u''
    else:
      user_sid = paths[1]
    version_path = self.ROOT_VERSION_PATH + row['version_path']
    path, _, _ = row['path'].rpartition(u'/')

    event_data = MacDocumentVersionsEventData()
    # TODO: shouldn't this be a separate event?
    event_data.last_time = row['last_time']
    event_data.name = row['name']
    event_data.path = path
    event_data.query = query
    # Note that the user_sid value is expected to be a string.
    event_data.user_sid = u'{0!s}'.format(user_sid)
    event_data.version_path = version_path

    date_time = dfdatetime_posix_time.PosixTime(timestamp=row['version_time'])
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(MacDocumentVersionsPlugin)
