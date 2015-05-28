# -*- coding: utf-8 -*-
"""This file contains a parser for the Google Drive snapshots.

The Google Drive snapshots are stored in SQLite database files named
snapshot.db.
"""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class GoogleDriveSnapshotCloudEntryEvent(time_events.PosixTimeEvent):
  """Convenience class for a Google Drive snapshot cloud entry."""

  DATA_TYPE = u'gdrive:snapshot:cloud_entry'

  # TODO: this could be moved to the formatter.
  # The following definition for values can be found on Patrick Olson's blog:
  # http://www.sysforensics.org/2012/05/google-drive-forensics-notes.html
  _DOC_TYPES = {
      0: u'FOLDER',
      1: u'FILE',
      2: u'PRESENTATION',
      3: u'UNKNOWN',
      4: u'SPREADSHEET',
      5: u'DRAWING',
      6: u'DOCUMENT',
      7: u'TABLE',
  }

  def __init__(self, posix_time, usage, url, path, size, doc_type, shared):
    """Initializes the event.

    Args:
      posix_time: The POSIX time value.
      usage: The description of the usage of the time value.
      url: The URL of the file as in the cloud.
      path: The path of the file.
      size: The size of the file.
      doc_type: Integer value containing the document type.
      shared: A string indicating whether or not this is a shared document.
    """
    super(GoogleDriveSnapshotCloudEntryEvent, self).__init__(
        posix_time, usage)

    self.url = url
    self.path = path
    self.size = size
    self.document_type = self._DOC_TYPES.get(doc_type, u'UNKNOWN')
    self.shared = shared


class GoogleDriveSnapshotLocalEntryEvent(time_events.PosixTimeEvent):
  """Convenience class for a Google Drive snapshot local entry event."""

  DATA_TYPE = u'gdrive:snapshot:local_entry'

  def __init__(self, posix_time, local_path, size):
    """Initializes the event object.

    Args:
      posix_time: The POSIX time value.
      local_path: The local path of the file.
      size: The size of the file.
    """
    super(GoogleDriveSnapshotLocalEntryEvent, self).__init__(
        posix_time, eventdata.EventTimestamp.MODIFICATION_TIME)

    self.path = local_path
    self.size = size


class GoogleDrivePlugin(interface.SQLitePlugin):
  """SQLite plugin for Google Drive snapshot.db files."""

  NAME = u'google_drive'
  DESCRIPTION = u'Parser for Google Drive SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT e.resource_id, e.filename, e.modified, e.created, e.size, '
        u'e.doc_type, e.shared, e.checksum, e.url, r.parent_resource_id FROM '
        u'cloud_entry AS e, cloud_relations AS r WHERE r.child_resource_id = '
        u'e.resource_id AND e.modified IS NOT NULL;'), u'ParseCloudEntryRow'),
      ((u'SELECT inode_number, filename, modified, checksum, size FROM '
        u'local_entry WHERE modified IS NOT NULL;'), u'ParseLocalEntryRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([
      u'cloud_entry', u'cloud_relations', u'local_entry', u'local_relations',
      u'mapping', u'overlay_status'])

  # Queries used to build cache.
  LOCAL_PATH_CACHE_QUERY = (
      u'SELECT r.child_inode_number, r.parent_inode_number, e.filename FROM '
      u'local_relations AS r, local_entry AS e WHERE r.child_inode_number = '
      u'e.inode_number')
  CLOUD_PATH_CACHE_QUERY = (
      u'SELECT e.filename, e.resource_id, r.parent_resource_id AS parent '
      u'FROM cloud_entry AS e, cloud_relations AS r WHERE e.doc_type = 0 '
      u'AND e.resource_id = r.child_resource_id')

  def GetLocalPath(self, inode, cache, database):
    """Return local path for a given inode.

    Args:
      inode: The inode number for the file.
      cache: A cache object (instance of SQLiteCache).
      database: A database object (instance of SQLiteDatabase).

    Returns:
      A full path, including the filename of the given inode value.
    """
    local_path = cache.GetResults(u'local_path')
    if not local_path:
      cursor = database.cursor
      results = cursor.execute(self.LOCAL_PATH_CACHE_QUERY)

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
      cursor = database.cursor
      results = cursor.execute(self.CLOUD_PATH_CACHE_QUERY)

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
      self, parser_mediator, row, query=None, cache=None, database=None,
      **unused_kwargs):
    """Parses a cloud entry row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
      cache: The local cache object.
      database: The database object.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    cloud_path = self.GetCloudPath(row['parent_resource_id'], cache, database)
    cloud_filename = u'{0:s}{1:s}'.format(cloud_path, row['filename'])

    if row['shared']:
      shared = u'Shared'
    else:
      shared = u'Private'

    event_object = GoogleDriveSnapshotCloudEntryEvent(
        row['modified'], eventdata.EventTimestamp.MODIFICATION_TIME,
        row['url'], cloud_filename, row['size'], row['doc_type'], shared)
    parser_mediator.ProduceEvent(event_object, query=query)

    if row['created']:
      event_object = GoogleDriveSnapshotCloudEntryEvent(
          row['created'], eventdata.EventTimestamp.CREATION_TIME,
          row['url'], cloud_filename, row['size'], row['doc_type'], shared)
      parser_mediator.ProduceEvent(event_object, query=query)

  def ParseLocalEntryRow(
      self, parser_mediator, row, query=None, cache=None, database=None,
      **unused_kwargs):
    """Parses a local entry row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
      cache: The local cache object (instance of SQLiteCache).
      database: A database object (instance of SQLiteDatabase).
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    local_path = self.GetLocalPath(row['inode_number'], cache, database)

    event_object = GoogleDriveSnapshotLocalEntryEvent(
        row['modified'], local_path, row['size'])
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(GoogleDrivePlugin)
