#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the OXML parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import oxml as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import oxml

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class OXMLTest(test_lib.ParserTestCase):
  """Tests for the OXML parser."""

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
    parser = oxml.OpenXMLParser()

    expected_properties = {
        'author': 'Nides',
        'created': '2012-11-07T23:29:00.1234567Z',
        'last_saved_by': 'Nides',
        'modified': '2013-08-25T22:18:00Z',
        'revision_number': '3'}

    properties = parser._ParsePropertiesXMLFile(self._PROPERTIES_XML_DATA)
    self.assertEqual(properties, expected_properties)

  def testParseRelationshipsXMLFile(self):
    """Tests the _ParseRelationshipsXMLFile function."""
    parser = oxml.OpenXMLParser()

    expected_property_files = ['docProps/core.xml', 'docProps/app.xml']

    property_files = parser._ParseRelationshipsXMLFile(
        self._RELATIONSHIPS_XML_DATA)
    self.assertEqual(property_files, expected_property_files)

  def testProduceEvent(self):
    """Tests the _ProduceEvent function."""
    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    event_data = oxml.OpenXMLEventData()

    parser = oxml.OpenXMLParser()

    properties = parser._ParsePropertiesXMLFile(self._PROPERTIES_XML_DATA)

    # Test parsing a date and time string in intervals of 1 s.
    parser._ProduceEvent(
        parser_mediator, event_data, properties, 'modified',
        definitions.TIME_DESCRIPTION_MODIFICATION, 'modification time')

    self.assertEqual(storage_writer.number_of_events, 1)

    # Test parsing a date and time string in intervals of 100 ns.
    parser._ProduceEvent(
        parser_mediator, event_data, properties, 'created',
        definitions.TIME_DESCRIPTION_CREATION, 'creation time')

    self.assertEqual(storage_writer.number_of_events, 2)

  @shared_test_lib.skipUnlessHasTestFile(['Document.docx'])
  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    parser = oxml.OpenXMLParser()
    storage_writer = self._ParseFile(['Document.docx'], parser)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-11-07 23:29:00.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event = events[1]

    self.assertEqual(event.number_of_characters, '13')
    self.assertEqual(event.total_time, '1385')
    self.assertEqual(event.number_of_characters_with_spaces, '14')
    self.assertEqual(event.i4, '1')
    self.assertEqual(event.app_version, '14.0000')
    self.assertEqual(event.number_of_lines, '1')
    self.assertEqual(event.scale_crop, 'false')
    self.assertEqual(event.number_of_pages, '1')
    self.assertEqual(event.number_of_words, '2')
    self.assertEqual(event.links_up_to_date, 'false')
    self.assertEqual(event.number_of_paragraphs, '1')
    self.assertEqual(event.doc_security, '0')
    self.assertEqual(event.hyperlinks_changed, 'false')
    self.assertEqual(event.revision_number, '3')
    self.assertEqual(event.last_saved_by, 'Nides')
    self.assertEqual(event.author, 'Nides')
    self.assertEqual(event.creating_app, 'Microsoft Office Word')
    self.assertEqual(event.template, 'Normal.dotm')

    expected_message = (
        'Creating App: Microsoft Office Word '
        'App version: 14.0000 '
        'Last saved by: Nides '
        'Author: Nides '
        'Revision number: 3 '
        'Template: Normal.dotm '
        'Number of pages: 1 '
        'Number of words: 2 '
        'Number of characters: 13 '
        'Number of characters with spaces: 14 '
        'Number of lines: 1 '
        'Hyperlinks changed: false '
        'Links up to date: false '
        'Scale crop: false')
    expected_short_message = (
        'Author: Nides')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
