#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound Files (OLECF) parser."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.parsers import olecf
from plaso.parsers import olecf_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class OLECFParserTest(test_lib.ParserTestCase):
  """Tests for the OLE Compound Files (OLECF) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = olecf.OLECFParser()
    storage_writer = self._ParseFile(['Document.doc'], parser)

    # OLE Compound File information:
    #     Version             : 3.62
    #     Sector size         : 512
    #     Short sector size   : 64

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    event = events[8]

    self.CheckTimestamp(event.timestamp, '2013-05-16 02:29:49.785000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'olecf:item')
    self.assertEqual(event_data.offset, 0)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser = olecf.OLECFParser()
    parser.ParseFileObject(parser_mediator, None)

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 0)

    warnings = list(storage_writer.GetWarnings())

    warning = warnings[0]
    self.assertIsNotNone(warning)

    self.assertTrue(warning.message.startswith(
        'unable to open file with error: pyolecf_file_open_file_object: '))


if __name__ == '__main__':
  unittest.main()
