#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This is a simple filter implementation for the collector in Plaso."""
import logging
import os
import re
import sre_constants

from google.protobuf import message

from plaso.lib import errors
from plaso.proto import transmission_pb2


class CollectionFilter(object):
  """A collection filter for plaso used for targeted collection."""

  def __init__(self, collector, filter_definition):
    """The constructor for the CollectionFilter.

    Args:
      collector: A Collector object used to find/locate files.
      filter_definition: This can be either a PathFilter protobuf,
      a path to a file with ascii presentation of the protobuf or a list
      of entries, where each entry is a single path.

    Raises:
      errors.BadConfigOption: When the filter_definition is not formatted
          correctly.
    """
    if type(filter_definition) in (list, tuple):
      self._filters = self._BuildFiltersFromList(filter_definition)
    elif isinstance(filter_definition, transmission_pb2.PathFilter):
      self._filters = filter_definition
    elif type(filter_definition) in (str, unicode):
      if os.path.isfile(filter_definition):
        self._filters = self._BuildFiltersFromFile(filter_definition)
      else:
        self._filters = self._BuildFromSerializedProto(filter_definition)
    else:
      raise errors.BadConfigOption(
          u'Filter expression wrongly formatted, unknown type: {}'.format(
              type(filter_definition)))

    self._collector = collector

  def _BuildFromSerializedProto(self, filter_serialized):
    """Return a PathFilter protobuf from a serialized protobuf."""
    proto = transmission_pb2.PathFilter()
    try:
      proto.ParseFromString(filter_serialized)
    except message.DecodeError:
      # We get here either because of a faulty serialized protobof or if
      # this was an attempt to open up a file that does not exist.
      raise errors.BadConfigOption(
          u'Filter file [{}] does not exist.'.format(filter_serialized))

    return proto

  def _BuildFiltersFromList(self, filter_list):
    """Return a PathFilter protobuf from the entries in the filter list."""
    proto = transmission_pb2.PathFilter()

    for filter_string in filter_list:
      if filter_string.startswith('filter_string:'):
        _, _, filter_end = filter_string.partition(':')
        if filter_end.endswith('\'') or filter_end.endswith('"'):
          filter_string = filter_end.strip()[1:-1]
        else:
          filter_string = filter_end

      proto.filter_string.append(filter_string)

    return proto

  def _BuildFiltersFromFile(self, filter_path):
    """Return a list of filter paths."""
    proto = transmission_pb2.PathFilter()

    with open(filter_path, 'rb') as fh:
      for line in fh:
        if line[0] == '#':
          continue
        proto.filter_string.append(line)

    return proto

  def BuildFiltersFromProto(self):
    """Return a list of tuples of paths and file names."""
    ret = []

    if not self._filters:
      return ret

    for line in self._filters.filter_string:
      dir_path, _, file_path = line.rstrip().rpartition('/')
      if not file_path:
        logging.warning(u'Unable to parse the filter line: {}'.format(line))
        continue
      ret.append((dir_path, file_path))

    return ret

  def GetPathSpecs(self):
    """A generator yielding all pathspecs from the given filters."""
    filter_list = self.BuildFiltersFromProto()

    for filter_path, filter_file in filter_list:
      try:
        paths = list(self._collector.FindPaths(filter_path))
      except errors.PathNotFound as e:
        logging.warning(u'Unable to find path: [{}]'.format(filter_path))
        continue
      try:
        for path in paths:
          for file_path in self._collector.GetFilePaths(path, filter_file):
            fh = self._collector.OpenFile(file_path)
            yield fh.pathspec_root.ToProtoString()
      except errors.PreProcessFail as e:
        logging.warning(
            u'Unable to parse the filter: {}|{} - path not found [{}].'.format(
                filter_path, filter_file, e))
        continue
      except sre_constants.error:
        logging.warning(
            (u'Unable to parse the filter: {}|{} - illegal regular '
             'expression.').format(filter_path, filter_file))
        continue

