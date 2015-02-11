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

import hachoir_core.config

# This is necessary to do PRIOR to loading up other parts of hachoir
# framework, otherwise console does not work and other "weird" behavior
# is observed.
hachoir_core.config.unicode_stdout = False
hachoir_core.config.quiet = True

import hachoir_core
import hachoir_parser
import hachoir_metadata

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'David Nides (david.nides@gmail.com)'


class HachoirEvent(time_events.TimestampEvent):
  """Process timestamps from Hachoir Events."""

  DATA_TYPE = 'metadata:hachoir'

  def __init__(self, dt_timestamp, usage, attributes):
    """An EventObject created from a Hachoir entry.

    Args:
      dt_timestamp: A python datetime.datetime object.
      usage: The description of the usage of the time value.
      attributes: A dict containing metadata for the event.
    """
    timestamp = timelib.Timestamp.FromPythonDatetime(dt_timestamp)
    super(HachoirEvent, self).__init__(timestamp, usage, self.DATA_TYPE)
    self.metadata = attributes


class HachoirParser(interface.BaseParser):
  """Parse meta data from files."""

  NAME = 'hachoir'
  DESCRIPTION = u'Parser that wraps Hachoir.'

  def Parse(self, parser_mediator, **kwargs):
    """Extract data from a file using Hachoir.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    file_name = parser_mediator.GetDisplayName()
    file_object = parser_mediator.GetFileObject()

    try:
      fstream = hachoir_core.stream.InputIOStream(file_object, None, tags=[])
    except hachoir_core.error.HachoirError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, exception))

    if not fstream:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, 'Not fstream'))

    try:
      doc_parser = hachoir_parser.guessParser(fstream)
    except hachoir_core.error.HachoirError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, exception))

    if not doc_parser:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, 'Not parser'))

    try:
      metadata = hachoir_metadata.extractMetadata(doc_parser)
    except (AssertionError, AttributeError) as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, exception))

    try:
      metatext = metadata.exportPlaintext(human=False)
    except AttributeError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, exception))

    if not metatext:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: No metadata'.format(
              self.NAME, file_name))



    attributes = {}
    extracted_events = []
    for meta in metatext:
      if not meta.startswith('-'):
        continue

      if len(meta) < 3:
        continue

      key, _, value = meta[2:].partition(': ')

      key2, _, value2 = value.partition(': ')
      if key2 == 'LastPrinted' and value2 != 'False':
        date_object = timelib.StringToDatetime(
            value2, timezone=parser_mediator.timezone)
        if isinstance(date_object, datetime.datetime):
          extracted_events.append((date_object, key2))

      try:
        date = metadata.get(key)
        if isinstance(date, datetime.datetime):
          extracted_events.append((date, key))
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

    if not extracted_events:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, 'No events discovered'))

    for date, key in extracted_events:
      event_object = HachoirEvent(date, key, attributes)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(HachoirParser)
