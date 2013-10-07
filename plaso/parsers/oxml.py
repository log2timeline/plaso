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
"""This file contains a parser for OXML files (i.e. MS Office 2007+)."""

import re
import logging
import zipfile

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib
from xml.etree import ElementTree

__author__ = 'David Nides (david.nides@gmail.com)'


class OpenXMLParser(parser.PlasoParser):
  """Parse metadata from OXML files."""

  DATA_TYPE = 'metadata:openxml'

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

  _FILES_REQUIRED = frozenset(['[Content_Types].xml',
                               '_rels/.rels',
                               'docProps/core.xml'])

  def Parse(self, filehandle):
    """Extract EventObjects from a file."""

    if not zipfile.is_zipfile(filehandle):
      raise errors.UnableToParseFile(
          u'[%s] unable to parse file %s: %s' % (
              self.parser_name, filehandle.name, 'Not a Zip file.'))

    try:
      zip_container = zipfile.ZipFile(filehandle, 'r')
    except zipfile.BadZipfile:
      raise errors.UnableToParseFile(
          u'[%s] unable to parse file %s: %s' % (
              self.parser_name, filehandle.name, 'Bad Zip file.'))

    zip_name_list = set(zip_container.namelist())

    if not self._FILES_REQUIRED.issubset(zip_name_list):
      raise errors.UnableToParseFile(
          u'[%s] unable to parse file %s: %s' % (
              self.parser_name, filehandle.name, 'OXML element(s) missing.'))
    metadata = {}

    rels_xml = zip_container.read('_rels/.rels')
    rels_root = ElementTree.fromstring(rels_xml)

    for properties in rels_root.iter():
      if 'properties' in repr(properties.get('Type')):
        try:
          xml = zip_container.read(properties.get('Target'))
          root = ElementTree.fromstring(xml)
        except (OverflowError, IndexError, ValueError) as exception:
          logging.warning(
            u'Unable to read property [%s].', exception)
          continue

        for element in root.iter():
          if element.text:
            _, _, tag = element.tag.partition('}')
            # Not including the 'lpstr' attribute because it is
            # very verbose.
            if tag != 'lpstr':
              metadata[tag] = element.text

    container = event.EventContainer()
    container.offset = 0
    container.data_type = self.DATA_TYPE

    for key, value in metadata.items():
      if key in ('created', 'modified', 'lastPrinted'):
        continue
      attribute_name = self._METAKEY_TRANSLATE.get(key, self.FixString(key))
      setattr(container, attribute_name, value)

    if metadata.get('created', None):
      container.Append(OpenXMLParserEvent(
          metadata['created'], eventdata.EventTimestamp.CREATION_TIME))

    if metadata.get('modified', None):
      container.Append(OpenXMLParserEvent(
          metadata['modified'], eventdata.EventTimestamp.MODIFICATION_TIME))

    if metadata.get('lastPrinted', None):
      container.Append(OpenXMLParserEvent(
          metadata['lastPrinted'], eventdata.EventTimestamp.LAST_PRINTED))

    if not container:
      raise errors.UnableToParseFile(
          u'[%s] unable to parse file %s: %s' % (
              self.parser_name, filehandle.name, 'No timestamps.'))

    return container

  def FixString(self, key):
    """Convert CamelCase to lower_with_underscore."""
    # TODO: Add unicode support.
    fix_key = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', key)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', fix_key).lower()


class OpenXMLParserEvent(event.TimestampEvent):
  """Process timestamps from MS Office XML Events."""

  DATA_TYPE = 'metadata:openxml'

  def __init__(self, dt_timestamp, usage):
    """An EventObject created from an OLE2 entry.

    Args:
      dt_timestamp: A python datetime.datetime object.
      usage: The description of the usage of the time value.
    """
    timestamp = timelib.Timestamp.FromTimeString(dt_timestamp)
    super(OpenXMLParserEvent, self).__init__(timestamp, usage, self.DATA_TYPE)
