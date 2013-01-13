#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright David Nides (davnads.blogspot.com). All Rights Reserved.
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

"""This file contains a Google Drive parser in plaso."""
import re

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser


class GoogleDrive(parser.SQLiteParser):
  """Parse Google Drive history snapshot.db files."""

  NAME = 'Google Drive'

  # Define the needed queries.
  QUERIES = [(('SELECT resource_id, filename, modified, '
               'created, size, doc_type, shared, checksum, url '
               'FROM cloud_entry WHERE modified IS NOT NULL;'),
              'ParseCloudEntry'),
             (('SELECT inode_number, filename, modified, '
               'checksum, size '
               'FROM local_entry WHERE modified IS NOT NULL;'),
              'ParseLocalEntry')]

  # The required tables.
  REQUIRED_TABLES = (
      'cloud_entry', 'cloud_relations', 'local_entry', 'local_relations',
      'mapping', 'overlay_status')

  # The following definition for values can be found on Patrick Olson's blog:
  # http://www.sysforensics.org/2012/05/google-drive-forensics-notes.html
  DOC_TYPES = {
      '0': 'FOLDER',
      '1': 'FILE',
      '2': 'PRESENTATION',
      '3': 'UNKNOWN',
      '4': 'SPREADSHEET',
      '5': 'DRAWING',
      '6': 'DOCUMENT',
      '7': 'TABLE',
  }

  DATE_MULTIPLIER = 1000000

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
    sql = ('SELECT e.filename, r.parent_inode_number FROM local_relations AS r'
           ', local_entry AS e WHERE r.child_inode_number = ? AND r.child_in'
           'ode_number = e.inode_number')
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
    sql = ('SELECT e.filename, r.parent_resource_id FROM cloud_relations AS r'
           ', cloud_entry AS e WHERE r.child_resource_id = ? AND r.child_res'
           'ource_id = e.resource_id')
    results = cursor.execute(sql, (resource_id,))
    new_path, new_resource_id = results.fetchone()
    path.append(new_path)

    if new_resource_id == 'folder:root':
      path.reverse()
      return u'/' + u'/'.join(path)

    return self.GetCloudPath(new_resource_id, path)

  def ParseLocalEntry(self, row, **_):
    """Return an EventObject from a local record."""
    source_type = 'Google Drive (local entry)'
    date = int(row['modified']) * self.DATE_MULTIPLIER
    descripton = 'mtime'

    evt = event.SQLiteEvent(date, descripton, 'LOG', source_type)
    evt.path = self.GetLocalPath(row['inode_number'], [])
    evt.size = str(row['size'])

    yield evt

  def ParseCloudEntry(self, row, **_):
    """Return an EventObject from a cloud record."""
    source_type = 'Google Drive (cloud entry)'

    container = event.EventContainer()
    container.path = self.GetCloudPath(row['resource_id'], [])
    container.size = row['size']
    container.url = row['url']

    doc_type_int = str(row['doc_type'])
    container.doc_type = self.DOC_TYPES.get(doc_type_int, 'UNKNOWN')

    container.shared = 'Private'
    if row['shared']:
      container.shared = 'Shared'

    date = int(row['modified']) * self.DATE_MULTIPLIER
    container.Append(event.SQLiteEvent(date, 'mtime', 'LOG', source_type))

    if row['created']:
      date = int(row['created']) * self.DATE_MULTIPLIER
      descripton = 'ctime'
      container.Append(event.SQLiteEvent(date, descripton, 'LOG', source_type))

    return container


class GDriveLocalEntryFormatter(eventdata.EventFormatter):
  """Define the formatting for Google Drive history."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('GoogleDrive:Google Drive \(local', re.DOTALL)

  # The format string.
  FORMAT_STRING = u'File Path: {path} Size: {size}'
  FORMAT_STRING_SHORT = u'{path}'


class GDriveCloudEntryFormatter(eventdata.EventFormatter):
  """Define the formatting for Google Drive history."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('GoogleDrive:Google Drive \(cloud', re.DOTALL)

  # The format string.
  FORMAT_STRING = (u'File Path: {path} [{shared}] Size:{size} URL:{url} doc_'
                   'type:{doc_type}')
  FORMAT_STRING_SHORT = u'{path}'

