# -*- coding: utf-8 -*-
"""This file contains a parser for OXML files (i.e. MS Office 2007+)."""

import logging
import os
import re
import struct
import zipfile

from xml.etree import ElementTree

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'David Nides (david.nides@gmail.com)'


class OpenXMLParserEvent(time_events.TimestampEvent):
  """Process timestamps from MS Office XML Events."""

  DATA_TYPE = 'metadata:openxml'

  def __init__(self, timestamp_string, usage, metadata):
    """Initializes the event object.

    Args:
      timestamp_string: An ISO 8601 representation of a timestamp.
      usage: The description of the usage of the time value.
      metadata: A dict object containing extracted metadata.
    """
    timestamp = timelib.Timestamp.FromTimeString(timestamp_string)
    super(OpenXMLParserEvent, self).__init__(timestamp, usage, self.DATA_TYPE)
    for key, value in metadata.iteritems():
      setattr(self, key, value)


class OpenXMLParser(interface.BaseParser):
  """Parse metadata from OXML files."""

  NAME = 'openxml'
  DESCRIPTION = u'Parser for OpenXML (OXML) files.'

  _METAKEY_TRANSLATE = {
      'creator': 'author',
      'lastModifiedBy': 'last_saved_by',
      'Total_Time': 'total_edit_time',
      'Pages': 'num_pages',
      'Characters_with_spaces': 'num_chars_w_spaces',
      'Paragraphs': 'num_paragraphs',
      'Characters': 'num_chars',
      'Lines': 'num_lines',
      'revision': 'revision_num',
      'Words': 'num_words',
      'Application': 'creating_app',
      'Shared_Doc': 'shared',
  }

  _FILES_REQUIRED = frozenset([
      '[Content_Types].xml', '_rels/.rels', 'docProps/core.xml'])

  def _FixString(self, key):
    """Convert CamelCase to lower_with_underscore."""
    # TODO: Add unicode support.
    fix_key = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', key)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', fix_key).lower()

  def Parse(self, parser_mediator, **kwargs):
    """Extract data from an OXML file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    file_object = parser_mediator.GetFileObject()
    try:
      self.ParseFileObject(parser_mediator, file_object)
    finally:
      file_object.close()

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows EventLog (EVT) file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_name = parser_mediator.GetDisplayName()

    file_object.seek(0, os.SEEK_SET)
    if not zipfile.is_zipfile(file_object):
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, file_name, 'Not a Zip file.'))

    try:
      zip_container = zipfile.ZipFile(file_object, 'r')
    except (zipfile.BadZipfile, struct.error, zipfile.LargeZipFile):
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, file_name, 'Bad Zip file.'))

    zip_name_list = set(zip_container.namelist())

    if not self._FILES_REQUIRED.issubset(zip_name_list):
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, file_name, 'OXML element(s) missing.'))

    metadata = {}
    timestamps = {}

    try:
      rels_xml = zip_container.read('_rels/.rels')
    except zipfile.BadZipfile as exception:
      parser_mediator.ProduceParseError(
          u'Unable to parse file with error: {0:s}'.format(exception))
      return

    rels_root = ElementTree.fromstring(rels_xml)

    for properties in rels_root.iter():
      if 'properties' in repr(properties.get('Type')):
        try:
          xml = zip_container.read(properties.get('Target'))
          root = ElementTree.fromstring(xml)
        except (
            OverflowError, IndexError, KeyError, ValueError,
            zipfile.BadZipfile) as exception:
          logging.warning(
              u'[{0:s}] unable to read property with error: {1:s}.'.format(
                  self.NAME, exception))
          continue

        for element in root.iter():
          if element.text:
            _, _, tag = element.tag.partition('}')
            # Not including the 'lpstr' attribute because it is
            # very verbose.
            if tag == 'lpstr':
              continue

            if tag in ('created', 'modified', 'lastPrinted'):
              timestamps[tag] = element.text
            else:
              tag_name = self._METAKEY_TRANSLATE.get(tag, self._FixString(tag))
              metadata[tag_name] = element.text

    if timestamps.get('created', None):
      event_object = OpenXMLParserEvent(
          timestamps.get('created'), eventdata.EventTimestamp.CREATION_TIME,
          metadata)
      parser_mediator.ProduceEvent(event_object)

    if timestamps.get('modified', None):
      event_object = OpenXMLParserEvent(
          timestamps.get('modified'),
          eventdata.EventTimestamp.MODIFICATION_TIME, metadata)
      parser_mediator.ProduceEvent(event_object)

    if timestamps.get('lastPrinted', None):
      event_object = OpenXMLParserEvent(
          timestamps.get('lastPrinted'), eventdata.EventTimestamp.LAST_PRINTED,
          metadata)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(OpenXMLParser)
