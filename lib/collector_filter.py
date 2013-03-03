#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This is a simple filter implementation for the collector in Plaso."""
import logging
import os
import re
import sre_constants

from plaso.lib import errors


class CollectionFilter(object):
  """A collection filter for plaso used for targeted collection."""

  def __init__(self, collector, filter_path):
    """The constructor for the CollectionFilter.

    Args:
      collector: A Collector object used to find/locate files.
      filter_path: A path to a file containing filter patterns.

    Raises:
      errors.BadConfigOption: When the filter_path does not exist or is not
                              correctly formed.
    """
    if not os.path.isfile(filter_path):
      raise errors.BadConfigOption(
          u'Filter file [{}] does not exist.'.format(filter_path))

    self._filters = self._BuildFiltersFromFile(filter_path)
    self._collector = collector

  def _BuildFiltersFromFile(self, filter_path):
    """Return a list of filter paths."""
    ret = []
    with open(filter_path, 'rb') as fh:
      for line in fh:
        if line[0] == '#':
          continue
        dir_path, _, file_path = line.rstrip().rpartition('/')
        if not file_path:
          logging.warning(u'Unable to parse the filter line: {}'.format(line))
          continue
        ret.append((dir_path, file_path))

    return ret

  def GetPathSpecs(self):
    """A generator yielding all pathspecs from the given filters."""
    for filter_path, filter_file in self._filters:
      try:
        path = self._collector.FindPath(filter_path)
      except errors.PathNotFound as e:
        logging.warning(u'Unable to find path: [{}]'.format(filter_path))
        continue
      try:
        for file_path in self._collector.GetFilePaths(path, filter_file):
          fh = self._collector.OpenFile(file_path)
          yield fh.pathspec_root.ToProtoString()
      except errors.PreProcessFail:
        logging.warning(
            u'Unable to parse the filter: {}|{} - path not found.'.format(
                filter_path, filter_file))
        continue
      except sre_constants.error:
        logging.warning(
            (u'Unable to parse the filter: {}|{} - illegal regular '
             'expression.').format(filter_path, filter_file))
        continue
