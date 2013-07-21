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
# Shut up pylint
# * R0924: Badly implemented Container
# pylint: disable=R0924

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib

__author__ = 'David Nides (david.nides@gmail.com)'


# TODO: Add tests: gdrive_test.py.
class GoogleDriveSnapshotCloudEntryEventContainer(event.EventContainer):
  """Convenience class for a Google Drive snapshot cloud entry container."""

  # TODO: this could be moved to the formatter.
  # The following definition for values can be found on Patrick Olson's blog:
  # http://www.sysforensics.org/2012/05/google-drive-forensics-notes.html
  _DOC_TYPES = {
      '0': 'FOLDER',
      '1': 'FILE',
      '2': 'PRESENTATION',
      '3': 'UNKNOWN',
      '4': 'SPREADSHEET',
      '5': 'DRAWING',
      '6': 'DOCUMENT',
      '7': 'TABLE',
  }
  _DOC_TYPES.setdefault('UNKNOWN')

  # TODO: check these descriptions. E.g. path is relative to what? local or
  # inside GDrive.
  def __init__(self, url, path, size, doc_type):
    """Initializes the event container.

    Args:
      url: The URL of the file as in the cloud.
      path: The path of the file.
      size: The size of the file.
      doc_type: Integer value containing the document type.
    """
    super(GoogleDriveSnapshotCloudEntryEventContainer, self).__init__()

    # TODO: refactor to formatter.
    self.data_type = 'gdrive:snapshot:cloud_entry'

    self.url = url
    self.path = path
    self.size = size
    self.doc_type = self._DOC_TYPES.get(doc_type, 'UNKNOWN')


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


class GoogleDriveParser(parser.SQLiteParser):
  """Parser for Google Drive snapshot.db files."""

  # Define the needed queries.
  QUERIES = [(('SELECT resource_id, filename, modified, '
               'created, size, doc_type, shared, checksum, url '
               'FROM cloud_entry WHERE modified IS NOT NULL;'),
              'ParseCloudEntryRow'),
             (('SELECT inode_number, filename, modified, '
               'checksum, size '
               'FROM local_entry WHERE modified IS NOT NULL;'),
              'ParseLocalEntryRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([
      'cloud_entry', 'cloud_relations', 'local_entry', 'local_relations',
      'mapping', 'overlay_status'])

  def GetLocalPath(self, inode, path):
    """Return local path for a given inode.

    Args:
      inode: The inode number for the file.
      path: A list containing the current path discovered so far,
            for the initial run, this should be an empty list.

    Returns:
      A full path, including the filename of the given inode value.
    """
    cursor = self.db.cursor()
    sql = ('SELECT e.filename, r.parent_inode_number FROM local_relations AS '
           'r, local_entry AS e WHERE r.child_inode_number = ? AND '
           'r.child_inode_number = e.inode_number')
    results = cursor.execute(sql, (inode,))

    try:
      new_path, new_inode = results.fetchone()
      path.append(new_path)
      return self.GetLocalPath(new_inode, path)
    except TypeError:
      path.reverse()
      return u'/' + u'/'.join(path)

  def GetCloudPath(self, resource_id, path):
    """Return cloud path given a resource id.

    Args:
      resource_id: The resource_id for the file.
      path: A list containing the current path discovered so far,
            for the initial run, this should be an empty list.

    Returns:
      A full path, including the filename of the given resource value.
    """
    cursor = self.db.cursor()
    sql = ('SELECT e.filename, r.parent_resource_id FROM cloud_relations AS '
           'r, cloud_entry AS e WHERE r.child_resource_id = ? AND '
           'r.child_resource_id = e.resource_id')
    results = cursor.execute(sql, (resource_id,))
    new_path, new_resource_id = results.fetchone()
    path.append(new_path)

    if new_resource_id == 'folder:root':
      path.reverse()
      return u'/' + u'/'.join(path)

    return self.GetCloudPath(new_resource_id, path)

  def ParseCloudEntryRow(self, row, **dummy_kwargs):
    """Parses a cloud entry row.

    Args:
      row: The row resulting from the query.

    Returns:
      An event container (GoogleDriveSnapshotCloudEntryEventContainer)
      containing the event data.
    """
    # TODO: this query is run for every row, can this be optimized by
    # either a join or caching the mappings of resource_id and the path.
    cloud_path = self.GetCloudPath(row['resource_id'], [])
    container = GoogleDriveSnapshotCloudEntryEventContainer(
        row['url'], cloud_path, row['size'],
        row['doc_type'])

    if row['shared']:
      container.shared = 'Shared'
    else:
      container.shared = 'Private'

    container.Append(event.PosixTimeEvent(
        row['modified'], eventdata.EventTimestamp.MODIFICATION_TIME,
        container.data_type))

    if row['created']:
      container.Append(event.PosixTimeEvent(
          row['created'], eventdata.EventTimestamp.CREATION_TIME,
          container.data_type))

    # TODO: shouldn't this be yield?
    return container

  def ParseLocalEntryRow(self, row, **dummy_kwargs):
    """Parses a local entry row.

    Args:
      row: The row resulting from the query.

    Yields:
      An event object (GoogleDriveSnapshotLocalEntryEvent) containing
      the event data.
    """
    # TODO: this query is run for every row, can this be optimized by
    # either a join or caching the mappings of resource_id and the path.
    local_path = self.GetLocalPath(row['inode_number'], [])

    yield GoogleDriveSnapshotLocalEntryEvent(
        row['modified'], local_path, row['size'])

