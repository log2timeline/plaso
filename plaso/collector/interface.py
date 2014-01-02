#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""The collector object interface."""

import abc
import logging
import re
import sre_constants

from plaso.lib import errors
from plaso.winreg import path_expander as winreg_path_expander


class PfileCollector(object):
  """Class that implements a pfile-based collector object interface."""

  def __init__(self, process_queue, output_queue, source_path):
    """Initializes the collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it added to the process queue
       as a path specification (instance of event.EventPathSpec).

    Args:
      proces_queue: The files processing queue (instance of
                    queue.QueueInterface).
      output_queue: The event output queue (instance of queue.QueueInterface).
                    This queue is used as a buffer to the storage layer.
      source_path: Path of the source file or directory.
    """
    super(PfileCollector, self).__init__()
    self._filter_file_path = None
    self._pre_obj = None
    self._queue = process_queue
    self._source_path = source_path
    self._storage_queue = output_queue
    self.collect_directory_metadata = True

  def __enter__(self):
    """Enters a with statement."""
    return self

  def __exit__(self, dummy_type, dummy_value, dummy_traceback):
    """Exits a with statement."""
    self.Finish()

  @abc.abstractmethod
  def Collect(self):
    """Discovers files adds their path specification to the process queue."""

  def Finish(self):
    """Finishes the collection and closes the process queue."""
    self._queue.Close()

  def Run(self):
    """Runs the collection process and closes the process queue afterwards."""
    self.Collect()
    self.Finish()

  def SetFilter(self, filter_file_path, pre_obj):
    """Sets the collection filter.

    Args:
      filter_file_path: The path of the filter file.
      pre_obj: The preprocessor object.
    """
    self._filter_file_path = filter_file_path
    self._pre_obj = pre_obj


class PreprocessCollector(object):
  """Class that implements the preprocess collector object interface."""

  def __init__(self, pre_obj):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The preprocessing object with all it's attributes that
      have been gathered so far.
    """
    self._path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
        pre_obj, None)

  def FindPaths(self, path_expression):
    """Return a path from a regular expression or a potentially wrong path.

    This method should attempt to find the correct file path given potentially
    limited information or a regular expression.

    Args:
      path_expression: A path to the the file in question. It can contain vague
      generic paths such as "{log_path}" or "{systemroot}" or a regular
      expression.

    Returns:
      The correct path as calculated from the source.

    Raises:
      errors.PathNotFound: If unable to compile any regular expression.
    """
    if not path_expression:
      return self.GetPaths('/')

    re_list = []
    for path_part in path_expression.split('/'):
      if not path_part:
        continue

      if '{' in path_part:
        re_list.append(self.GetExtendedPath(path_part))
      else:
        try:
          # We compile the regular expression so it matches the entire string
          # from beginning to end.
          re_list.append(re.compile(r'^{0:s}$'.format(path_part, re.I | re.S)))
        except sre_constants.error as e:
          logging.warning((
              u'Unable to append the following expression: {0:s} with error: '
              u'{1:s}').format(path_part, e))
          raise errors.PathNotFound((
              u'Unable to compile regex for path: {0:s} with error: '
              u'{1:s}').format(path_part, e))

    return self.GetPaths(re_list)

  @abc.abstractmethod
  def GetPaths(self, path_list):
    """Return a list of paths from an extended regular expression path.

    Args:
      path_list: A list of either regular expressions or expanded
                 paths (strings).

    Returns:
      A list of strings, presenting the correct paths (None if not found).
    """

  def GetExtendedPath(self, path):
    """Return an extened path without the generic path elements.

    Remove common generic path elements, like {log_path}, {systemroot}
    and extend them to their real meaning.

    Args:
      path: The path before extending it.

    Returns:
      A string containing the extended path.
    """
    try:
      return self._path_expander.ExpandPath(path)
    except KeyError as e:
      logging.error(
          u'Unable to expand path {0:s} with error: {1:s}'.format(path, e))

  @abc.abstractmethod
  def GetFilePaths(self, path, file_name):
    """Return a filepath to a file given a name pattern and a path.

    Args:
      path: The correct path to the file, perhaps gathered from GetPaths
            or FindPaths.
      file_name: The filename to the file (may be a regular expression).

    Returns:
      A list of all files found that fit the pattern.
    """

  @abc.abstractmethod
  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""

  @abc.abstractmethod
  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
