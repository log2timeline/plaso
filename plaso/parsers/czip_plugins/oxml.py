# -*- coding: utf-8 -*-
"""Compound ZIP parser plugin for OpenXML files."""

from __future__ import unicode_literals

import re
import zipfile

from defusedxml import ElementTree
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.parsers import czip
from plaso.parsers.czip_plugins import interface

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

  DATA_TYPE = 'metadata:openxml'

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

class OpenXMLPlugin(interface.CompoundZIPPlugin):
  """Parse metadata from OXML files."""

  NAME = 'oxml'
  DESCRIPTION = 'Parser for OpenXML (OXML) files.'

  REQUIRED_PATHS = frozenset(
      ['[Content_Types].xml', '_rels/.rels', 'docProps/core.xml'])

  _PROPERTY_NAMES = {
      'creator': 'author',
      'lastModifiedBy': 'last_saved_by',
      'Total_Time': 'total_edit_time',
      'Pages': 'number_of_pages',
      'CharactersWithSpaces': 'number_of_characters_with_spaces',
      'Paragraphs': 'number_of_paragraphs',
      'Characters': 'number_of_characters',
      'Lines': 'number_of_lines',
      'revision': 'revision_number',
      'Words': 'number_of_words',
      'Application': 'creating_app',
      'Shared_Doc': 'shared',
  }

  def _GetPropertyValue(self, parser_mediator, properties, property_name):
    """Retrieves a property value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      properties (dict[str, object]): properties.
      property_name (str): name of the property.

    Returns:
      str: property value.
    """
    property_value = properties.get(property_name, None)
    if isinstance(property_value, py2to3.BYTES_TYPE):
      try:
        # TODO: get encoding form XML metadata.
        property_value = property_value.decode('utf-8')
      except UnicodeDecodeError:
        parser_mediator.ProduceExtractionWarning(
            'unable to decode property: {0:s}'.format(property_name))

    return property_value

  def _FormatPropertyName(self, property_name):
    """Formats a camel case property name as snake case.

    Args:
      property_name (str): property name in camel case.

    Returns:
      str: property name in snake case.
    """
    # TODO: Add Unicode support.
    fix_key = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', property_name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', fix_key).lower()

  def _ParsePropertiesXMLFile(self, xml_data):
    """Parses a properties XML file.

    Args:
      xml_data (bytes): data of a _rels/.rels XML file.

    Returns:
      dict[str, object]: properties.

    Raises:
      zipfile.BadZipfile: if the properties XML file cannot be read.
    """
    xml_root = ElementTree.fromstring(xml_data)

    properties = {}
    for xml_element in xml_root.iter():
      if not xml_element.text:
        continue

      # The property name is formatted as: {URL}name
      # For example: {http://purl.org/dc/terms/}modified
      _, _, name = xml_element.tag.partition('}')

      # Do not including the 'lpstr' attribute because it is very verbose.
      if name == 'lpstr':
        continue

      property_name = self._PROPERTY_NAMES.get(name, None)
      if not property_name:
        property_name = self._FormatPropertyName(name)

      properties[property_name] = xml_element.text

    return properties

  def _ParseRelationshipsXMLFile(self, xml_data):
    """Parses the relationships XML file (_rels/.rels).

    Args:
      xml_data (bytes): data of a _rels/.rels XML file.

    Returns:
      list[str]: property file paths. The path is relative to the root of
          the ZIP file.

    Raises:
      zipfile.BadZipfile: if the relationship XML file cannot be read.
    """
    xml_root = ElementTree.fromstring(xml_data)

    property_files = []
    for xml_element in xml_root.iter():
      type_attribute = xml_element.get('Type')
      if 'properties' in repr(type_attribute):
        target_attribute = xml_element.get('Target')
        property_files.append(target_attribute)

    return property_files

  def _ProduceEvent(
      self, parser_mediator, event_data, properties, property_name,
      timestamp_description, error_description):
    """Produces an event.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      event_data (OpenXMLEventData): event data.
      properties (dict[str, object]): properties.
      property_name (str): name of the date and time property.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      error_description (str): description of the meaning of the timestamp
          value for error reporting purposes.
    """
    time_string = properties.get(property_name, None)
    if not time_string:
      return

    # Date and time strings are in ISO 8601 format either with 1 second
    # or 100th nano second precision. For example:
    # 2012-11-07T23:29:00Z
    # 2012-03-05T20:40:00.0000000Z
    date_time = dfdatetime_time_elements.TimeElements()

    try:
      date_time.CopyFromStringISO8601(time_string)

      event = time_events.DateTimeValuesEvent(date_time, timestamp_description)
      parser_mediator.ProduceEventWithEventData(event, event_data)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unsupported {0:s}: {1:s} with error: {2!s}'.format(
              error_description, time_string, exception))

  def InspectZipFile(self, parser_mediator, zip_file):
    """Parses an OXML file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      zip_file (zipfile.ZipFile): the zip file containing OXML content. It is
          not be closed in this method, but will be closed by the parser logic
           in czip.py.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      xml_data = zip_file.read('_rels/.rels')
      property_files = self._ParseRelationshipsXMLFile(xml_data)
    except (IndexError, IOError, KeyError, OverflowError, ValueError,
            zipfile.BadZipfile) as exception:
      parser_mediator.ProduceExtractionWarning((
          'Unable to parse relationships XML file: _rels/.rels with error: '
          '{0!s}').format(exception))
      return

    metadata = {}

    for path in property_files:
      try:
        xml_data = zip_file.read(path)
        properties = self._ParsePropertiesXMLFile(xml_data)
      except (IndexError, IOError, KeyError, OverflowError, ValueError,
              zipfile.BadZipfile) as exception:
        parser_mediator.ProduceExtractionWarning((
            'Unable to parse properties XML file: {0:s} with error: '
            '{1!s}').format(path, exception))
        continue

      metadata.update(properties)

    event_data = OpenXMLEventData()
    event_data.app_version = self._GetPropertyValue(
        parser_mediator, metadata, 'app_version')
    event_data.app_version = self._GetPropertyValue(
        parser_mediator, metadata, 'app_version')
    event_data.author = self._GetPropertyValue(
        parser_mediator, metadata, 'author')
    event_data.creating_app = self._GetPropertyValue(
        parser_mediator, metadata, 'creating_app')
    event_data.doc_security = self._GetPropertyValue(
        parser_mediator, metadata, 'doc_security')
    event_data.hyperlinks_changed = self._GetPropertyValue(
        parser_mediator, metadata, 'hyperlinks_changed')
    event_data.i4 = self._GetPropertyValue(
        parser_mediator, metadata, 'i4')
    event_data.last_saved_by = self._GetPropertyValue(
        parser_mediator, metadata, 'last_saved_by')
    event_data.links_up_to_date = self._GetPropertyValue(
        parser_mediator, metadata, 'links_up_to_date')
    event_data.number_of_characters = self._GetPropertyValue(
        parser_mediator, metadata, 'number_of_characters')
    event_data.number_of_characters_with_spaces = self._GetPropertyValue(
        parser_mediator, metadata, 'number_of_characters_with_spaces')
    event_data.number_of_lines = self._GetPropertyValue(
        parser_mediator, metadata, 'number_of_lines')
    event_data.number_of_pages = self._GetPropertyValue(
        parser_mediator, metadata, 'number_of_pages')
    event_data.number_of_paragraphs = self._GetPropertyValue(
        parser_mediator, metadata, 'number_of_paragraphs')
    event_data.number_of_words = self._GetPropertyValue(
        parser_mediator, metadata, 'number_of_words')
    event_data.revision_number = self._GetPropertyValue(
        parser_mediator, metadata, 'revision_number')
    event_data.scale_crop = self._GetPropertyValue(
        parser_mediator, metadata, 'scale_crop')
    event_data.shared_doc = self._GetPropertyValue(
        parser_mediator, metadata, 'shared_doc')
    event_data.template = self._GetPropertyValue(
        parser_mediator, metadata, 'template')
    event_data.total_time = self._GetPropertyValue(
        parser_mediator, metadata, 'total_time')

    self._ProduceEvent(
        parser_mediator, event_data, metadata, 'created',
        definitions.TIME_DESCRIPTION_CREATION, 'creation time')
    self._ProduceEvent(
        parser_mediator, event_data, metadata, 'modified',
        definitions.TIME_DESCRIPTION_MODIFICATION, 'modification time')
    self._ProduceEvent(
        parser_mediator, event_data, metadata, 'last_printed',
        definitions.TIME_DESCRIPTION_LAST_PRINTED, 'last printed time')


czip.CompoundZIPParser.RegisterPlugin(OpenXMLPlugin)
