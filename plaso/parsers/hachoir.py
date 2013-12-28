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
"""This file contains a parser for extracting metadata."""
# TODO: Add a unit test for this parser.

import datetime

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import parser
from plaso.lib import timelib

import hachoir_core.config

# This is necessary to do PRIOR to loading up other parts of hachoir
# framework, otherwise console does not work and other "weird" behavior
# is observed.
hachoir_core.config.unicode_stdout = False
hachoir_core.config.quiet = True

import hachoir_core
import hachoir_parser
import hachoir_metadata


__author__ = 'David Nides (david.nides@gmail.com)'


class HachoirEvent(event.TimestampEvent):
  """Process timestamps from Hachoir Events."""

  DATA_TYPE = 'metadata:hachoir'

  def __init__(self, dt_timestamp, usage):
    """An EventObject created from a Hachoir entry.

    Args:
      dt_timestamp: A python datetime.datetime object.
      usage: The description of the usage of the time value.
    """
    timestamp = timelib.Timestamp.FromPythonDatetime(dt_timestamp)
    super(HachoirEvent, self).__init__(timestamp, usage, self.DATA_TYPE)


class HachoirParser(parser.BaseParser):
  """Parse meta data from files."""

  DATA_TYPE = 'metadata:hachoir'

  NAME = 'hachoir'

  def Parse(self, file_entry):
    """Extract data from a file using Hachoir.

    Args:
      file_entry: A file entry object.

    Yields:
      An event container (EventContainer) that contains the parsed
      attributes.
    """
    file_object = file_entry.Open()

    try:
      fstream = hachoir_core.stream.InputIOStream(file_object, None, tags=[])
    except hachoir_core.error.HachoirError as exception:
      raise errors.UnableToParseFile(u'[%s] unable to parse file %s: %s' % (
          self.parser_name, file_entry.name, exception))

    if not fstream:
      raise errors.UnableToParseFile(u'[%s] unable to parse file %s: %s' % (
          self.parser_name, file_entry.name, 'Not fstream'))

    try:
      doc_parser = hachoir_parser.guessParser(fstream)
    except hachoir_core.error.HachoirError as exception:
      raise errors.UnableToParseFile(u'[%s] unable to parse file %s: %s' % (
          self.parser_name, file_entry.name, exception))

    if not doc_parser:
      raise errors.UnableToParseFile(u'[%s] unable to parse file %s: %s' % (
          self.parser_name, file_entry.name, 'Not parser'))

    try:
      metadata = hachoir_metadata.extractMetadata(doc_parser)
    except (AssertionError, AttributeError) as exception:
      raise errors.UnableToParseFile(u'[%s] unable to parse file %s: %s' % (
          self.parser_name, file_entry.name, exception))

    try:
      metatext = metadata.exportPlaintext(human=False)
    except AttributeError as exception:
      raise errors.UnableToParseFile(u'[%s] unable to parse file %s: %s' % (
          self.parser_name, file_entry.name, exception))

    if not metatext:
      raise errors.UnableToParseFile(
          u'[%s] unable to parse file %s: No metadata' % (
              self.parser_name, file_entry.name))

    event_container = event.EventContainer()
    event_container.offset = 0
    event_container.data_type = self.DATA_TYPE

    attributes = {}
    for meta in metatext:
      if meta[0] != '-' or len(meta) < 3:
        continue

      key, _, value = meta[2:].partition(': ')

      key2, _, value2 = value.partition(': ')
      if key2 == 'LastPrinted' and value2 != 'False':
        date_object = timelib.StringToDatetime(
            value2, timezone=self._pre_obj.zone)
        if isinstance(date_object, datetime.datetime):
          event_container.Append(HachoirEvent(
              date_object, key2))

      try:
        date = metadata.get(key)
        if isinstance(date, datetime.datetime):
          event_container.Append(HachoirEvent(date, key))
      except ValueError:
        pass

      if key in attributes:
        if isinstance(attributes.get(key), list):
          attributes[key].append(value)
        else:
          old_value = attributes.get(key)
          attributes[key] = [old_value, value]
      else:
        attributes[key] = value

    length = len(event_container)
    if not length:
      raise errors.UnableToParseFile('[%s] unable to parse file %s: %s' % (
          self.parser_name, file_entry.name, 'None'))

    event_container.metadata = attributes
    file_object.close()
    yield event_container
