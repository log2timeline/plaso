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
"""This file contains a parser for the Google Drive snaphots.

The Google Drive snapshots are stored in SQLite database files named
snapshot.db.
"""

from plaso.events import time_events
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class GoogleDriveSnapshotCloudEntryEvent(time_events.PosixTimeEvent):
  """Convenience class for a Google Drive snapshot cloud entry."""

  DATA_TYPE = 'gdrive:snapshot:cloud_entry'

  # TODO: this could be moved to the formatter.
  # The following definition for values can be found on Patrick Olson's blog:
  # http://www.sysforensics.org/2012/05/google-drive-forensics-notes.html
  _DOC_TYPES = {
      0: 'FOLDER',
      1: 'FILE',
      2: 'PRESENTATION',
      3: 'UNKNOWN',
      4: 'SPREADSHEET',
      5: 'DRAWING',
      6: 'DOCUMENT',
      7: 'TABLE',
  }
  _DOC_TYPES.setdefault('UNKNOWN')

  def __init__(self, timestamp, usage, url, path, size, doc_type, shared):
    """Initializes the event.

    Args:
      timestamp: The POSIX timestamp value.
      usage: The usage string of the timestamp.
      url: The URL of the file as in the cloud.
      path: The path of the file.
      size: The size of the file.
      doc_type: Integer value containing the document type.
      shared: A string indicating whether or not this is a shared document.
    """
    super(GoogleDriveSnapshotCloudEntryEvent, self).__init__(
        timestamp, usage)

    self.url = url
    self.path = path
    self.size = size
    self.document_type = self._DOC_TYPES.get(doc_type, 'UNKNOWN')
    self.shared = shared


class GoogleDriveSnapshotLocalEntryEvent(event.EventObject):
  """Convenience class for a Google Drive snapshot local entry event."""

  DATA_TYPE = 'gdrive:snapshot:local_entry'

  def __init__(self, timestamp, local_path, size):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of seconds since Jan 1, 1970 00:00:00 UTC.
      local_path: The local path of the file.
      size: The size of the file.
    """
    super(GoogleDriveSnapshotLocalEntryEvent, self).__init__()

    self.timestamp = timelib.Timestamp.FromPosixTime(timestamp)
    self.timestamp_desc = eventdata.EventTimestamp.MODIFICATION_TIME

    self.path = local_path
    self.size = size


class GoogleDrivePlugin(interface.SQLitePlugin):
  """SQLite lugin for Google Drive snapshot.db files."""

  NAME = 'google_drive'

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT e.resource_id, e.filename, e.modified, e.created, e.size, '
        u'e.doc_type, e.shared, e.checksum, e.url, r.parent_resource_id FROM '
        u'cloud_entry AS e, cloud_relations AS r WHERE r.child_resource_id = '
        u'e.resource_id AND e.modified IS NOT NULL;'), 'ParseCloudEntryRow'),
      ((u'SELECT inode_number, filename, modified, checksum, size FROM '
        u'local_entry WHERE modified IS NOT NULL;'), 'ParseLocalEntryRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([
      'cloud_entry', 'cloud_relations', 'local_entry', 'local_relations',
      'mapping', 'overlay_status'])

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
    local_path = cache.GetResults('local_path')
    if not local_path:
      cursor = database.cursor
      results = cursor.execute(self.LOCAL_PATH_CACHE_QUERY)
      cache.CacheQueryResults(
          results, 'local_path', 'child_inode_number',
          ('parent_inode_number', 'filename'))
      local_path = cache.GetResults('local_path')

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
    cloud_path = cache.GetResults('cloud_path')
    if not cloud_path:
      cursor = database.cursor
      results = cursor.execute(self.CLOUD_PATH_CACHE_QUERY)
      cache.CacheQueryResults(
          results, 'cloud_path', 'resource_id', ('filename', 'parent'))
      cloud_path = cache.GetResults('cloud_path')

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
    return u'/' + u'/'.join(paths) + u'/'

  def ParseCloudEntryRow(self, row, cache, database, **unused_kwargs):
    """Parses a cloud entry row.

    Args:
      row: The row resulting from the query.
      cache: The local cache object.

    Yields:
      An event object (instance of GoogleDriveSnapshotCloudEntryEvent)
      containing the event data.
    """
    cloud_path = self.GetCloudPath(row['parent_resource_id'], cache, database)
    cloud_filename = u'{}{}'.format(cloud_path, row['filename'])

    if row['shared']:
      shared = 'Shared'
    else:
      shared = 'Private'

    yield GoogleDriveSnapshotCloudEntryEvent(
        row['modified'], eventdata.EventTimestamp.MODIFICATION_TIME,
        row['url'], cloud_filename, row['size'], row['doc_type'], shared)

    if row['created']:
      yield GoogleDriveSnapshotCloudEntryEvent(
          row['created'], eventdata.EventTimestamp.CREATION_TIME,
          row['url'], cloud_filename, row['size'], row['doc_type'], shared)

  def ParseLocalEntryRow(self, row, cache, database, **unused_kwargs):
    """Parses a local entry row.

    Args:
      row: The row resulting from the query.
      cache: The local cache object (instance of SQLiteCache).
      database: A database object (instance of SQLiteDatabase).

    Yields:
      An event object (GoogleDriveSnapshotLocalEntryEvent) containing
      the event data.
    """
    local_path = self.GetLocalPath(row['inode_number'], cache, database)

    yield GoogleDriveSnapshotLocalEntryEvent(
        row['modified'], local_path, row['size'])
