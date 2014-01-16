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


class PreprocessCollector(object):
  """Class that implements the preprocess collector object interface."""

  _PATH_EXPANDER_RE = re.compile(r'^[{][a-z_]+[}]$')

  def __init__(self, pre_obj, source_path):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The preprocessing object.
      source_path: Path of the source file or directory.
    """
    super(PreprocessCollector, self).__init__()
    self._source_path = source_path
    self._path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
        pre_obj, None)

  def _GetExtendedPath(self, path):
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
  def _GetPaths(self, path_segments_expressions_list):
    """Retrieves paths based on path segment expressions.

       A path segment expression is either a regular expression or a string
       containing an expanded path segment.

    Args:
      path_segments_expressions_list: A list of path segments expressions.

    Yields:
      The paths found.
    """

  def _GetPathSegmentExpressionsList(self, path_expression):
    """Retrieves a list of paths  segment expressions on a path expression.

       A path segment expression is either a regular expression or a string
       containing an expanded path segment.

    Args:
      path_expression: The path expression, which is a string that can contain
                       system specific placeholders such as e.g. "{log_path}"
                       or "{systemroot}" or regular expressions such as e.g.
                       "[0-9]+" to match a path segments that only consists of
                       numeric values.

    Returns:
      A list of path segments expressions.
    """
    path_segments_expressions_list = []
    for path_segment in path_expression.split(u'/'):
      # Ignore empty path segments.
      if not path_segment:
        continue

      if self._PATH_EXPANDER_RE.match(path_segment):
        expression_list = self._GetExtendedPath(path_segment).split(u'/')
        if expression_list[0] == u'' and len(expression_list) > 1:
          expression_list = expression_list[1:]

        path_segments_expressions_list.extend(expression_list)

      else:
        try:
          # We compile the regular expression so it spans the full path
          # segment.
          expression_string = u'^{0:s}$'.format(path_segment)
          expression = re.compile(expression_string, re.I | re.S)

        except sre_constants.error as e:
          error_string = (
              u'Unable to compile regular expression for path segment: {0:s} '
              u'with error: {1:s}').format(path_segment, e)
          logging.warning(error_string)
          raise errors.PathNotFound(error_string)

        path_segments_expressions_list.append(expression)

    return path_segments_expressions_list

  # TODO: in PyVFS create a separate FindExpression of FindSpec object to
  # define path expresssions.
  def FindPaths(self, path_expression):
    """Finds paths based on a path expression.

       An empty path expression will return all paths. Note that the path
       expression uses / as the path (segment) separator.

    Args:
      path_expression: The path expression, which is a string that can contain
                       system specific placeholders such as e.g. "{log_path}" or
                       "{systemroot}" or regular expressions such as e.g.
                       "[0-9]+" to match a path segments that only consists of
                       numeric values.

    Returns:
      A list of paths.

    Raises:
      errors.PathNotFound: If unable to compile any regular expression.
    """
    path_segments_expressions_list = self._GetPathSegmentExpressionsList(
        path_expression)

    return self._GetPaths(path_segments_expressions_list)

  def GetFilePaths(self, path_expression, filename_expression):
    """Retrieves paths based on a path and filename expression.

    Args:
      path_expression: The path expression, which is a string that can contain
                       system specific placeholders such as e.g. "{log_path}"
                       or "{systemroot}" or regular expressions such as e.g.
                       "[0-9]+" to match a path segments that only consists of
                       numeric values.
      filename_expression: The filename expression.

    Returns:
      A list of paths.
    """
    path_segments_expressions_list = self._GetPathSegmentExpressionsList(
        path_expression)

    path_segments_expressions_list.extend(
        self._GetPathSegmentExpressionsList(filename_expression))

    return self._GetPaths(path_segments_expressions_list)

  @abc.abstractmethod
  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""

  @abc.abstractmethod
  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
