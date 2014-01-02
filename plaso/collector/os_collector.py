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

import logging
import os
import re

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

      if not sub_paths_found:
        break

      paths_found = sub_paths_found

    # A resulting path will contain a leading path separator that needs
    # to be removed.
    for path in paths_found:
      # TODO: the original function contained a check for os.path.isdir()
      # is this function supposed to only return paths of directories?
      yield path[1:]

  def GetFilePaths(self, path, file_name):
    """Return a list of files given a path and a pattern.

    Args:
      path: the path.
      file_name: the file name pattern.

    Returns:
      A list of filenames.
    """
    filenames_found = []
    file_re = re.compile(r'^{0:s}$'.format(file_name), re.I | re.S)
    if path == os.path.sep:
      directory = self._source_path
      path_use = '.'
    else:
      directory = os.path.join(self._source_path, path)
      path_use = path

    try:
      for entry in os.listdir(directory):
        match = file_re.match(entry)
        if match:
          if os.path.isfile(os.path.join(directory, match.group(0))):
            filenames_found.append(os.path.join(path_use, match.group(0)))
    except OSError as exception:
      logging.error((
          u'Unable to read directory: {0:s} with error: {1:s}').format(
              directory, exception))
    return filenames_found

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    return pvfs_utils.OpenOSFileEntry(os.path.join(self._source_path, path))

  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
    return False
