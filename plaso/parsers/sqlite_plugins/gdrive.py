# -*- coding: utf-8 -*-
"""This file contains a parser for the Google Drive snapshots.

The Google Drive snapshots are stored in SQLite database files named
snapshot.db.
"""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class GoogleDriveSnapshotCloudEntryEventData(events.EventData):
  """Google Drive snapshot cloud entry event data.

  Attributes:
    doc_type (int): document type.
    path (str): path of the file.
    shared (bool): True if the file is shared, False if the file is private.
    size (int): size of the file.
    url (str): URL of the file.
  """

  DATA_TYPE = u'gdrive:snapshot:cloud_entry'

  def __init__(self):
    """Initializes event data."""
    super(GoogleDriveSnapshotCloudEntryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.document_type = None
    self.path = None
    self.shared = None
    self.size = None
    self.url = None


class GoogleDriveSnapshotLocalEntryEventData(events.EventData):
  """Google Drive snapshot local entry event data.

  Attributes:
    path (str): path of the file.
    size (int): size of the file.
  """

  DATA_TYPE = u'gdrive:snapshot:local_entry'

  def __init__(self):
    """Initializes event data."""
    super(GoogleDriveSnapshotLocalEntryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.path = None
    self.size = None


class GoogleDrivePlugin(interface.SQLitePlugin):
  """SQLite plugin for Google Drive snapshot.db files."""

  NAME = u'google_drive'
  DESCRIPTION = u'Parser for Google Drive SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT cloud_entry.resource_id, cloud_entry.filename, '
        u'cloud_entry.modified, cloud_entry.created, cloud_entry.size, '
        u'cloud_entry.doc_type, cloud_entry.shared, cloud_entry.checksum, '
        u'cloud_entry.url, cloud_relations.parent_resource_id '
        u'FROM cloud_entry, cloud_relations '
        u'WHERE cloud_relations.child_resource_id = cloud_entry.resource_id '
        u'AND cloud_entry.modified IS NOT NULL;'),
       u'ParseCloudEntryRow'),
      ((u'SELECT inode_number, filename, modified, checksum, size '
        u'FROM local_entry WHERE modified IS NOT NULL;'),
       u'ParseLocalEntryRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([
      u'cloud_entry', u'cloud_relations', u'local_entry', u'local_relations',
      u'mapping', u'overlay_status'])

  SCHEMAS = [{
      u'cloud_entry': (
          u'CREATE TABLE cloud_entry (resource_id TEXT, filename TEXT, '
          u'modified INTEGER, created INTEGER, acl_role INTEGER, doc_type '
          u'INTEGER, removed INTEGER, url TEXT, size INTEGER, checksum TEXT, '
          u'shared INTEGER, PRIMARY KEY (resource_id))'),
      u'cloud_relations': (
          u'CREATE TABLE cloud_relations (child_resource_id TEXT, '
          u'parent_resource_id TEXT, UNIQUE (child_resource_id, '
          u'parent_resource_id), FOREIGN KEY (child_resource_id) REFERENCES '
          u'cloud_entry(resource_id), FOREIGN KEY (parent_resource_id) '
          u'REFERENCES cloud_entry(resource_id))'),
      u'local_entry': (
          u'CREATE TABLE local_entry (inode_number INTEGER, filename TEXT, '
          u'modified INTEGER, checksum TEXT, size INTEGER, PRIMARY KEY '
          u'(inode_number))'),
      u'local_relations': (
          u'CREATE TABLE local_relations (child_inode_number INTEGER, '
          u'parent_inode_number INTEGER, UNIQUE (child_inode_number), FOREIGN '
          u'KEY (parent_inode_number) REFERENCES local_entry(inode_number), '
          u'FOREIGN KEY (child_inode_number) REFERENCES '
          u'local_entry(inode_number))'),
      u'mapping': (
          u'CREATE TABLE mapping (inode_number INTEGER, resource_id TEXT, '
          u'UNIQUE (inode_number), FOREIGN KEY (inode_number) REFERENCES '
          u'local_entry(inode_number), FOREIGN KEY (resource_id) REFERENCES '
          u'cloud_entry(resource_id))'),
      u'overlay_status': (
          u'CREATE TABLE overlay_status (path TEXT, overlay_status INTEGER, '
          u'PRIMARY KEY (path))')}]

  # Queries used to build cache.
  LOCAL_PATH_CACHE_QUERY = (
      u'SELECT local_relations.child_inode_number, '
      u'local_relations.parent_inode_number, local_entry.filename '
      u'FROM local_relations, local_entry '
      u'WHERE local_relations.child_inode_number = local_entry.inode_number')
  CLOUD_PATH_CACHE_QUERY = (
      u'SELECT cloud_entry.filename, cloud_entry.resource_id, '
      u'cloud_relations.parent_resource_id AS parent '
      u'FROM cloud_entry, cloud_relations '
      u'WHERE cloud_entry.doc_type = 0 '
      u'AND cloud_entry.resource_id = cloud_relations.child_resource_id')

  def GetLocalPath(self, inode, cache, database):
    """Return local path for a given inode.

    Args:
      inode: The inode number for the file.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.

    Returns:
      A full path, including the filename of the given inode value.
    """
    local_path = cache.GetResults(u'local_path')
    if not local_path:
      results = database.Query(self.LOCAL_PATH_CACHE_QUERY)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      cache.CacheQueryResults(
          results, 'local_path', 'child_inode_number',
          ('parent_inode_number', 'filename'))
      local_path = cache.GetResults(u'local_path')

    parent, path = local_path.get(inode, [None, None])

    # TODO: Read the local_sync_root from the sync_config.db and use that
    # for a root value.
    root_value = u'%local_sync_root%/'

    if not path:
      return root_value

    paths = []
    while path:
      paths.append(path)
      parent, path = local_path.get(parent, [None, None])

    if not paths:
      return root_value

    # Paths are built top level to root so we need to reverse the list to
    # represent them in the traditional order.
    paths.reverse()
    return root_value + u'/'.join(paths)

  def GetCloudPath(self, resource_id, cache, database):
    """Return cloud path given a resource id.

    Args:
      resource_id: The resource_id for the file.
      cache: The local cache object.
      database: A database object (instance of SQLiteDatabase).

    Returns:
      A full path to the resource value.
    """
    cloud_path = cache.GetResults(u'cloud_path')
    if not cloud_path:
      results = database.Query(self.CLOUD_PATH_CACHE_QUERY)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      cache.CacheQueryResults(
          results, 'cloud_path', 'resource_id', ('filename', 'parent'))
      cloud_path = cache.GetResults(u'cloud_path')

    if resource_id == u'folder:root':
      return u'/'

    paths = []
    parent_path, parent_id = cloud_path.get(resource_id, [u'', u''])
    while parent_path:
      if parent_path == u'folder:root':
        break
      paths.append(parent_path)
      parent_path, parent_id = cloud_path.get(parent_id, [u'', u''])

    if not paths:
      return u'/'

    # Paths are built top level to root so we need to reverse the list to
    # represent them in the traditional order.
    paths.reverse()
    return u'/{0:s}/'.format(u'/'.join(paths))

  def ParseCloudEntryRow(
      self, parser_mediator, row, cache=None, database=None, query=None,
      **unused_kwargs):
    """Parses a cloud entry row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    cloud_path = self.GetCloudPath(row['parent_resource_id'], cache, database)
    cloud_filename = u'{0:s}{1:s}'.format(cloud_path, row['filename'])

    event_data = GoogleDriveSnapshotCloudEntryEventData()
    event_data.document_type = row['doc_type']
    event_data.path = cloud_filename
    event_data.query = query
    event_data.shared = bool(row['shared'])
    event_data.size = row['size']
    event_data.url = row['url']

    date_time = dfdatetime_posix_time.PosixTime(timestamp=row['modified'])
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    if row['created']:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=row['created'])
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseLocalEntryRow(
      self, parser_mediator, row, cache=None, database=None, query=None,
      **unused_kwargs):
    """Parses a local entry row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    local_path = self.GetLocalPath(row['inode_number'], cache, database)

    event_data = GoogleDriveSnapshotLocalEntryEventData()
    event_data.path = local_path
    event_data.query = query
    event_data.size = row['size']

    date_time = dfdatetime_posix_time.PosixTime(timestamp=row['modified'])
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(GoogleDrivePlugin)
