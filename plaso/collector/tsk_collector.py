#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""The SleuthKit collector object implementation."""

import logging

from plaso.collector import interface
from plaso.lib import event
from plaso.lib import utils
from plaso.pvfs import pvfs
from plaso.pvfs import pfile_entry
from plaso.pvfs import utils as pvfs_utils


class TSKFilePreprocessCollector(interface.PreprocessCollector):
  """A wrapper around collecting files from TSK images."""

  _BYTES_PER_SECTOR = 512

  def __init__(self, pre_obj, source_path, byte_offset=0):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The preprocessing object.
      source_path: Path of the source image file.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
    """
    super(TSKFilePreprocessCollector, self).__init__(pre_obj, source_path)
    self._image_offset = byte_offset
    self._fscache = pvfs.FilesystemCache()
    self._file_system_container = self._fscache.Open(
        source_path, byte_offset=byte_offset)

  def _GetPaths(self, path_segments_expressions_list):
    """Retrieves paths based on path segments expressions.

       A path segment expression is either a regular expression or a string
       containing an expanded path segment.

    Args:
       path_segments_expressions_list: A list of path segments expressions.

    Yields:
      The paths found.
    """
    paths_found = ['']
    for path_segment_expression in path_segments_expressions_list:
      sub_paths_found = []

      for path in paths_found:
        path_spec = event.EventPathSpec()
        path_spec.type = 'TSK'

        if not path:
          path_spec.file_path = u'/'
          path_spec.image_inode = self._file_system_container.fs.info.root_inum
        else:
          path_spec.file_path = utils.GetUnicodeString(path)

        path_spec.container_path = self._source_path
        path_spec.image_offset = self._image_offset
        # TODO: do we need to set root here?
        file_entry = pfile_entry.TSKFileEntry(
            path_spec, root=None, fscache=self._fscache)

        if isinstance(file_entry, pfile_entry.TSKFileEntry):
          # Work-around the limitation in TSKFileEntry that it needs to be open
          # to return stat information. This will be fixed by PyVFS.
          try:
            _  = file_entry.Open()
          except AttributeError as e:
            logging.error((
                u'Unable to read file: {0:s} from image with error: '
                u'{1:s}').format(file_entry.pathspec.file_path, e))
            continue

        # Since there are more path segment expressions and the file entry
        # is not a directory this cannot be the path we're looking for.
        if not file_entry.IsDirectory():
          continue

        for sub_file_entry in file_entry.GetSubFileEntries():
          sub_file_entry_match = u''

          # TODO: need to handle case (in)sentive matches.
          if isinstance(path_segment_expression, basestring):
            if path_segment_expression == sub_file_entry.directory_entry_name:
              sub_file_entry_match = sub_file_entry.directory_entry_name

          else:
            re_match = path_segment_expression.match(
                sub_file_entry.directory_entry_name)

            if re_match:
              sub_file_entry_match = re_match.group(0)

          if sub_file_entry_match:
            sub_paths_found.append(pfile_entry.TSKFileEntry.JoinPath([
                path, sub_file_entry_match]))

      paths_found = sub_paths_found

      if not paths_found:
        break

    for path in paths_found:
      yield path

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    return pvfs_utils.OpenTskFileEntry(
        path, self._source_path,
        int(self._image_offset / self._BYTES_PER_SECTOR), self._fscache)

  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
    return True


class VSSFilePreprocessCollector(TSKFilePreprocessCollector):
  """A wrapper around collecting files from a VSS store from an image file."""

  def __init__(self, pre_obj, source_path, store_number, byte_offset=0):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The preprocessing object.
      source_path: Path of the source image file.
      store_number: The VSS store index number.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
    """
    super(VSSFilePreprocessCollector, self).__init__(
        pre_obj, source_path, byte_offset=byte_offset)
    self._store_number = store_number
    self._fscache = pvfs.FilesystemCache()
    self._file_system_container = self._fscache.Open(
        source_path, byte_offset=byte_offset, store_number=store_number)

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    return pvfs_utils.OpenVssFileEntry(
        path, self._source_path, self._store_number,
        int(self._source_path / self._BYTES_PER_SECTOR), self._fscache)
