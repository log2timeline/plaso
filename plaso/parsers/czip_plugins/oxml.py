# -*- coding: utf-8 -*-
"""Compound ZIP parser plugin for OpenXML files."""

import re
import zipfile

from xml.parsers import expat

from defusedxml import ElementTree

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import czip
from plaso.parsers.czip_plugins import interface


class OpenXMLEventData(events.EventData):
  """OXML event data.

  Attributes:
    application (str): name of application that created document.
    application_version (str): version of application that created document.
    author (str): name of author.
    creation_time (dfdatetime.DateTimeValues): creation date and time of
        the document.
    digital_signature (str): digital signature.
    edit_duration (int): total editing time.
    hyperlinks_changed (bool): True if hyperlinks have changed.
    last_printed_time (dfdatetime.DateTimeValues): date and time the document
        was last printed.
    last_saved_by (str): name of user that last saved the document.
    links_up_to_date (bool): True if the links are up to date.
    modification_time (dfdatetime.DateTimeValues): modification date and time
        of the document.
    number_of_characters (int): number of characters without spaces in
        the document.
    number_of_characters_with_spaces (int): number of characters including
        spaces in the document.
    number_of_clips (int): number of multi-media clips in the document.
    number_of_hidden_slides (int): number of hidden slides in the document.
    number_of_lines (int): number of lines in the document.
    number_of_pages (int): number of pages in the document.
    number_of_paragraphs (int): number of paragraphs in the document.
    number_of_slides (int): number of slides in the document.
    number_of_words (int): number of words in the document.
    revision_number (int): revision number.
    scale (bool): True if scaling of the thumbnail is desired or false if
        cropping is desired.
    security_flags (int): security flags.
    shared_doc (bool): True if document is shared.
    template (str): name of the template used to created the document.
  """

  DATA_TYPE = 'openxml:metadata'

  def __init__(self):
    """Initializes event data."""
    super(OpenXMLEventData, self).__init__(data_type=self.DATA_TYPE)
    self.application = None
    self.application_version = None
    self.author = None
    self.creation_time = None
    self.digital_signature = None
    self.edit_duration = None
    self.hyperlinks_changed = None
    self.last_printed_time = None
    self.last_saved_by = None
    self.links_up_to_date = None
    self.modification_time = None
    self.number_of_characters = None
    self.number_of_characters_with_spaces = None
    self.number_of_clips = None
    self.number_of_hidden_slides = None
    self.number_of_lines = None
    self.number_of_pages = None
    self.number_of_paragraphs = None
    self.number_of_slides = None
    self.number_of_words = None
    self.revision_number = None
    self.scale = None
    self.security_flags = None
    self.shared_doc = None
    self.template = None


class OpenXMLPlugin(interface.CompoundZIPPlugin):
  """Parse metadata from OXML files."""

  NAME = 'oxml'
  DATA_FORMAT = 'OpenXML (OXML) file'

  REQUIRED_PATHS = frozenset([
      '[Content_Types].xml', '_rels/.rels', 'docProps/core.xml'])

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
      'Application': 'application',
      'Shared_Doc': 'shared'}

  def _GetPropertyValue(self, parser_mediator, properties, name):
    """Retrieves a property value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      properties (dict[str, object]): properties.
      name (str): name of the property.

    Returns:
      str: property value.
    """
    property_value = properties.get(name, None)
    if isinstance(property_value, bytes):
      try:
        # TODO: get encoding form XML metadata.
        property_value = property_value.decode('utf-8')
      except UnicodeDecodeError:
        parser_mediator.ProduceExtractionWarning(
            'unable to decode property: {0:s}'.format(name))

    return property_value

  def _FormatPropertyName(self, name):
    """Formats a camel case property name as snake case.

    Args:
      name (str): property name in camel case.

    Returns:
      str: property name in snake case.
    """
    # TODO: Add Unicode support.
    fix_key = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', fix_key).lower()

  def _ParseBooleanValue(self, properties, name):
    """Parses a boolean property value.

    Args:
      properties (dict[str, object]): properties.
      name (str): name of the property.

    Returns:
      bool: boolean value or None not available.
    """
    string_value = properties.get(name, None)
    if string_value:
      if string_value == 'false':
        return False
      if string_value == 'true':
        return True

    return None

  def _ParseIntegerValue(self, properties, name):
    """Parses an integer property value.

    Args:
      properties (dict[str, object]): properties.
      name (str): name of the property.

    Returns:
      int: integer value or None not available.
    """
    string_value = properties.get(name, None)
    if string_value:
      try:
        return int(string_value, 10)
      except (TypeError, ValueError):
        pass

    return None

  def _ParseISO8601DateTimeString(self, parser_mediator, properties, name):
    """Parses an ISO8601 date and time string.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      properties (dict[str, object]): properties.
      name (str): name of the property.

    Returns:
      dfdatetime.TimeElementsInMicroseconds: date and time value or None if
          not available.
    """
    iso8601_string = properties.get(name, None)
    if not iso8601_string:
      return None

    # Date and time strings are in ISO8601 format either with 1 second
    # or 100th nano second precision. For example:
    # 2012-11-07T23:29:00Z
    # 2012-03-05T20:40:00.0000000Z
    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

    try:
      date_time.CopyFromStringISO8601(iso8601_string)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning((
          'Unable to parse value: {0:s} ISO8601 string: {1:s} with error: '
          '{2!s}').format(name, iso8601_string, exception))
      return None

    return date_time

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

  def _ParseZIPFile(self, parser_mediator, zip_file):
    """Parses an OXML file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      zip_file (zipfile.ZipFile): the zip file containing OXML content. It is
          not be closed in this method, but will be closed by the parser logic
           in czip.py.
    """
    try:
      xml_data = zip_file.read('_rels/.rels')
      property_files = self._ParseRelationshipsXMLFile(xml_data)
    except (IndexError, IOError, KeyError, LookupError, OverflowError,
            ValueError, ElementTree.ParseError, expat.ExpatError,
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
      except (IndexError, IOError, KeyError, LookupError, OverflowError,
              ValueError, ElementTree.ParseError, expat.ExpatError,
              zipfile.BadZipfile) as exception:
        parser_mediator.ProduceExtractionWarning((
            'Unable to parse properties XML file: {0:s} with error: '
            '{1!s}').format(path, exception))
        continue

      metadata.update(properties)

    event_data = OpenXMLEventData()
    event_data.application = self._GetPropertyValue(
        parser_mediator, metadata, 'application')
    event_data.application_version = self._GetPropertyValue(
        parser_mediator, metadata, 'app_version')
    event_data.author = self._GetPropertyValue(
        parser_mediator, metadata, 'author')
    event_data.creation_time = self._ParseISO8601DateTimeString(
        parser_mediator, metadata, 'created')
    event_data.digital_signature = self._GetPropertyValue(
        parser_mediator, metadata, 'dig_sig')
    event_data.edit_duration = self._ParseIntegerValue(metadata, 'total_time')
    event_data.hyperlinks_changed = self._ParseBooleanValue(
        metadata, 'hyperlinks_changed')
    # event_data.i4 = self._ParseIntegerValue(
    #     parser_mediator, metadata, 'i4')
    event_data.last_printed_time = self._ParseISO8601DateTimeString(
        parser_mediator, metadata, 'last_printed')
    event_data.last_saved_by = self._GetPropertyValue(
        parser_mediator, metadata, 'last_saved_by')
    event_data.links_up_to_date = self._ParseBooleanValue(
        metadata, 'links_up_to_date')
    event_data.modification_time = self._ParseISO8601DateTimeString(
        parser_mediator, metadata, 'modified')
    event_data.number_of_characters = self._ParseIntegerValue(
        metadata, 'number_of_characters')
    event_data.number_of_characters_with_spaces = self._ParseIntegerValue(
        metadata, 'number_of_characters_with_spaces')
    event_data.number_of_clips = self._ParseIntegerValue(metadata, 'mm_clips')
    event_data.number_of_hidden_slides = self._ParseIntegerValue(
        metadata, 'hidden_slides')
    event_data.number_of_lines = self._ParseIntegerValue(
        metadata, 'number_of_lines')
    event_data.number_of_pages = self._ParseIntegerValue(
        metadata, 'number_of_pages')
    event_data.number_of_paragraphs = self._ParseIntegerValue(
        metadata, 'number_of_paragraphs')
    event_data.number_of_slides = self._ParseIntegerValue(metadata, 'slides')
    event_data.number_of_words = self._ParseIntegerValue(
        metadata, 'number_of_words')
    event_data.revision_number = self._ParseIntegerValue(
        metadata, 'revision_number')
    event_data.scale = self._ParseBooleanValue(metadata, 'scale_crop')
    event_data.security_flags = self._ParseIntegerValue(
        metadata, 'doc_security')
    event_data.shared_doc = self._GetPropertyValue(
        parser_mediator, metadata, 'shared_doc')
    event_data.template = self._GetPropertyValue(
        parser_mediator, metadata, 'template')

    parser_mediator.ProduceEventData(event_data)


czip.CompoundZIPParser.RegisterPlugin(OpenXMLPlugin)
