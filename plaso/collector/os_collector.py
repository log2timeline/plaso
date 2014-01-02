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
"""The operating system collector object implementation."""

import os

from plaso.collector import interface
from plaso.lib import event
from plaso.lib import utils
from plaso.pvfs import pfile_entry
from plaso.pvfs import utils as pvfs_utils


class FileSystemPreprocessCollector(interface.PreprocessCollector):
  """Class that implements the file system preprocess collector object."""

  def _GetPaths(self, path_segments_expressions_list):
    """Retrieves paths based on path segments expressions.

       A path segment expression is either a regular expression or a string
       containing an expanded path segment.

    Args:
       path_segments_expressions_list: A list of path segments expressions.

    Yields:
      The paths found.
    """
    source_path = self._source_path
    if source_path.endswith(os.path.sep):
      source_path = source_path[:-1]

    paths_found = ['']
    for path_segment_expression in path_segments_expressions_list:
      sub_paths_found = []

      for path in paths_found:
        full_path = pfile_entry.OsFileEntry.JoinPath([source_path, path])

        path_spec = event.EventPathSpec()
        path_spec.type = 'OS'
        path_spec.file_path = utils.GetUnicodeString(full_path)
        file_entry = pfile_entry.OsFileEntry(path_spec)

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
            sub_paths_found.append(pfile_entry.OsFileEntry.JoinPath([
                path, sub_file_entry_match]))

      paths_found = sub_paths_found

      if not paths_found:
        break

    for path in paths_found:
      # A resulting path will contain a leading path separator that needs to be
      # removed. If path is an empty string the result of path[1:] will be
      # an empty string.
      yield path[1:]

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    return pvfs_utils.OpenOSFileEntry(os.path.join(self._source_path, path))

  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
    return False
