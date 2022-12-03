#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OXML plugin."""

import unittest

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

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    plugin = oxml.OpenXMLPlugin()
    storage_writer = self._ParseZIPFileWithPlugin(['Document.docx'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'application': 'Microsoft Office Word',
        'application_version': '14.0000',
        'author': 'Nides',
        'creation_time': '2012-11-07T23:29:00.000000+00:00',
        'data_type': 'openxml:metadata',
        'edit_duration': 1385,
        'hyperlinks_changed': False,
        'last_printed_time': None,
        'last_saved_by': 'Nides',
        'links_up_to_date': False,
        'modification_time': '2013-08-25T22:18:00.000000+00:00',
        'number_of_characters': 13,
        'number_of_characters_with_spaces': 14,
        'number_of_clips': None,
        'number_of_hidden_slides': None,
        'number_of_lines': 1,
        'number_of_pages': 1,
        'number_of_paragraphs': 1,
        'number_of_slides': None,
        'number_of_words': 2,
        'revision_number': 3,
        'scale': False,
        'security_flags': 0,
        'template': 'Normal.dotm'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
