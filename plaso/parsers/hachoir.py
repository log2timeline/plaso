# -*- coding: utf-8 -*-
"""Parser that uses Hachoir to extract metadata."""

from __future__ import unicode_literals

# TODO: Add a unit test for this parser.

import datetime

# pylint: disable=import-error,wrong-import-position
import hachoir_core.config

# This is necessary to do PRIOR to loading up other parts of hachoir
# framework, otherwise console does not work and other "weird" behavior
# is observed.
hachoir_core.config.unicode_stdout = False
hachoir_core.config.quiet = True

import hachoir_core
import hachoir_parser
import hachoir_metadata

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


class HachoirEventData(events.EventData):
  """Hachoir event data.

  Attributes:
    metadata (dict[str, object]): hachoir metadata.
  """

  DATA_TYPE = 'metadata:hachoir'

  def __init__(self):
    """Initializes event data."""
    super(HachoirEventData, self).__init__(data_type=self.DATA_TYPE)
    self.metadata = {}


class HachoirParser(interface.FileObjectParser):
  """Parser that uses Hachoir."""

  NAME = 'hachoir'
  DESCRIPTION = 'Parser that wraps Hachoir.'

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a file-like object using Hachoir.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_name = parser_mediator.GetDisplayName()

    try:
      fstream = hachoir_core.stream.InputIOStream(file_object, None, tags=[])
    except hachoir_core.error.HachoirError as exception:
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, exception))

    if not fstream:
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, 'Not fstream'))

    try:
      doc_parser = hachoir_parser.guessParser(fstream)
    except hachoir_core.error.HachoirError as exception:
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, exception))

    if not doc_parser:
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, 'Not parser'))

    try:
      metadata = hachoir_metadata.extractMetadata(doc_parser)
    except (AssertionError, AttributeError) as exception:
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, exception))

    try:
      metatext = metadata.exportPlaintext(human=False)
    except AttributeError as exception:
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, exception))

    if not metatext:
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file {1:s}: No metadata'.format(
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
        date_object = timelib.Timestamp.FromTimeString(
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
          '[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_name, 'No events discovered'))

    event_data = HachoirEventData()
    event_data.metadata = attributes

    for datetime_value, usage in extracted_events:
      event = time_events.PythonDatetimeEvent(datetime_value, usage)
      parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(HachoirParser)
