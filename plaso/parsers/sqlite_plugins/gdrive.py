# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google Drive snapshot database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class GoogleDriveSnapshotCloudEntryEventData(events.EventData):
  """Google Drive snapshot cloud entry event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): date and time the snapshot cloud
        entry was created.
    doc_type (int): document type.
    modification_time (dfdatetime.DateTimeValues): date and time the snapshot
        cloud entry was last modified.
    path (str): path of the file.
    query (str): SQL query that was used to obtain the event data.
    shared (bool): True if the file is shared, False if the file is private.
    size (int): size of the file.
    url (str): URL of the file.
  """

  DATA_TYPE = 'gdrive:snapshot:cloud_entry'

  def __init__(self):
    """Initializes event data."""
    super(GoogleDriveSnapshotCloudEntryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.creation_time = None
    self.document_type = None
    self.modification_time = None
    self.path = None
    self.query = None
    self.shared = None
    self.size = None
    self.url = None


class GoogleDriveSnapshotLocalEntryEventData(events.EventData):
  """Google Drive snapshot local entry event data.

  Attributes:
    modification_time (dfdatetime.DateTimeValues): date and time the snapshot
        local entry was last modified.
    path (str): path of the file.
    query (str): SQL query that was used to obtain the event data.
    size (int): size of the file.
  """

  DATA_TYPE = 'gdrive:snapshot:local_entry'

  def __init__(self):
    """Initializes event data."""
    super(GoogleDriveSnapshotLocalEntryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.modification_time = None
    self.path = None
    self.query = None
    self.size = None


class GoogleDrivePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Google Drive snapshot database files.

  The Google Drive snapshot database file is typically stored in:
  snapshot.db
  """

  NAME = 'google_drive'
  DATA_FORMAT = 'Google Drive snapshot SQLite database (snapshot.db) file'

  REQUIRED_STRUCTURE = {
      'cloud_entry': frozenset([
          'resource_id', 'filename', 'modified', 'created', 'size', 'doc_type',
          'shared', 'checksum', 'url']),
      'cloud_relations': frozenset([
          'parent_resource_id', 'child_resource_id']),
      'local_entry': frozenset([
          'inode_number', 'filename', 'modified', 'checksum', 'size']),
      'local_relations': frozenset([
          'child_inode_number', 'parent_inode_number'])}

  QUERIES = [
      (('SELECT cloud_entry.resource_id, cloud_entry.filename, '
        'cloud_entry.modified, cloud_entry.created, cloud_entry.size, '
        'cloud_entry.doc_type, cloud_entry.shared, cloud_entry.checksum, '
        'cloud_entry.url, cloud_relations.parent_resource_id '
        'FROM cloud_entry, cloud_relations '
        'WHERE cloud_relations.child_resource_id = cloud_entry.resource_id '
        'AND cloud_entry.modified IS NOT NULL;'),
       'ParseCloudEntryRow'),
      (('SELECT inode_number, filename, modified, checksum, size '
        'FROM local_entry WHERE modified IS NOT NULL;'),
       'ParseLocalEntryRow')]

  SCHEMAS = [{
      'cloud_entry': (
          'CREATE TABLE cloud_entry (resource_id TEXT, filename TEXT, '
          'modified INTEGER, created INTEGER, acl_role INTEGER, doc_type '
          'INTEGER, removed INTEGER, url TEXT, size INTEGER, checksum TEXT, '
          'shared INTEGER, PRIMARY KEY (resource_id))'),
      'cloud_relations': (
          'CREATE TABLE cloud_relations (child_resource_id TEXT, '
          'parent_resource_id TEXT, UNIQUE (child_resource_id, '
          'parent_resource_id), FOREIGN KEY (child_resource_id) REFERENCES '
          'cloud_entry(resource_id), FOREIGN KEY (parent_resource_id) '
          'REFERENCES cloud_entry(resource_id))'),
      'local_entry': (
          'CREATE TABLE local_entry (inode_number INTEGER, filename TEXT, '
          'modified INTEGER, checksum TEXT, size INTEGER, PRIMARY KEY '
          '(inode_number))'),
      'local_relations': (
          'CREATE TABLE local_relations (child_inode_number INTEGER, '
          'parent_inode_number INTEGER, UNIQUE (child_inode_number), FOREIGN '
          'KEY (parent_inode_number) REFERENCES local_entry(inode_number), '
          'FOREIGN KEY (child_inode_number) REFERENCES '
          'local_entry(inode_number))'),
      'mapping': (
          'CREATE TABLE mapping (inode_number INTEGER, resource_id TEXT, '
          'UNIQUE (inode_number), FOREIGN KEY (inode_number) REFERENCES '
          'local_entry(inode_number), FOREIGN KEY (resource_id) REFERENCES '
          'cloud_entry(resource_id))'),
      'overlay_status': (
          'CREATE TABLE overlay_status (path TEXT, overlay_status INTEGER, '
          'PRIMARY KEY (path))')}]

  # Queries used to build cache.
  LOCAL_PATH_CACHE_QUERY = (
      'SELECT local_relations.child_inode_number, '
      'local_relations.parent_inode_number, local_entry.filename '
      'FROM local_relations, local_entry '
      'WHERE local_relations.child_inode_number = local_entry.inode_number')
  CLOUD_PATH_CACHE_QUERY = (
      'SELECT cloud_entry.filename, cloud_entry.resource_id, '
      'cloud_relations.parent_resource_id AS parent '
      'FROM cloud_entry, cloud_relations '
      'WHERE cloud_entry.doc_type = 0 '
      'AND cloud_entry.resource_id = cloud_relations.child_resource_id')

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  def GetLocalPath(self, inode, cache, database):
    """Return local path for a given inode.

    Args:
      inode (int): inode number for the file.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.

    Returns:
      str: full path, including the filename of the given inode value.
    """
    local_path = cache.GetResults('local_path')
    if not local_path:
      results = database.Query(self.LOCAL_PATH_CACHE_QUERY)

      cache.CacheQueryResults(
          results, 'local_path', 'child_inode_number',
          ('parent_inode_number', 'filename'))
      local_path = cache.GetResults('local_path')

    parent, path = local_path.get(inode, [None, None])

    # TODO: Read the local_sync_root from the sync_config.db and use that
    # for a root value.
    root_value = '%local_sync_root%/'

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
    return root_value + '/'.join(paths)

  def GetCloudPath(self, resource_id, cache, database):
    """Return cloud path given a resource id.

    Args:
      resource_id (str): resource identifier for the file.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.

    Returns:
      str: full path to the resource value.
    """
    cloud_path = cache.GetResults('cloud_path')
    if not cloud_path:
      results = database.Query(self.CLOUD_PATH_CACHE_QUERY)

      cache.CacheQueryResults(
          results, 'cloud_path', 'resource_id', ('filename', 'parent'))
      cloud_path = cache.GetResults('cloud_path')

    if resource_id == 'folder:root':
      return '/'

    paths = []
    parent_path, parent_id = cloud_path.get(resource_id, ['', ''])
    while parent_path:
      if parent_path == 'folder:root':
        break
      paths.append(parent_path)
      parent_path, parent_id = cloud_path.get(parent_id, ['', ''])

    if not paths:
      return '/'

    # Paths are built top level to root so we need to reverse the list to
    # represent them in the traditional order.
    paths.reverse()
    return '/{0:s}/'.format('/'.join(paths))

  def ParseCloudEntryRow(
      self, parser_mediator, query, row, cache=None, database=None,
      **unused_kwargs):
    """Parses a cloud entry row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.
    """
    query_hash = hash(query)

    parent_resource_id = self._GetRowValue(
        query_hash, row, 'parent_resource_id')

    cloud_path = self.GetCloudPath(parent_resource_id, cache, database)
    filename = self._GetRowValue(query_hash, row, 'filename')

    event_data = GoogleDriveSnapshotCloudEntryEventData()
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'created')
    event_data.document_type = self._GetRowValue(query_hash, row, 'doc_type')
    event_data.modification_time = self._GetDateTimeRowValue(
        query_hash, row, 'modified')
    event_data.path = ''.join([cloud_path, filename])
    event_data.query = query
    event_data.shared = bool(self._GetRowValue(query_hash, row, 'shared'))
    event_data.size = self._GetRowValue(query_hash, row, 'size')
    event_data.url = self._GetRowValue(query_hash, row, 'url')

    parser_mediator.ProduceEventData(event_data)

  def ParseLocalEntryRow(
      self, parser_mediator, query, row, cache=None, database=None,
      **unused_kwargs):
    """Parses a local entry row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
      cache (Optional[SQLiteCache]): cache.
      database (Optional[SQLiteDatabase]): database.
    """
    query_hash = hash(query)

    inode_number = self._GetRowValue(query_hash, row, 'inode_number')
    local_path = self.GetLocalPath(inode_number, cache, database)

    event_data = GoogleDriveSnapshotLocalEntryEventData()
    event_data.modification_time = self._GetDateTimeRowValue(
        query_hash, row, 'modified')
    event_data.path = local_path
    event_data.query = query
    event_data.size = self._GetRowValue(query_hash, row, 'size')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(GoogleDrivePlugin)
