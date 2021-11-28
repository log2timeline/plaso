#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OXML plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.czip_plugins import oxml

from tests.parsers.czip_plugins import test_lib


class OXMLTest(test_lib.CompoundZIPPluginTestCase):
  """Tests for the OXML plugin."""

  # pylint: disable=protected-access

  _PROPERTIES_XML_DATA = ''.join([
      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
      ('<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/'
       'package/2006/metadata/core-properties" xmlns:dc="http://purl.org/'
       'dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
       'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
       'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'),
      '<dc:creator>Nides</dc:creator>',
      '<cp:lastModifiedBy>Nides</cp:lastModifiedBy>',
      '<cp:revision>3</cp:revision>',
      ('<dcterms:created xsi:type="dcterms:W3CDTF">2012-11-07T23:29:00.1234567Z'
       '</dcterms:created>'),
      ('<dcterms:modified xsi:type="dcterms:W3CDTF">2013-08-25T22:18:00Z'
       '</dcterms:modified>'),
      '</cp:coreProperties>'])

  _RELATIONSHIPS_XML_DATA = ''.join([
      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
      ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
       'relationships">'),
      ('<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/'
       'package/2006/relationships/metadata/core-properties" Target="docProps/'
       'core.xml"/>'),
      ('<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/'
       'package/2006/relationships/metadata/thumbnail" Target="docProps/'
       'thumbnail.emf"/>'),
      ('<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
       'officeDocument/2006/relationships/officeDocument" Target="word/'
       'document.xml"/>'),
      ('<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/'
       'officeDocument/2006/relationships/extended-properties" '
       'Target="docProps/app.xml"/>'),
      '</Relationships>'])

  # TODO: add tests for _FormatPropertyName.

  def testParsePropertiesXMLFile(self):
    """Tests the _ParsePropertiesXMLFile function."""
    plugin = oxml.OpenXMLPlugin()

    expected_properties = {
        'author': 'Nides',
        'created': '2012-11-07T23:29:00.1234567Z',
        'last_saved_by': 'Nides',
        'modified': '2013-08-25T22:18:00Z',
        'revision_number': '3'}

    properties = plugin._ParsePropertiesXMLFile(self._PROPERTIES_XML_DATA)
    self.assertEqual(properties, expected_properties)

  def testParseRelationshipsXMLFile(self):
    """Tests the _ParseRelationshipsXMLFile function."""
    plugin = oxml.OpenXMLPlugin()

    expected_property_files = ['docProps/core.xml', 'docProps/app.xml']

    property_files = plugin._ParseRelationshipsXMLFile(
        self._RELATIONSHIPS_XML_DATA)
    self.assertEqual(property_files, expected_property_files)

  def testProduceEvent(self):
    """Tests the _ProduceEvent function."""
    plugin = oxml.OpenXMLPlugin()

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    event_data = oxml.OpenXMLEventData()

    properties = plugin._ParsePropertiesXMLFile(self._PROPERTIES_XML_DATA)

    # Test parsing a date and time string in intervals of 1 s.
    plugin._ProduceEvent(
        parser_mediator, event_data, properties, 'modified',
        definitions.TIME_DESCRIPTION_MODIFICATION, 'modification time')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test parsing a date and time string in intervals of 100 ns.
    plugin._ProduceEvent(
        parser_mediator, event_data, properties, 'created',
        definitions.TIME_DESCRIPTION_CREATION, 'creation time')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    plugin = oxml.OpenXMLPlugin()
    storage_writer = self._ParseZIPFileWithPlugin(['Document.docx'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'metadata:openxml',
        'date_time': '2012-11-07 23:29:00',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'app_version': '14.0000',
        'author': 'Nides',
        'creating_app': 'Microsoft Office Word',
        'data_type': 'metadata:openxml',
        'date_time': '2013-08-25 22:18:00',
        'doc_security': '0',
        'hyperlinks_changed': 'false',
        'i4': '1',
        'last_saved_by': 'Nides',
        'links_up_to_date': 'false',
        'number_of_characters': '13',
        'number_of_characters_with_spaces': '14',
        'number_of_lines': '1',
        'number_of_pages': '1',
        'number_of_paragraphs': '1',
        'number_of_words': '2',
        'revision_number': '3',
        'scale_crop': 'false',
        'template': 'Normal.dotm',
        'total_time': '1385'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
