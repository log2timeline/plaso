# -*- coding: utf-8 -*-
"""This file contains a parser for OXML files (i.e. MS Office 2007+)."""

import logging
import re
import struct
import zipfile

from xml.etree import ElementTree

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'David Nides (david.nides@gmail.com)'


class OpenXMLEventData(events.EventData):
  """OXML event data.

  Attributes:
    app_version (str): version of application that created document.
    author (str): name of author.
    creating_app (str): name of application that created document.
    doc_security (str): ???
    hyperlinks_changed (bool): True if hyperlinks have changed.
    i4 (str): ???
    last_saved_by (str): name of user that last saved the document.
    links_up_to_date (bool): True if the links are up to date.
    number_of_characters (int): number of characters without spaces in
        the document.
    number_of_characters_with_spaces (int): number of characters including
        spaces in the document.
    number_of_lines (int): number of lines in the document.
    number_of_pages (int): number of pages in the document.
    number_of_paragraphs (int): number of paragraphs in the document.
    number_of_words (int): number of words in the document.
    revision_number (int): revision number.
    scale_crop (bool): True if crop to scale is enabled.
    shared_doc (bool): True if document is shared.
    template (str): name of template ???
    total_time (str): ???
  """

  DATA_TYPE = u'metadata:openxml'

  def __init__(self):
    """Initializes event data."""
    super(OpenXMLEventData, self).__init__(data_type=self.DATA_TYPE)
    self.app_version = None
    self.author = None
    self.creating_app = None
    self.doc_security = None
    self.hyperlinks_changed = None
    self.i4 = None
    self.last_saved_by = None
    self.links_up_to_date = None
    self.number_of_characters = None
    self.number_of_characters_with_spaces = None
    self.number_of_lines = None
    self.number_of_pages = None
    self.number_of_paragraphs = None
    self.number_of_words = None
    self.revision_number = None
    self.scale_crop = None
    self.shared_doc = None
    self.template = None
    self.total_time = None


class OpenXMLParser(interface.FileObjectParser):
  """Parse metadata from OXML files."""

  NAME = u'openxml'
  DESCRIPTION = u'Parser for OpenXML (OXML) files.'

  _METAKEY_TRANSLATE = {
      u'creator': u'author',
      u'lastModifiedBy': u'last_saved_by',
      u'Total_Time': u'total_edit_time',
      u'Pages': u'number_of_pages',
      u'CharactersWithSpaces': u'number_of_characters_with_spaces',
      u'Paragraphs': u'number_of_paragraphs',
      u'Characters': u'number_of_characters',
      u'Lines': u'number_of_lines',
      u'revision': u'revision_number',
      u'Words': u'number_of_words',
      u'Application': u'creating_app',
      u'Shared_Doc': u'shared',
  }

  _FILES_REQUIRED = frozenset([
      u'[Content_Types].xml', u'_rels/.rels', u'docProps/core.xml'])

  def _FixString(self, key):
    """Convert CamelCase to lower_with_underscore."""
    # TODO: Add Unicode support.
    fix_key = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', key)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', fix_key).lower()

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an OXML file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_name = parser_mediator.GetDisplayName()

    if not zipfile.is_zipfile(file_object):
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, file_name, u'Not a Zip file.'))

    try:
      zip_container = zipfile.ZipFile(file_object, 'r')
    except (zipfile.BadZipfile, struct.error, zipfile.LargeZipFile):
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, file_name, u'Bad Zip file.'))

    zip_name_list = set(zip_container.namelist())

    if not self._FILES_REQUIRED.issubset(zip_name_list):
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, file_name, u'OXML element(s) missing.'))

    metadata = {}
    timestamps = {}

    try:
      rels_xml = zip_container.read(u'_rels/.rels')
    except zipfile.BadZipfile as exception:
      parser_mediator.ProduceExtractionError(
          u'Unable to parse file with error: {0:s}'.format(exception))
      return

    rels_root = ElementTree.fromstring(rels_xml)

    for properties in rels_root.iter():
      if u'properties' in repr(properties.get(u'Type')):
        try:
          xml = zip_container.read(properties.get(u'Target'))
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
            _, _, tag = element.tag.partition(u'}')
            # Not including the 'lpstr' attribute because it is
            # very verbose.
            if tag == u'lpstr':
              continue

            if tag in (u'created', u'modified', u'lastPrinted'):
              timestamps[tag] = element.text
            else:
              tag_name = self._METAKEY_TRANSLATE.get(tag, self._FixString(tag))
              metadata[tag_name] = element.text

    event_data = OpenXMLEventData()
    event_data.app_version = metadata.get(u'app_version', None)
    event_data.author = metadata.get(u'author', None)
    event_data.creating_app = metadata.get(u'creating_app', None)
    event_data.doc_security = metadata.get(u'doc_security', None)
    event_data.hyperlinks_changed = metadata.get(u'hyperlinks_changed', None)
    event_data.i4 = metadata.get(u'i4', None)
    event_data.last_saved_by = metadata.get(u'last_saved_by', None)
    event_data.links_up_to_date = metadata.get(u'links_up_to_date', None)
    event_data.number_of_characters = metadata.get(
        u'number_of_characters', None)
    event_data.number_of_characters_with_spaces = metadata.get(
        u'number_of_characters_with_spaces', None)
    event_data.number_of_lines = metadata.get(u'number_of_lines', None)
    event_data.number_of_pages = metadata.get(u'number_of_pages', None)
    event_data.number_of_paragraphs = metadata.get(
        u'number_of_paragraphs', None)
    event_data.number_of_words = metadata.get(u'number_of_words', None)
    event_data.revision_number = metadata.get(u'revision_number', None)
    event_data.scale_crop = metadata.get(u'scale_crop', None)
    event_data.shared_doc = metadata.get(u'shared_doc', None)
    event_data.template = metadata.get(u'template', None)
    event_data.total_time = metadata.get(u'total_time', None)

    # Date and time strings are in ISO 8601 format with 1 second precision.
    # For example: 2012-11-07T23:29:00Z
    date_time = dfdatetime_time_elements.TimeElements()

    time_string = timestamps.get(u'created', None)
    if time_string:
      try:
        date_time.CopyFromStringISO8601(time_string)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_CREATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)
      except ValueError as exception:
        parser_mediator.ProduceExtractionError(
            u'unsupported created time: {0:s} with error: {1:s}.'.format(
                time_string, exception))

    time_string = timestamps.get(u'modified', None)
    if time_string:
      try:
        date_time.CopyFromStringISO8601(time_string)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)
      except ValueError as exception:
        parser_mediator.ProduceExtractionError(
            u'unsupported modified time: {0:s} with error: {1:s}.'.format(
                time_string, exception))

    time_string = timestamps.get(u'lastPrinted', None)
    if time_string:
      try:
        date_time.CopyFromStringISO8601(time_string)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_LAST_PRINTED)
        parser_mediator.ProduceEventWithEventData(event, event_data)
      except ValueError as exception:
        parser_mediator.ProduceExtractionError(
            u'unsupported last printed time: {0:s} with error: {1:s}.'.format(
                time_string, exception))


manager.ParsersManager.RegisterParser(OpenXMLParser)
